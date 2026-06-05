"""
AI交互路由 V2
支持多智能体：教师(Tutor)、评分(Grader)、推荐(Recommender)
教师智能体必须关联大纲(outline_id)，严格按大纲模块教学
"""
from fastapi import APIRouter, Depends, Request, HTTPException
from starlette.responses import StreamingResponse
from typing import Optional
from datetime import datetime, timezone
import asyncio
import json
import logging

from app.core.security import get_current_user
from app.langgraph.orchestrator import orchestrator, AgentType
from app.langgraph.state import MultiAgentState
from app.sse.manager import sse_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["AI交互 - 多智能体"])

from pydantic import BaseModel, Field


# ─── 请求模型 ───

class TutorRequest(BaseModel):
    """教师教学请求"""
    message: str = Field(..., description="用户消息")
    outline_id: int = Field(..., description="关联的大纲ID（必填，教师需要知道教什么）")
    teacher_style: Optional[str] = Field("default", description="教师风格: default/humorous/rigorous")
    session_id: Optional[str] = Field("", description="教学会话ID（续接时传入）")


class GradeRequest(BaseModel):
    """评分请求"""
    message: str = Field(..., description="需要评分的回答内容")


class RecommendRequest(BaseModel):
    """推荐请求"""
    message: str = Field(..., description="学习情况描述")
    outline_id: Optional[int] = Field(None, description="关联的大纲ID（可选）")


class AgentInfoResponse(BaseModel):
    """Agent信息"""
    type: str
    description: str
    capabilities: list


# ─── 教师教学 ───

@router.post("/tutor/start")
async def start_tutor_session(
    request: TutorRequest,
    current_user=Depends(get_current_user)
):
    """
    启动教师教学会话

    教师智能体会：
    1. 从MySQL加载指定大纲
    2. 加载/创建教学进度记录
    3. 从Chroma检索历史教学对话
    4. 严格按大纲当前模块进行教学
    """
    uid = current_user["id"]

    # 验证大纲是否存在
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select
    from app.db.session import get_db
    from app.models.outline import Outline

    # 创建会话ID
    session_id = request.session_id or f"teach_{uid}_{request.outline_id}_{int(datetime.now(timezone.utc).timestamp())}"

    # 创建SSE队列
    queue = await sse_manager.connect(uid, session_id)

    # 准备初始状态 - 教师需要outline_id
    initial_state = MultiAgentState(
        user_id=uid,
        current_agent="tutor",
        user_input=request.message,
        messages=[],
        agent_messages=[],
        agent_outputs={},
        intermediate_steps=[],
        sse_queue=queue,
        session_id=session_id,
        teacher_style=request.teacher_style,
        context={
            "outline_id": request.outline_id
        }
    )

    async def run_teaching():
        try:
            await sse_manager.send_event(uid, session_id, {
                "event": "started",
                "data": {
                    "agent_type": "tutor",
                    "outline_id": request.outline_id,
                    "message": "正在准备教学内容..."
                }
            })

            state_dict = initial_state.model_dump(exclude={'sse_queue'})
            state_dict["sse_queue"] = queue
            result = await orchestrator.run_agent(AgentType.TUTOR, state_dict)

            await sse_manager.send_event(uid, session_id, {
                "event": "completed",
                "data": {
                    "agent_type": "tutor",
                    "output": result.get("ai_output", ""),
                    "context": result.get("context", {})
                }
            })

        except Exception as e:
            logger.error(f"教学失败: {e}", exc_info=True)
            await sse_manager.send_event(uid, session_id, {
                "event": "error",
                "data": {"message": str(e)}
            })

    asyncio.create_task(run_teaching())

    return {
        "session_id": session_id,
        "status": "started",
        "outline_id": request.outline_id,
        "stream_url": f"/api/v1/ai/stream/{session_id}"
    }


# ─── 模块内容生成 + 课程教学 ───

class GenerateModuleRequest(BaseModel):
    """生成模块教学内容请求"""
    outline_id: int = Field(..., description="大纲ID")
    module_index: int = Field(..., ge=1, description="模块序号(1-based)")
    teacher_style: str = Field("default", description="教师风格")


class TeachModuleRequest(BaseModel):
    """模块教学请求"""
    outline_id: int = Field(..., description="大纲ID")
    module_index: int = Field(..., ge=1, description="模块序号")
    message: str = Field("开始上课", description="用户消息")
    teacher_style: str = Field("default", description="教师风格")


