"""
大纲规划 API V3
简洁三步流程：问知识 → 选程度 → 问时间 → 生成大纲
"""
import re
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import logging
import json
import asyncio

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.outline import Outline
from app.langgraph.outline_agent import run_outline_workflow, parse_outline_to_modules, generate_outline_from_pdf_text, extract_pdf_text
from app.sse.manager import sse_manager
from pydantic import BaseModel, Field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/outline", tags=["大纲规划"])


def _clean_topic_name(raw: str) -> str:
    """去除 topic 中的前缀词，返回纯净的学科名称用于拼接「XX学习大纲」"""
    topic = raw.strip()
    # 去掉常见的前缀词
    topic = re.sub(r'^(教我|帮我|帮我规划|帮我整理|我想学|我想学习|我要学|我要学习|学习|复习|准备|整理)\s*', '', topic)
    # 去掉末尾多余的「的」「内容」等
    topic = re.sub(r'\s*(的学习?|的内容|的相关知识)\s*$', '', topic)
    # 太长则截断
    if len(topic) > 20:
        topic = topic[:20]
    return topic.strip() or raw.strip()[:20]


class OutlineGenerateRequest(BaseModel):
    """大纲生成请求"""
    message: str = Field(..., description="用户的学习需求描述")
    topic: str = Field("", description="学习主题（可选，AI会自动识别）")
    level: str = Field("beginner", description="难度等级: beginner/intermediate/advanced")
    session_id: str = Field("", description="会话ID（续接之前对话时传入）")


class OutlineStartTeachingRequest(BaseModel):
    """开始教学请求"""
    outline_id: int = Field(..., description="大纲ID")
    teacher_style: str = Field("default", description="教师风格: default/humorous/rigorous")


# ─── 大纲生成（V3 简洁三步流程） ───

