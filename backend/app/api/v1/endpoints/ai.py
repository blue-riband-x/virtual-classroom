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
            # 发送终止信号
            await sse_manager.send_event(uid, session_id, None)

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
                "has_boards": bool(mc and mc.board_data and mc.board_data.get("boards")),
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

            # 生成板书（同步等待，图片全部生成完毕才算"生成课程"完成）
            await sse_manager.send_event(uid, session_id, {
                "event": "status", "data": {"phase": "generating_boards", "message": "正在分析课程内容，生成知识板书..."}
            })
            try:
                from app.langgraph.board_agent import generate_boards_for_module
                board_data = await generate_boards_for_module(
                    module_name=module_name,
                    module_content=full_text,
                    key_points=key_points,
                    duration=duration
                )
                if board_data:
                    boards = board_data.get('boards', [])
                    total_boards = len(boards)
                    # 逐张生成板书图片，同步等待完成
                    from app.services.image_gen import generate_board_image
                    for i, board in enumerate(boards):
                        prompt = board.get('image_prompt', '')
                        if prompt:
                            await sse_manager.send_event(uid, session_id, {
                                "event": "status", "data": {
                                    "phase": "generating_board_image",
                                    "message": f"正在生成板书图片 ({i+1}/{total_boards})...",
                                    "current": i + 1,
                                    "total": total_boards,
                                }
                            })
                            image_url = await generate_board_image(
                                prompt=prompt,
                                outline_id=request.outline_id,
                                module_index=request.module_index,
                                board_index=i,
                            )
                            if image_url:
                                board['image_url'] = image_url

                    # 图片全部生成完毕，保存含image_url的完整board_data到数据库
                    async with async_session_factory() as db:
                        r4 = await db.execute(
                            select(ModuleContent).where(ModuleContent.id == mc.id)
                        )
                        mc_board = r4.scalar_one_or_none()
                        if mc_board:
                            mc_board.board_data = board_data
                            await db.commit()

                    # 通知前端板书已就绪（含图片）
                    await sse_manager.send_event(uid, session_id, {
                        "event": "boards_ready", "data": board_data
                    })
            except Exception as be:
                logger.warning(f"板书生成失败(不影响教学): {be}")

            await sse_manager.send_event(uid, session_id, {
                "event": "completed", "data": {"content": full_text, "module_index": request.module_index}
            })
            # 发送终止信号，让 SSE 流端点退出并清理
            await sse_manager.send_event(uid, session_id, None)

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

                # 发送板书数据（如果有，没有也不阻塞教学）
                board_data = mc.board_data if mc and mc.board_data else None
                if board_data and board_data.get('boards'):
                    # 补充 image_url：检查本地图片文件是否存在，如果DB中缺失但文件已有则补上
                    from app.services.image_gen import BOARD_IMAGE_DIR
                    import os as _os
                    for i, b in enumerate(board_data['boards']):
                        if not b.get('image_url'):
                            filename = f"board_{request.outline_id}_{request.module_index}_{i}.png"
                            filepath = _os.path.join(BOARD_IMAGE_DIR, filename)
                            if _os.path.exists(filepath):
                                b['image_url'] = f"/static/boards/{filename}"
                    try:
                        await sse_manager.send_event(uid, session_id, {
                            "event": "boards_ready", "data": board_data
                        })
                    except Exception as be:
                        logger.warning(f"发送板书数据失败(继续教学): {be}")

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

                # 板书切换跟踪 — 基于时间间隔，与token进度解耦
                boards_list = board_data.get('boards', []) if board_data else []
                current_board_index = -1
                last_board_switch_time = 0
                # 每张板书最少展示时长（秒），根据模块总时长和板书数动态计算
                module_duration_sec = mod.get('duration', 20) * 60  # 转为秒
                min_board_interval = max(module_duration_sec / max(len(boards_list), 1), 30)  # 至少30秒
                # 课堂开始5秒后切换到第一张板书
                if boards_list:
                    import time as _time
                    last_board_switch_time = _time.monotonic() - min_board_interval + 5

                async for chunk in llm.astream([
                    SystemMessage(content=system),
                    HumanMessage(content=request.message)
                ]):
                    token = chunk.content if hasattr(chunk, 'content') else str(chunk)
                    if token:
                        await sse_manager.send_event(uid, session_id, {
                            "event": "token", "data": {"token": token}
                        })

                        # 检查是否需要切换板书（时间间隔驱动，非进度驱动）
                        if boards_list and current_board_index < len(boards_list) - 1:
                            try:
                                import time as _time
                                now = _time.monotonic()
                                elapsed = now - last_board_switch_time
                                if elapsed >= min_board_interval and current_board_index < len(boards_list) - 1:
                                    current_board_index += 1
                                    last_board_switch_time = now
                                    await sse_manager.send_event(uid, session_id, {
                                        "event": "board_switch", "data": {
                                            "board": boards_list[current_board_index],
                                            "index": current_board_index,
                                            "total": len(boards_list),
                                        }
                                    })
                            except Exception as bse:
                                logger.debug(f"板书切换异常(忽略): {bse}")
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
            # 发送终止信号，让 SSE 流端点退出循环并清理
            await sse_manager.send_event(uid, session_id, None)

        except Exception as e:
            logger.error(f"模块教学失败: {e}", exc_info=True)
            await sse_manager.send_event(uid, session_id, {"event": "error", "data": {"message": str(e)}})

    asyncio.create_task(run_teach())
    return {
        "session_id": session_id,
        "status": "teaching",
        "stream_url": f"/api/v1/ai/stream/{session_id}"
    }