@router.get("/tutor/modules/{outline_id}")
async def list_module_status(
    outline_id: int,
    current_user=Depends(get_current_user),
):
    """获取大纲各模块的生成状态 + 教学进度"""
    uid = current_user["id"]
    from app.db.session import async_session_factory
    from app.models.conversation import ModuleContent, TeachingSession
    from app.models.outline import Outline
    from sqlalchemy import select

    async with async_session_factory() as db:
        # 加载大纲
        r = await db.execute(select(Outline).where(Outline.id == outline_id, Outline.user_id == uid))
        outline = r.scalar_one_or_none()
        if not outline:
            raise HTTPException(404, "大纲不存在")

        modules = outline.modules_data or []

        # 加载模块内容
        r2 = await db.execute(
            select(ModuleContent).where(
                ModuleContent.outline_id == outline_id,
                ModuleContent.user_id == uid
            )
        )
        contents = {c.module_index: c for c in r2.scalars().all()}

        # 加载教学进度
        r3 = await db.execute(
            select(TeachingSession).where(
                TeachingSession.outline_id == outline_id,
                TeachingSession.user_id == uid,
                TeachingSession.status == "active"
            ).order_by(TeachingSession.updated_at.desc())
        )
        ts = r3.scalars().first()

        result = []
        for i, mod in enumerate(modules):
            idx = i + 1
            mc = contents.get(idx)
            result.append({
                "module_index": idx,
                "name": mod.get("name", f"模块{idx}"),
                "duration": mod.get("duration", 20),
                "keyPoints": mod.get("keyPoints", []),
                "deliverable": mod.get("deliverable", ""),
                "content_status": mc.status if mc else "pending",
                "has_content": bool(mc and mc.status == "completed"),
            })

        return {
            "outline_id": outline_id,
            "title": outline.title,
            "modules": result,
            "teaching_progress": {
                "current_module": ts.current_module if ts else 1,
                "module_progress": ts.module_progress if ts else 0,
                "completed_modules": ts.completed_modules if ts and ts.completed_modules else [],
                "status": ts.status if ts else "active"
            } if ts else None
        }


@router.post("/tutor/generate-module")
async def generate_module_content(
    request: GenerateModuleRequest,
    current_user=Depends(get_current_user),
):
    """预生成单个模块的AI教学内容（SSE流式返回进度）"""
    uid = current_user["id"]
    session_id = f"genmod_{uid}_{request.outline_id}_{request.module_index}_{int(datetime.now(timezone.utc).timestamp())}"
    queue = await sse_manager.connect(uid, session_id)

    async def run_generate():
        try:
            from app.db.session import async_session_factory
            from app.models.conversation import ModuleContent
            from app.models.outline import Outline
            from sqlalchemy import select
            from app.langgraph.outline_agent import _get_llm as get_outline_llm

            await sse_manager.send_event(uid, session_id, {
                "event": "status", "data": {"phase": "loading", "message": "正在加载模块信息..."}
            })

            async with async_session_factory() as db:
                r = await db.execute(select(Outline).where(Outline.id == request.outline_id, Outline.user_id == uid))
                outline = r.scalar_one_or_none()
                if not outline:
                    await sse_manager.send_event(uid, session_id, {"event": "error", "data": {"message": "大纲不存在"}})
                    return

                modules = outline.modules_data or []
                if request.module_index < 1 or request.module_index > len(modules):
                    await sse_manager.send_event(uid, session_id, {"event": "error", "data": {"message": "模块序号无效"}})
                    return

                mod = modules[request.module_index - 1]
                module_name = mod.get("name", "")
                key_points = mod.get("keyPoints", [])
                deliverable = mod.get("deliverable", "")
                duration = mod.get("duration", 20)

            # 检查是否已生成
            async with async_session_factory() as db:
                r2 = await db.execute(
                    select(ModuleContent).where(
                        ModuleContent.outline_id == request.outline_id,
                        ModuleContent.module_index == request.module_index,
                        ModuleContent.user_id == uid
                    )
                )
                existing = r2.scalar_one_or_none()
                if existing and existing.status == "completed":
                    await sse_manager.send_event(uid, session_id, {
                        "event": "completed", "data": {"content": existing.content, "reused": True}
                    })
                    return
                elif existing:
                    mc = existing
                    mc.status = "generating"
                    await db.commit()
                else:
                    mc = ModuleContent(
                        user_id=uid, outline_id=request.outline_id,
                        module_index=request.module_index, module_name=module_name,
                        teacher_style=request.teacher_style, status="generating"
                    )
                    db.add(mc)
                    await db.commit()
                    await db.refresh(mc)

            # 构建生成 Prompt
            style_map = {
                "humorous": "幽默风趣的脱口秀风格，多用生动的比喻和玩笑",
                "rigorous": "严谨认真的教授风格，注重逻辑推导和理论深度",
                "default": "亲切易懂的风格，注重互动和启发式教学"
            }
            style_desc = style_map.get(request.teacher_style, style_map["default"])

            system = f"""你是一位经验丰富的AI教师。请为以下课程模块生成详细的教学内容。

模块信息：
  模块名称：{module_name}
  建议时长：{duration}分钟
  核心知识点：{'; '.join(key_points)}
  学完后能：{deliverable}

教学要求：
  教学风格：{style_desc}
  内容要有深度，逐步递进
  包含具体代码示例和练习
  使用生活例子辅助理解

重要规则：
  这是语音课堂！输出会被朗读。禁止使用任何Markdown格式标记
  禁止 `#` `**` `*` `-` `>` `|` `~~~` ` ``` ` 等符号
  代码示例用缩进呈现，不要用反引号包裹
  用自然的口语讲授，像真实教师上课一样"""

            user_msg = f"请为「{module_name}」模块生成完整的教学内容。"

            from langchain_core.messages import HumanMessage, SystemMessage
            # 使用DeepSeek LLM
            llm = None
            try:
                from app.langgraph.tutor_agent import _get_llm as get_tutor_llm
                llm = get_tutor_llm()
            except:
                llm = get_outline_llm()

            full_text = ""
            async for chunk in llm.astream([SystemMessage(content=system), HumanMessage(content=user_msg)]):
                token = chunk.content if hasattr(chunk, 'content') else str(chunk)
                if token:
                    full_text += token
                    await sse_manager.send_event(uid, session_id, {
                        "event": "token", "data": {"token": token}
                    })

            # 保存结果
            async with async_session_factory() as db:
                r3 = await db.execute(
                    select(ModuleContent).where(ModuleContent.id == mc.id)
                )
                mc_saved = r3.scalar_one_or_none()
                if mc_saved:
                    mc_saved.content = full_text
                    mc_saved.status = "completed"
                    await db.commit()

            await sse_manager.send_event(uid, session_id, {
                "event": "completed", "data": {"content": full_text, "module_index": request.module_index}
            })

        except Exception as e:
            logger.error(f"模块内容生成失败: {e}", exc_info=True)
            await sse_manager.send_event(uid, session_id, {"event": "error", "data": {"message": str(e)}})

    asyncio.create_task(run_generate())
    return {
        "session_id": session_id,
        "status": "generating",
        "stream_url": f"/api/v1/ai/stream/{session_id}"
    }


