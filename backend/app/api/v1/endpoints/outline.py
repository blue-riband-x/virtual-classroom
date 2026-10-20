"""
大纲规划 API - 仅 AI 生成相关
CRUD 操作已迁移至 Java Spring Boot
"""
import re
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
import json
import asyncio

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.outline import Outline
from app.langgraph.outline_agent import (
    run_outline_workflow, parse_outline_to_modules,
    generate_outline_from_pdf_text, extract_pdf_text
)
from app.sse.manager import sse_manager
from pydantic import BaseModel, Field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/outline", tags=["大纲规划"])


def _clean_topic_name(raw: str) -> str:
    topic = raw.strip()
    topic = re.sub(r'^(教我|帮我|帮我规划|帮我整理|我想学|我想学习|我要学|我要学习|学习|复习|准备|整理)\s*', '', topic)
    topic = re.sub(r'\s*(的学习?|的内容|的相关知识)\s*$', '', topic)
    if len(topic) > 20:
        topic = topic[:20]
    return topic.strip() or raw.strip()[:20]


class OutlineGenerateRequest(BaseModel):
    message: str = Field(..., description="用户的学习需求描述")
    topic: str = Field("", description="学习主题")
    level: str = Field("beginner", description="难度等级: beginner/intermediate/advanced")
    session_id: str = Field("", description="会话ID")


# ─── AI 对话式大纲生成 ───

@router.post("/generate")
async def generate_outline_v3(
    request: OutlineGenerateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    uid = current_user["id"]
    session_id = request.session_id or f"outline_{uid}_{int(datetime.now().timestamp())}"
    queue = await sse_manager.connect(uid, session_id)

    asyncio.create_task(
        _do_generate(uid, session_id, request.message, request.topic, request.level, request.session_id, queue)
    )

    return {
        "status": "generating",
        "session_id": session_id,
        "stream_url": f"/api/v1/outline/stream/{session_id}"
    }


async def _do_generate(uid: int, session_id: str, message: str, topic: str, level: str, existing_session: str, sse_queue):
    from app.db.session import async_session_factory
    try:
        result = await run_outline_workflow(
            user_id=uid, session_id=existing_session or session_id,
            user_message=message, sse_queue=sse_queue,
            topic=topic, level=level
        )

        context = result.get("context", {})
        should_generate = context.get("should_generate", False)

        if should_generate:
            # Step 4: 大纲已生成 → 解析并保存
            raw_text = result.get("ai_output", "")
            outline_data = parse_outline_to_modules(raw_text, topic, level)

            async with async_session_factory() as db:
                now = datetime.now(timezone.utc)
                outline = Outline(
                    user_id=uid,
                    title=outline_data.get("title", topic),
                    topic=_clean_topic_name(topic) or topic,
                    subject=_clean_topic_name(topic) or topic,
                    level=level,
                    total_duration=outline_data.get("total_duration", 0),
                    module_count=len(outline_data.get("modules", [])),
                    modules_data=outline_data.get("modules", []),
                    ai_generated=True,
                    status="completed",
                    created_at=now, updated_at=now
                )
                db.add(outline)
                await db.commit()
                await db.refresh(outline)

                # 发送 outline_completed 事件（前端监听此事件来展示大纲）
                await sse_manager.send_event(uid, session_id, {
                    "event": "outline_completed",
                    "data": {
                        "outline_id": outline.id,
                        "title": outline.title,
                        "topic": outline.topic,
                        "level": outline.level,
                        "total_duration": outline.total_duration,
                        "module_count": outline.module_count,
                        "modules": outline_data.get("modules", []),
                        "full_text": raw_text
                    }
                })
        else:
            # Step 1-3: 对话阶段，不需要保存大纲
            # token/options 事件已由 outline_agent 直接通过 sse_queue 发送
            pass

        # 无论如何发送 done 事件关闭 SSE 流
        await sse_manager.send_event(uid, session_id, {
            "event": "done",
            "data": {"status": "ok"}
        })
    except Exception as e:
        logger.error(f"Outline generation failed: {e}")
        await sse_manager.send_event(uid, session_id, {
            "event": "error", "data": {"message": str(e)}
        })


# ─── SSE 流 ───

@router.get("/stream/{session_id}")
async def outline_stream(session_id: str):
    # 查找该 session_id 对应的队列
    queue = None
    for uid_sessions in sse_manager.connections.values():
        if session_id in uid_sessions:
            queue = uid_sessions[session_id]
            break

    if queue is None:
        from fastapi.responses import StreamingResponse
        return StreamingResponse(
            iter(["event: error\ndata: {\"message\": \"会话不存在\"}\n\n"]),
            media_type="text/event-stream"
        )

    async def event_gen():
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=5.0)
                if event is None:
                    break
                evt_type = event.get("event", "message")
                evt_data = event.get("data", "")
                if isinstance(evt_data, dict):
                    evt_data = json.dumps(evt_data, ensure_ascii=False)
                yield f"event: {evt_type}\ndata: {evt_data}\n\n"
            except asyncio.TimeoutError:
                yield f"event: heartbeat\ndata: {json.dumps({'ts': datetime.now().isoformat()})}\n\n"

    from fastapi.responses import StreamingResponse
    return StreamingResponse(event_gen(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"})


# ─── PDF 资料生成大纲 ───

@router.post("/pdf-generate")
async def generate_outline_from_pdf(
    file: UploadFile = File(...),
    topic: str = Form(""),
    level: str = Form("beginner"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    uid = current_user["id"]
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(400, "仅支持 PDF 文件")

    try:
        contents = await file.read()
        pdf_text = extract_pdf_text(contents)
    except Exception as e:
        raise HTTPException(400, f"PDF 解析失败: {str(e)}")

    if not pdf_text or len(pdf_text.strip()) < 50:
        raise HTTPException(400, "PDF 内容过少，无法生成大纲")

    detected_topic = topic.strip() if topic.strip() else file.filename.replace('.pdf', '').strip()
    detected_topic = _clean_topic_name(detected_topic)

    raw_text = await generate_outline_from_pdf_text(pdf_text, detected_topic, level, file.filename)
    outline_data = parse_outline_to_modules(raw_text, detected_topic, level)

    now = datetime.now(timezone.utc)
    outline = Outline(
        user_id=uid,
        title=outline_data.get("title", detected_topic),
        topic=detected_topic,
        subject=detected_topic,
        level=level,
        total_duration=outline_data.get("total_duration", 0),
        module_count=len(outline_data.get("modules", [])),
        modules_data=outline_data.get("modules", []),
        ai_generated=True, status="completed",
        created_at=now, updated_at=now
    )
    db.add(outline)
    await db.commit()
    await db.refresh(outline)

    return {
        "status": "ok",
        "outline_id": outline.id,
        "title": outline.title,
        "topic": detected_topic,
        "level": level,
        "total_duration": outline.total_duration,
        "module_count": outline.module_count,
        "modules": outline.modules_data or []
    }