class AskQuestionRequest(BaseModel):
    """课堂提问请求"""
    outline_id: int = Field(..., description="大纲ID")
    module_index: int = Field(..., ge=1, description="当前模块序号")
    lecture_context: str = Field("", description="当前已讲授的内容")
    question: str = Field("", description="学生的问题")
    teacher_style: str = Field("default", description="教师风格")


async def _generate_board_images_async(
    uid: int,
    session_id: str,
    module_content_id: int,
    board_data: dict,
    outline_id: int,
    module_index: int,
):
    """后台异步生成板书图片，生成完毕后更新DB并通知前端"""
    try:
        from app.services.image_gen import generate_board_image
        boards = board_data.get('boards', [])
        for i, board in enumerate(boards):
            prompt = board.get('image_prompt', '')
            if not prompt:
                continue
            image_url = await generate_board_image(
                prompt=prompt,
                outline_id=outline_id,
                module_index=module_index,
                board_index=i,
            )
            if image_url:
                board['image_url'] = image_url
                # 每生成一张图就通知前端更新
                try:
                    await sse_manager.send_event(uid, session_id, {
                        "event": "board_image_ready", "data": {
                            "index": i,
                            "image_url": image_url,
                            "board": board
                        }
                    })
                except Exception:
                    pass  # SSE可能已关闭

        # 更新数据库中的board_data（含image_url）
        from app.db.session import async_session_factory
        from app.models.conversation import ModuleContent
        from sqlalchemy import select as sa_select
        async with async_session_factory() as db:
            r = await db.execute(
                sa_select(ModuleContent).where(ModuleContent.id == module_content_id)
            )
            mc = r.scalar_one_or_none()
            if mc:
                mc.board_data = board_data
                await db.commit()
        logger.info(f"板书图片生成完成: outline={outline_id} module={module_index}")
    except Exception as e:
        logger.warning(f"板书图片生成异常(不影响教学): {e}")


class RegenerateBoardsRequest(BaseModel):
    """重新生成板书请求"""
    outline_id: int = Field(..., description="大纲ID")
    module_index: Optional[int] = Field(None, ge=1, description="模块序号(不传则重新生成全部)")