@router.post("/tutor/teach")
async def teach_module(
    request: TeachModuleRequest,
    current_user=Depends(get_current_user),
):
    """开始教授指定模块（使用预生成内容 + AI互动）"""
    uid = current_user["id"]
    session_id = f"teach_{uid}_{request.outline_id}_{request.module_index}_{int(datetime.now(timezone.utc).timestamp())}"
    queue = await sse_manager.connect(uid, session_id)

    async def run_teach():
        try:
            from app.db.session import async_session_factory
            from app.models.conversation import ModuleContent, TeachingSession
            from app.models.outline import Outline
            from sqlalchemy import select

            await sse_manager.send_event(uid, session_id, {
                "event": "status", "data": {"phase": "loading", "message": "准备教学内容..."}
            })

            async with async_session_factory() as db:
                # 加载大纲
                r = await db.execute(select(Outline).where(Outline.id == request.outline_id, Outline.user_id == uid))
                outline = r.scalar_one_or_none()
                if not outline:
                    await sse_manager.send_event(uid, session_id, {"event": "error", "data": {"message": "大纲不存在"}})
                    return

                modules = outline.modules_data or []
                if request.module_index < 1 or request.module_index > len(modules):
                    await sse_manager.send_event(uid, session_id, {"event": "error", "data": {"message": "模块序号无效"}})
                    return

                mod = modules[request.module_index - 1]

                # 加载预生成的内容
                r2 = await db.execute(
                    select(ModuleContent).where(
                        ModuleContent.outline_id == request.outline_id,
                        ModuleContent.module_index == request.module_index,
                        ModuleContent.user_id == uid,
                        ModuleContent.status == "completed"
                    )
                )
                mc = r2.scalar_one_or_none()

                # 更新教学会话
                r3 = await db.execute(
                    select(TeachingSession).where(
                        TeachingSession.outline_id == request.outline_id,
                        TeachingSession.user_id == uid,
                        TeachingSession.status == "active"
                    ).order_by(TeachingSession.updated_at.desc())
                )
                ts = r3.scalars().first()
                if ts:
                    ts.current_module = request.module_index
                    ts.module_progress = 0
                    ts.session_id = session_id
                    await db.commit()
                else:
                    ts = TeachingSession(
                        user_id=uid, outline_id=request.outline_id,
                        session_id=session_id, current_module=request.module_index,
                        total_modules=len(modules), status="active"
                    )
                    db.add(ts)
                    await db.commit()

            if mc and mc.content:
                # 有预生成内容：用预设内容 + AI按需互动
                pre_content = mc.content
                style_map = {"humorous": "幽默风趣", "rigorous": "严谨认真", "default": "亲切耐心"}
                style = style_map.get(request.teacher_style, "亲切耐心")

                system = f"""你是AI虚拟课堂的讲师，正在教授模块"{mod.get('name','')}"。
以下是你备课的内容原文（请严格按此内容进行讲授，不要偏离主题）：

---
{pre_content}
---

## 教学规则
1. 严格围绕上述备课内容进行讲授
2. 用{style}的风格教学
3. 每讲完一个知识点后主动提问
4. 适当引用代码示例
5. 学生提问时，基于备课内容解答"""

                from langchain_core.messages import HumanMessage, SystemMessage
                llm = None
                try:
                    from app.langgraph.tutor_agent import _get_llm as get_tutor_llm
                    llm = get_tutor_llm()
                except:
                    from app.langgraph.outline_agent import _get_llm as get_outline_llm
                    llm = get_outline_llm()

                async for chunk in llm.astream([
                    SystemMessage(content=system),
                    HumanMessage(content=request.message)
                ]):
                    token = chunk.content if hasattr(chunk, 'content') else str(chunk)
                    if token:
                        await sse_manager.send_event(uid, session_id, {
                            "event": "token", "data": {"token": token}
                        })
            else:
                # 没有预生成内容：直接在这里生成并教学
                style_map2 = {"humorous": "幽默风趣", "rigorous": "严谨认真", "default": "亲切耐心"}
                style2 = style_map2.get(request.teacher_style, "亲切耐心")
                system = f"""你是AI虚拟课堂的讲师，正在教授课程"{outline.title}"的模块"{mod.get('name','')}"。
模块信息：时长{mod.get('duration',20)}分钟，知识点：{'; '.join(mod.get('keyPoints',[]))}
请用{style2}的风格进行详细教学，包含代码示例和实际练习。
重要：这是语音课堂，输出会被朗读。严禁使用任何Markdown格式标记（# ** * - `等），用纯文本口语讲授。"""

                from langchain_core.messages import HumanMessage, SystemMessage
                llm = None
                try:
                    from app.langgraph.tutor_agent import _get_llm as get_tutor_llm
                    llm = get_tutor_llm()
                except:
                    from app.langgraph.outline_agent import _get_llm as get_outline_llm
                    llm = get_outline_llm()

                async for chunk in llm.astream([
                    SystemMessage(content=system),
                    HumanMessage(content=request.message)
                ]):
                    token = chunk.content if hasattr(chunk, 'content') else str(chunk)
                    if token:
                        await sse_manager.send_event(uid, session_id, {
                            "event": "token", "data": {"token": token}
                        })

            await sse_manager.send_event(uid, session_id, {
                "event": "done", "data": {"module_index": request.module_index}
            })

        except Exception as e:
            logger.error(f"模块教学失败: {e}", exc_info=True)
            await sse_manager.send_event(uid, session_id, {"event": "error", "data": {"message": str(e)}})

    asyncio.create_task(run_teach())
    return {
        "session_id": session_id,
        "status": "teaching",
        "stream_url": f"/api/v1/ai/stream/{session_id}"
    }