@router.post("/generate")
async def generate_outline_v3(
    request: OutlineGenerateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    大纲生成 V3 - 简洁三步流程

    流程：
    1. 用户说想学什么 → AI确认并询问程度
    2. 用户选择程度（初级/中级/高级）→ AI确认并询问时间
    3. 用户说时间 → AI直接生成大纲

    前端需要：
    - 首次调用时不传 session_id，后端返回新的
    - 后续对话传入 session_id 续接
    - 连接 SSE 流获取实时输出
    - 监听 event=options 事件渲染程度选择按钮
    - 监听 event=outline_completed 获取大纲结果
    """
    uid = current_user["id"]

    # 使用已有session_id或创建新的
    session_id = request.session_id or f"outline_{uid}_{int(datetime.now(timezone.utc).timestamp())}"

    # 创建SSE队列
    queue = await sse_manager.connect(uid, session_id)

    # 后台运行
    async def run_workflow():
        try:
            await sse_manager.send_event(uid, session_id, {
                "event": "started",
                "data": {"message": "正在分析...", "session_id": session_id}
            })

            result = await run_outline_workflow(
                user_id=uid,
                session_id=session_id,
                user_message=request.message,
                sse_queue=queue,
                topic=request.topic,
                level=request.level
            )

            ai_output = result.get("ai_output", "")
            ctx = result.get("context", {})
            should_generate = ctx.get("should_generate", False)
            collected_info = ctx.get("collected_info", {})
            current_step = ctx.get("current_step", 0)

            if should_generate and ai_output:
                # 解析并保存大纲
                parsed = parse_outline_to_modules(
                    ai_output,
                    topic=collected_info.get("topic", request.topic),
                    level=collected_info.get("level", request.level)
                )

                # 默认标题：{干净的主题}学习大纲
                raw_topic = collected_info.get('topic', request.topic or '')
                clean_topic = _clean_topic_name(raw_topic)
                default_title = f"{clean_topic}学习大纲" if clean_topic else "自定义学习大纲"
                outline = Outline(
                    user_id=uid,
                    title=default_title or parsed["title"] or "自定义学习大纲",
                    topic=collected_info.get("topic", request.topic or "自定义"),
                    level=collected_info.get("level", request.level),
                    total_duration=parsed["total_duration"],
                    module_count=len(parsed["modules"]),
                    modules_data=parsed["modules"],
                    ai_generated=True
                )
                db.add(outline)
                await db.commit()
                await db.refresh(outline)

                # 发送大纲完成事件
                await sse_manager.send_event(uid, session_id, {
                    "event": "outline_completed",
                    "data": {
                        "outline_id": outline.id,
                        "title": outline.title,
                        "topic": outline.topic,
                        "level": outline.level,
                        "total_duration": outline.total_duration,
                        "module_count": outline.module_count,
                        "modules": outline.modules_data,
                        "collected_info": collected_info
                    }
                })
            else:
                # 还在对话阶段，发送 step 事件
                await sse_manager.send_event(uid, session_id, {
                    "event": "step_update",
                    "data": {
                        "step": current_step,
                        "has_options": ctx.get("has_options", False),
                        "options": ctx.get("options", []),
                        "session_id": session_id
                    }
                })

            # 发送结束信号
            await sse_manager.send_event(uid, session_id, {
                "event": "done",
                "data": {"session_id": session_id, "is_outline": should_generate}
            })

            # 生成完成后清理 SSE 连接
            if should_generate:
                sse_manager.disconnect(uid, session_id)

        except Exception as e:
            logger.error(f"大纲生成失败: {e}", exc_info=True)
            await sse_manager.send_event(uid, session_id, {
                "event": "error",
                "data": {"message": str(e)}
            })
            sse_manager.disconnect(uid, session_id)

    asyncio.create_task(run_workflow())

    return {
        "session_id": session_id,
        "status": "generating",
        "stream_url": f"/api/v1/outline/stream/{session_id}"
    }


# ─── SSE流式输出 ───

@router.get("/stream/{session_id}")
async def outline_stream(session_id: str, current_user=Depends(get_current_user)):
    """SSE流式输出端点（使用原生 StreamingResponse，兼容性更好）"""
    from starlette.responses import StreamingResponse

    uid = current_user["id"]

    if uid not in sse_manager.connections or session_id not in sse_manager.connections.get(uid, {}):
        raise HTTPException(404, "会话不存在或已过期")

    queue = sse_manager.connections[uid][session_id]

    async def event_gen():
        # 发送连接成功事件
        yield f"event: connected\ndata: {json.dumps({'session_id': session_id})}\n\n"
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

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# ─── 大纲管理 ───

@router.get("/my")
async def get_my_outlines(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户的所有大纲"""
    uid = current_user["id"]
    result = await db.execute(
        select(Outline)
        .where(Outline.user_id == uid)
        .order_by(Outline.created_at.desc())
    )
    outlines = result.scalars().all()

    return [
        {
            "id": o.id,
            "title": o.title,
            "topic": o.topic,
            "level": o.level,
            "total_duration": o.total_duration,
            "module_count": o.module_count,
            "modules_data": o.modules_data or [],
            "ai_generated": o.ai_generated,
            "status": o.status,
            "created_at": o.created_at.isoformat() if o.created_at else "",
            "updated_at": o.updated_at.isoformat() if o.updated_at else "",
        }
        for o in outlines
    ]


@router.get("/{outline_id}")
async def get_outline_detail(
    outline_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取大纲详情"""
    uid = current_user["id"]
    result = await db.execute(
        select(Outline).where(Outline.id == outline_id, Outline.user_id == uid)
    )
    outline = result.scalar_one_or_none()
    if not outline:
        raise HTTPException(404, "大纲不存在")

    return {
        "id": outline.id,
        "title": outline.title,
        "topic": outline.topic,
        "level": outline.level,
        "total_duration": outline.total_duration,
        "module_count": outline.module_count,
        "modules_data": outline.modules_data or [],
        "ai_generated": outline.ai_generated,
        "status": outline.status,
        "created_at": outline.created_at.isoformat() if outline.created_at else "",
        "updated_at": outline.updated_at.isoformat() if outline.updated_at else "",
    }


class RenameOutlineRequest(BaseModel):
    """重命名大纲请求"""
    title: str = Field(..., min_length=1, max_length=100, description="新的标题")


@router.put("/{outline_id}/rename")
async def rename_outline(
    outline_id: int,
    request: RenameOutlineRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """重命名大纲"""
    uid = current_user["id"]
    result = await db.execute(
        select(Outline).where(Outline.id == outline_id, Outline.user_id == uid)
    )
    outline = result.scalar_one_or_none()
    if not outline:
        raise HTTPException(404, "大纲不存在")

    outline.title = request.title.strip()
    await db.commit()
    return {"status": "ok", "title": outline.title}


@router.delete("/{outline_id}")
async def delete_outline(
    outline_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除大纲"""
    uid = current_user["id"]
    result = await db.execute(
        select(Outline).where(Outline.id == outline_id, Outline.user_id == uid)
    )
    outline = result.scalar_one_or_none()
    if not outline:
        raise HTTPException(404, "大纲不存在")
    await db.delete(outline)
    await db.commit()
    return {"status": "deleted"}


# ─── PDF 资料生成大纲 ───

@router.post("/pdf-generate")
async def generate_outline_from_pdf(
    file: UploadFile = File(...),
    topic: str = Form(""),
    level: str = Form("beginner"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """上传 PDF 文件，根据内容生成学习大纲（SSE 流式返回）"""
    uid = current_user["id"]

    # 验证文件类型
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(400, "仅支持 PDF 文件")

    # 读取并提取文本
    try:
        contents = await file.read()
        pdf_text = extract_pdf_text(contents)
    except Exception as e:
        raise HTTPException(400, f"PDF 解析失败: {str(e)}")

    if not pdf_text or len(pdf_text.strip()) < 50:
        raise HTTPException(400, "PDF 内容过少，无法生成大纲")

    # 自动识别主题
    detected_topic = topic.strip() if topic.strip() else file.filename.replace('.pdf', '').strip()
    detected_topic = _clean_topic_name(detected_topic)

    session_id = f"pdf_{uid}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # 生成大纲
    raw_text = await generate_outline_from_pdf_text(
        pdf_text, detected_topic, level, file.filename
    )

    # 解析为结构化模块
    outline_data = parse_outline_to_modules(raw_text, detected_topic, level)

    # 保存到数据库
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
        ai_generated=True,
        status="completed",
        created_at=now,
        updated_at=now
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