@router.post("/tutor/regenerate-boards")
async def regenerate_boards(
    request: RegenerateBoardsRequest,
    current_user=Depends(get_current_user),
):
    """为已有模块内容重新生成板书"""
    uid = current_user["id"]
    from app.db.session import async_session_factory
    from app.models.conversation import ModuleContent
    from app.models.outline import Outline
    from sqlalchemy import select

    async with async_session_factory() as db:
        # 加载大纲获取模块信息
        r = await db.execute(select(Outline).where(Outline.id == request.outline_id, Outline.user_id == uid))
        outline = r.scalar_one_or_none()
        if not outline:
            raise HTTPException(status_code=404, detail="大纲不存在")

        modules = outline.modules_data or []

        # 确定要处理的模块
        if request.module_index:
            indices = [request.module_index]
        else:
            # 所有已有内容的模块
            r2 = await db.execute(
                select(ModuleContent).where(
                    ModuleContent.outline_id == request.outline_id,
                    ModuleContent.user_id == uid,
                    ModuleContent.status == "completed"
                )
            )
            existing = r2.scalars().all()
            indices = [mc.module_index for mc in existing]

    results = []
    for idx in indices:
        if idx < 1 or idx > len(modules):
            continue

        mod = modules[idx - 1]
        module_name = mod.get("name", "")
        key_points = mod.get("keyPoints", [])
        duration = mod.get("duration", 20)

        async with async_session_factory() as db:
            r3 = await db.execute(
                select(ModuleContent).where(
                    ModuleContent.outline_id == request.outline_id,
                    ModuleContent.module_index == idx,
                    ModuleContent.user_id == uid,
                    ModuleContent.status == "completed"
                )
            )
            mc = r3.scalar_one_or_none()
            if not mc or not mc.content:
                continue

            # 生成板书
            from app.langgraph.board_agent import generate_boards_for_module
            board_data = await generate_boards_for_module(
                module_name=module_name,
                module_content=mc.content,
                key_points=key_points,
                duration=duration
            )

            if board_data:
                mc.board_data = board_data
                await db.commit()

                # 异步生成板书图片（regenerate场景没有活跃SSE，只存DB）
                asyncio.create_task(_generate_board_images_async(
                    uid=uid, session_id="",
                    module_content_id=mc.id,
                    board_data=board_data, outline_id=request.outline_id, module_index=idx
                ))

                results.append({
                    "module_index": idx,
                    "module_name": module_name,
                    "board_count": len(board_data.get("boards", [])),
                    "status": "ok"
                })
            else:
                results.append({
                    "module_index": idx,
                    "module_name": module_name,
                    "status": "failed"
                })

    return {"results": results}


@router.post("/tutor/ask")
async def ask_teacher_question(
    request: AskQuestionRequest,
    current_user=Depends(get_current_user),
):
    """课堂提问 - 学生向AI教师提问，基于当前讲授内容解答疑惑"""
    uid = current_user["id"]
    session_id = f"ask_{uid}_{request.outline_id}_{int(datetime.now(timezone.utc).timestamp())}"
    queue = await sse_manager.connect(uid, session_id)

    async def run_answer():
        try:
            from app.db.session import async_session_factory
            from app.models.outline import Outline
            from app.models.conversation import ModuleContent
            from sqlalchemy import select

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

                r2 = await db.execute(
                    select(ModuleContent).where(
                        ModuleContent.outline_id == request.outline_id,
                        ModuleContent.module_index == request.module_index,
                        ModuleContent.user_id == uid,
                        ModuleContent.status == "completed"
                    )
                )
                mc = r2.scalar_one_or_none()
                pre_content = mc.content if mc else ""

            style_map = {"humorous": "幽默风趣", "rigorous": "严谨认真", "default": "亲切耐心"}
            style = style_map.get(request.teacher_style, "亲切耐心")

            system = f"""你是AI虚拟课堂的讲师，正在教授课程"{outline.title}"的模块"{mod.get('name','')}"。
你用{style}的风格教学。

学生现在提出了一个问题，请你基于已讲授的内容来解答学生的疑惑。
解答要求：
1. 用{style}的风格回答
2. 基于已讲授的内容和课程知识来解答
3. 回答简洁明了，不要冗长
4. 如果学生的问题与当前教学无关，温和地引导回课堂内容
5. 严禁Markdown格式！用自然口语回答，不要用特殊符号标记"""

            if pre_content:
                system += f"\n\n你的备课内容（参考）：\n{pre_content[:2000]}"

            if request.lecture_context:
                system += f"\n\n目前已经讲授的内容：\n{request.lecture_context[:1500]}"

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
                HumanMessage(content=request.question)
            ]):
                token = chunk.content if hasattr(chunk, 'content') else str(chunk)
                if token:
                    await sse_manager.send_event(uid, session_id, {
                        "event": "token", "data": {"token": token}
                    })

            await sse_manager.send_event(uid, session_id, {"event": "done", "data": {}})
            await sse_manager.send_event(uid, session_id, None)

        except Exception as e:
            logger.error(f"课堂提问回答失败: {e}", exc_info=True)
            await sse_manager.send_event(uid, session_id, {"event": "error", "data": {"message": str(e)}})

    asyncio.create_task(run_answer())
    return {
        "session_id": session_id,
        "status": "answering",
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
    token: Optional[str] = None,
):
    """通用SSE流式输出端点（使用原生 StreamingResponse，兼容性更好）
    支持 query param token（EventSource 不支持自定义 header）
    """
    # 从 header 或 query param 获取用户身份
    uid = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        from app.core.security import verify_token
        payload = verify_token(auth_header[7:])
        if payload:
            uid = payload.get("user_id")
    
    if uid is None and token:
        from app.core.security import verify_token
        payload = verify_token(token)
        if payload:
            uid = payload.get("user_id")
    
    # 开发模式 fallback
    if uid is None:
        from app.core.config import settings
        if settings.DEBUG:
            uid = 1
        else:
            raise HTTPException(status_code=401, detail="请先登录")

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