class ModuleProgressRequest(BaseModel):
    """模块进度更新请求"""
    outline_id: int = Field(...)
    module_index: int = Field(..., ge=1)
    progress: int = Field(0, ge=0, le=100, description="进度 0-100")
    completed: bool = Field(False, description="是否标记为完成")


@router.put("/tutor/progress")
async def update_module_progress(
    request: ModuleProgressRequest,
    current_user=Depends(get_current_user),
):
    """更新当前模块学习进度"""
    uid = current_user["id"]
    from app.db.session import async_session_factory
    from app.models.conversation import TeachingSession
    from sqlalchemy import select

    async with async_session_factory() as db:
        r = await db.execute(
            select(TeachingSession).where(
                TeachingSession.outline_id == request.outline_id,
                TeachingSession.user_id == uid,
                TeachingSession.status == "active"
            ).order_by(TeachingSession.updated_at.desc())
        )
        ts = r.scalars().first()
        if ts:
            ts.current_module = request.module_index
            ts.module_progress = request.progress
            if request.completed:
                completed = list(ts.completed_modules or [])
                if request.module_index not in completed:
                    completed.append(request.module_index)
                ts.completed_modules = completed
                ts.module_progress = 100
            await db.commit()
            return {"status": "ok", "current_module": ts.current_module, "progress": ts.module_progress}
        return {"status": "ok", "current_module": request.module_index, "progress": request.progress}