# ─── AI学伴智能体 ───

COMPANION_PROFILES = {
    "scholar": {
        "name": "小明",
        "avatar": "🎓",
        "type_label": "学霸型",
        "system_prompt": """你是AI学伴"小明"，一个学霸型的学习伙伴。
性格：自信、知识丰富、偶尔爱炫耀知识，但很热心。
行为特点：
- 回答正确率高（约90%），会给出准确的知识点
- 偶尔分享一些课外的拓展知识
- 对老师的讲解会给出积极的肯定，如"这个讲得很清楚"
- 说话简洁有底气，偶尔带点小骄傲
- 称呼用户为"同学"
每次发言控制在1-2句话，简洁有力。""",
    },
    "social": {
        "name": "小乐",
        "avatar": "😎",
        "type_label": "显眼包",
        "system_prompt": """你是AI学伴"小乐"，一个显眼包型的学习伙伴。
性格：活泼、爱互动、爱提问、有点话痨，课堂气氛担当。
行为特点：
- 经常主动发言，对什么都感兴趣
- 爱问问题，如"为什么是这样呢？""那如果不这样会怎样？"
- 说话风格轻松活泼，经常用语气词如"哇""哦～""嗯嗯"
- 偶尔会跑偏话题，但很快拉回来
- 爱用表情符号和感叹号
- 称呼用户为"小伙伴"
每次发言控制在1-2句话，活泼有趣。""",
    },
    "introvert": {
        "name": "小静",
        "avatar": "🤫",
        "type_label": "内向型",
        "system_prompt": """你是AI学伴"小静"，一个内向型的学习伙伴。
性格：安静、害羞、不太主动说话，但内心很有想法。
行为特点：
- 很少主动发言，发言频率低
- 说话声音小（用"……""嗯""也许"开头）
- 但一旦发言，往往有独到的见解
- 偶尔会小声说"我觉得……也许不完全是那样"
- 不会主动跟老师打招呼
- 称呼用户为"同学"
每次发言控制在1句话，简短含蓄。""",
    },
}


class CompanionGreetRequest(BaseModel):
    """学伴打招呼请求"""
    outline_id: int = Field(..., description="大纲ID")
    module_index: int = Field(..., description="模块索引")
    companions: list = Field(..., description="学伴类型列表，如['scholar','social']")


class CompanionCommentRequest(BaseModel):
    """学伴评论请求"""
    outline_id: int = Field(..., description="大纲ID")
    module_index: int = Field(..., description="模块索引")
    lecture_text: str = Field(..., description="当前讲授内容片段")
    companions: list = Field(..., description="学伴类型列表")


class CompanionDiscussRequest(BaseModel):
    """学伴讨论请求"""
    outline_id: int = Field(..., description="大纲ID")
    module_index: int = Field(..., description="模块索引")
    topic: str = Field(..., description="讨论话题")
    user_message: str = Field("", description="用户发言内容（讨论中追加）")
    discussion_history: list = Field(default_factory=list, description="已有讨论记录")
    companions: list = Field(..., description="学伴类型列表")


async def _call_companion_llm(system_prompt: str, user_msg: str) -> str:
    """调用LLM生成学伴发言"""
    from langchain_core.messages import HumanMessage, SystemMessage
    try:
        from app.langgraph.tutor_agent import _get_llm as get_tutor_llm
        llm = get_tutor_llm()
        # 学伴用非流式
        from langchain_deepseek import ChatDeepSeek
        from app.core.config import settings
        llm = ChatDeepSeek(
            model=settings.DEEPSEEK_MODEL,
            api_key=settings.DEEPSEEK_API_KEY,
            temperature=0.9,
            streaming=False
        )
        response = await llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_msg)
        ])
        text = response.content if hasattr(response, 'content') else str(response)
        return text.strip().strip('"').strip("'")
    except Exception as e:
        logger.warning(f"学伴LLM调用失败: {e}")
        return ""


@router.post("/companion/greet")
async def companion_greet(
    request: CompanionGreetRequest,
    current_user=Depends(get_current_user),
):
    """学伴在课堂开始时跟老师打招呼（内向型不会打招呼）"""
    greetings = []
    for ctype in request.companions:
        profile = COMPANION_PROFILES.get(ctype)
        if not profile:
            continue
        # 内向型不打招呼
        if ctype == "introvert":
            continue

        module_name = ""
        try:
            from app.langgraph.outline_agent import get_outline_from_db
            outline_data = await get_outline_from_db(request.outline_id)
            if outline_data:
                modules = outline_data.get("modules_data", outline_data.get("modulesData", []))
                if isinstance(modules, str):
                    import json as _json
                    modules = _json.loads(modules)
                idx = request.module_index - 1
                if 0 <= idx < len(modules):
                    module_name = modules[idx].get("name", "")
        except:
            pass

        user_msg = f"课堂刚开始了，主题是「{module_name}」。请跟老师和同学们打个招呼，简短1-2句话。"
        text = await _call_companion_llm(profile["system_prompt"], user_msg)
        if text:
            greetings.append({
                "type": ctype,
                "name": profile["name"],
                "avatar": profile["avatar"],
                "text": text,
            })
    return {"greetings": greetings}


@router.post("/companion/comment")
async def companion_comment(
    request: CompanionCommentRequest,
    current_user=Depends(get_current_user),
):
    """学伴根据讲授内容发表评论或疑惑"""
    comments = []
    import random
    for ctype in request.companions:
        profile = COMPANION_PROFILES.get(ctype)
        if not profile:
            continue
        # 内向型只有20%概率发言，显眼包80%，学霸50%
        speak_chance = {"scholar": 0.5, "social": 0.8, "introvert": 0.2}.get(ctype, 0.3)
        if random.random() > speak_chance:
            continue

        user_msg = f"老师正在讲：「{request.lecture_text[:500]}」\n请根据这段内容，用你自己的性格发表一句简短评论或疑惑（1-2句话）。"
        text = await _call_companion_llm(profile["system_prompt"], user_msg)
        if text:
            comments.append({
                "type": ctype,
                "name": profile["name"],
                "avatar": profile["avatar"],
                "text": text,
            })
    return {"comments": comments}


@router.post("/companion/discuss")
async def companion_discuss(
    request: CompanionDiscussRequest,
    current_user=Depends(get_current_user),
):
    """发起/继续学伴讨论，所有学伴依次发言"""
    # 构建讨论上下文
    history_text = ""
    for h in request.discussion_history[-10:]:  # 最近10条
        history_text += f"{h.get('name', '')}: {h.get('text', '')}\n"

    responses = []
    for ctype in request.companions:
        profile = COMPANION_PROFILES.get(ctype)
        if not profile:
            continue

        user_msg = f"""讨论话题：「{request.topic}」
用户发言：「{request.user_message}」
之前的讨论：
{history_text if history_text else '（刚刚开始讨论）'}

请用你自己的性格参与讨论，发表你的看法（1-2句话）。"""

        text = await _call_companion_llm(profile["system_prompt"], user_msg)
        if text:
            responses.append({
                "type": ctype,
                "name": profile["name"],
                "avatar": profile["avatar"],
                "text": text,
            })
            # 更新历史，让下一个学伴能看到之前的发言
            history_text += f"{profile['name']}: {text}\n"

    return {"responses": responses}