# ─── 评分 ───

@router.post("/grade")
async def grade_answer(
    request: GradeRequest,
    current_user=Depends(get_current_user)
):
    """评分 - 独立评分Agent，不涉及教学"""
    uid = current_user["id"]
    session_id = f"grade_{uid}_{int(datetime.now(timezone.utc).timestamp())}"
    queue = await sse_manager.connect(uid, session_id)

    initial_state = MultiAgentState(
        user_id=uid,
        current_agent="grader",
        user_input=request.message,
        messages=[],
        agent_messages=[],
        agent_outputs={},
        intermediate_steps=[],
        sse_queue=queue,
        session_id=session_id
    )

    async def run_grade():
        try:
            state_dict = initial_state.model_dump(exclude={'sse_queue'})
            state_dict["sse_queue"] = queue
            await orchestrator.run_agent(AgentType.GRADER, state_dict)
        except Exception as e:
            logger.error(f"评分失败: {e}", exc_info=True)
            await sse_manager.send_event(uid, session_id, {
                "event": "error", "data": {"message": str(e)}
            })

    asyncio.create_task(run_grade())
    return {
        "session_id": session_id,
        "status": "grading",
        "stream_url": f"/api/v1/ai/stream/{session_id}"
    }


# ─── 推荐 ───

@router.post("/recommend")
async def recommend_resources(
    request: RecommendRequest,
    current_user=Depends(get_current_user)
):
    """推荐 - 独立推荐Agent，不涉及教学"""
    uid = current_user["id"]
    session_id = f"rec_{uid}_{int(datetime.now(timezone.utc).timestamp())}"
    queue = await sse_manager.connect(uid, session_id)

    initial_state = MultiAgentState(
        user_id=uid,
        current_agent="recommender",
        user_input=request.message,
        messages=[],
        agent_messages=[],
        agent_outputs={},
        intermediate_steps=[],
        sse_queue=queue,
        session_id=session_id,
        context={"outline_id": request.outline_id} if request.outline_id else None
    )

    async def run_recommend():
        try:
            state_dict = initial_state.model_dump(exclude={'sse_queue'})
            state_dict["sse_queue"] = queue
            await orchestrator.run_agent(AgentType.RECOMMENDER, state_dict)
        except Exception as e:
            logger.error(f"推荐失败: {e}", exc_info=True)
            await sse_manager.send_event(uid, session_id, {
                "event": "error", "data": {"message": str(e)}
            })

    asyncio.create_task(run_recommend())
    return {
        "session_id": session_id,
        "status": "recommending",
        "stream_url": f"/api/v1/ai/stream/{session_id}"
    }


# ─── 通用SSE流 ───

@router.get("/stream/{session_id}")
async def ai_sse_stream(
    session_id: str,
    request: Request,
    current_user=Depends(get_current_user)
):
    """通用SSE流式输出端点（使用原生 StreamingResponse，兼容性更好）"""
    uid = current_user["id"]

    if uid not in sse_manager.connections or \
       session_id not in sse_manager.connections[uid]:
        raise HTTPException(status_code=404, detail="会话不存在，请先启动教学/评分/推荐")

    queue = sse_manager.connections[uid][session_id]

    async def event_generator():
        yield f"event: connected\ndata: {json.dumps({'session_id': session_id, 'timestamp': datetime.now(timezone.utc).isoformat()})}\n\n"

        while True:
            if await request.is_disconnected():
                break

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
                yield f"event: heartbeat\ndata: {json.dumps({'timestamp': datetime.now(timezone.utc).isoformat()})}\n\n"

        sse_manager.disconnect(uid, session_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# ─── Agent列表 ───

@router.get("/agents")
async def list_agents(current_user=Depends(get_current_user)):
    """列出所有可用Agent"""
    agents = orchestrator.list_agents()
    return {
        "agents": [
            {
                "type": agent.agent_type,
                "description": agent.description,
                "capabilities": agent.capabilities,
                "is_active": agent.is_active
            }
            for agent in agents
        ]
    }
