"""
大纲生成智能体 V3 - 简洁三步流程
1. 询问想学什么知识
2. 提供选项让用户选择程度（初级/中级/高级）
3. 询问每天/每周能投入的时间
4. 收集完毕后直接生成大纲
"""
import logging
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

_llm = None

# ─── 学习程度选项 ───
LEVEL_OPTIONS = [
    {"value": "beginner", "label": "🟢 初级", "desc": "零基础或刚入门，需要从基础开始"},
    {"value": "intermediate", "label": "🟡 中级", "desc": "有一定基础，想系统提升"},
    {"value": "advanced", "label": "🔴 高级", "desc": "已有较好基础，想深入精通"},
]

# ─── 步骤定义 ───
STEP_ASK_TOPIC = 1      # 问想学什么
STEP_ASK_LEVEL = 2      # 让用户选程度
STEP_ASK_TIME = 3       # 问时间投入
STEP_GENERATE = 4       # 生成大纲


def _get_llm():
    """获取DeepSeek LLM实例"""
    global _llm
    if _llm is None:
        from langchain_deepseek import ChatDeepSeek
        from app.core.config import settings
        _llm = ChatDeepSeek(
            model=settings.DEEPSEEK_MODEL,
            api_key=settings.DEEPSEEK_API_KEY,
            temperature=0.7,
            streaming=True
        )
    return _llm


# ─── 数据库操作 ───

async def _save_conversation_turn(
    user_id: int,
    session_id: str,
    round_num: int,
    role: str,
    content: str,
    collected_info: dict = None,
    step: int = 0
):
    """保存对话轮次到MySQL"""
    try:
        from app.db.session import async_session_factory
        from app.models.conversation import OutlineConversation

        async with async_session_factory() as db:
            record = OutlineConversation(
                user_id=user_id,
                session_id=session_id,
                round_num=round_num,
                role=role,
                content=content,
                collected_info=collected_info or {},
                asked_questions=[str(step)] if step else []
            )
            db.add(record)
            await db.commit()
    except Exception as e:
        logger.warning(f"Failed to save conversation turn: {e}")


async def _load_conversation_history(user_id: int, session_id: str) -> List[dict]:
    """从MySQL加载对话历史"""
    try:
        from app.db.session import async_session_factory
        from app.models.conversation import OutlineConversation
        from sqlalchemy import select

        async with async_session_factory() as db:
            result = await db.execute(
                select(OutlineConversation)
                .where(
                    OutlineConversation.user_id == user_id,
                    OutlineConversation.session_id == session_id
                )
                .order_by(OutlineConversation.round_num.asc())
            )
            records = result.scalars().all()
            return [
                {
                    "round": r.round_num,
                    "role": r.role,
                    "content": r.content,
                    "collected_info": r.collected_info,
                    "asked_questions": r.asked_questions
                }
                for r in records
            ]
    except Exception as e:
        logger.warning(f"Failed to load conversation history: {e}")
        return []


async def _get_collected_info(user_id: int, session_id: str) -> Dict[str, str]:
    """汇总已收集的用户信息"""
    history = await _load_conversation_history(user_id, session_id)
    collected = {}
    for record in history:
        if record.get("collected_info"):
            collected.update(record["collected_info"])
    return collected


async def _determine_current_step(user_id: int, session_id: str) -> int:
    """
    根据历史对话判断当前应该进行到哪一步。
    检查 collected_info 中的 topic、level、time 三个字段。
    """
    info = await _get_collected_info(user_id, session_id)

    topic = info.get("topic", "")
    level = info.get("level", "")
    time = info.get("time", "")

    if not topic:
        return STEP_ASK_TOPIC
    if not level:
        return STEP_ASK_LEVEL
    if not time:
        return STEP_ASK_TIME
    return STEP_GENERATE


async def _extract_topic_from_message(user_message: str) -> Optional[str]:
    """从用户消息中提取学习主题"""
    text = user_message.strip()

    # 如果很短且有意义，直接用作主题
    if len(text) <= 60:
        return text

    # 用LLM提取
    llm = _get_llm()
    from langchain_core.messages import HumanMessage, SystemMessage

    system = """从用户消息中提取他想学习的具体知识/技能名称。只返回名称，不要多余内容。
示例：用户说"我想学Python基础" → 返回 "Python基础"
示例：用户说"帮我复习数据结构" → 返回 "数据结构"
如果无法提取，返回用户消息的前30个字符。"""

    try:
        response = await llm.ainvoke([
            SystemMessage(content=system),
            HumanMessage(content=user_message)
        ])
        topic = response.content.strip() if hasattr(response, 'content') else str(response).strip()
        # 清理引号
        topic = topic.strip('"\'').strip()
        if len(topic) > 50:
            topic = topic[:50]
        return topic or text[:30]
    except Exception:
        return text[:30]


async def _extract_time_from_message(user_message: str) -> Optional[str]:
    """从用户消息中提取时间投入信息"""
    text = user_message.strip()

    # 规则匹配
    patterns = [
        r'每天\s*(\d+)\s*(?:小时|个?小时|h)',   # 每天2小时
        r'(\d+)\s*(?:小时|个?小时|h)\s*(?:/|每)?天',  # 2小时/天
        r'每周\s*(\d+)\s*(?:小时|天|次)',         # 每周3小时
        r'每天\s*(\d+)\s*(?:分钟|分)',           # 每天30分钟
        r'(\d+)\s*分钟\s*(?:/|每)?天',           # 30分钟/天
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(0)

    # 模糊匹配
    if "每天" in text or "一天" in text or "每日" in text:
        return text[:60]

    if "每周" in text or "一周" in text:
        return text[:60]

    return None


def _build_outline_system_prompt(topic: str, level: str, time_info: str) -> str:
    """构建大纲生成的System Prompt"""
    level_map = {
        "beginner": "初级（零基础入门）",
        "intermediate": "中级（有一定基础，需系统提升）",
        "advanced": "高级（已有较好基础，需深入精通）"
    }
    level_desc = level_map.get(level, "初级")

    return f"""你是一位资深的学习路径设计师。请为用户生成一份具体、可执行的学习大纲。

## 用户信息
- 学习主题：{topic}
- 程度等级：{level_desc}
- 时间投入：{time_info or "未明确"}

## 大纲要求
1. 针对 "{topic}" 这个具体主题，不要泛泛而谈
2. 根据 {level_desc} 调整内容深度和难度
3. 每个模块有明确的交付物：学完这个模块用户能做出什么
4. 模块间有递进关系
5. 包含实战练习
6. 4-6个模块，每个模块标注建议时长（分钟为单位，不要用小时）

## 输出格式（严格遵守，禁止使用任何Markdown格式标记！）
# {topic} - 学习大纲

学习概览：
目标：[一句话总结]
程度：{level_desc}
总时长：[X分钟，数字即可]
适合人群：[描述]

## 模块1: [模块名称]
建议时长：X分钟
学完后你能：[具体能力描述]
知识点1：[具体描述]
知识点2：[具体描述]
练习：[具体练习内容]

## 模块2: [模块名称]
建议时长：X分钟
...

（以此类推4-6个模块）

## 学习建议
[根据用户的程度和时间给出个性化建议]

## 重要规则
- 模块名称只写核心内容名，不要在名称里缀上时间
- 禁止使用 **、*、>、- 等Markdown标记，只用纯文本
- 时长统一用分钟，不要用小数"""


# ─── 主流程 ───

async def run_outline_workflow(
    user_id: int,
    session_id: str,
    user_message: str,
    sse_queue,
    topic: str = "",
    level: str = "beginner"
) -> dict:
    """
    执行大纲生成工作流。

    返回: {"ai_output": str, "context": {...}, "collected_info": {...}}
    """
    logger.info(f"[OutlineAgent V3] Starting workflow for user={user_id}, session={session_id}")

    # 1. 确定当前步骤
    current_step = await _determine_current_step(user_id, session_id)
    collected_info = await _get_collected_info(user_id, session_id)

    # 加载历史获取轮次
    history = await _load_conversation_history(user_id, session_id)
    round_num = len([h for h in history if h["role"] == "user"]) + 1

    # 保存用户消息
    await _save_conversation_turn(
        user_id=user_id, session_id=session_id,
        round_num=round_num, role="user",
        content=user_message, step=current_step
    )

    logger.info(f"[OutlineAgent V3] Current step={current_step}, collected={list(collected_info.keys())}")

    # 2. 根据步骤处理
    if current_step == STEP_ASK_TOPIC:
        return await _handle_step_topic(user_id, session_id, user_message, sse_queue, round_num, collected_info)

    elif current_step == STEP_ASK_LEVEL:
        return await _handle_step_level(user_id, session_id, user_message, sse_queue, round_num, collected_info)

    elif current_step == STEP_ASK_TIME:
        return await _handle_step_time(user_id, session_id, user_message, sse_queue, round_num, collected_info)

    else:
        return await _handle_generate(user_id, session_id, user_message, sse_queue, round_num, collected_info)


async def _handle_step_topic(
    user_id, session_id, user_message, sse_queue, round_num, collected_info
) -> dict:
    """Step 1: 用户说想学什么 → 提取主题 → 跳转到问程度"""
    topic = await _extract_topic_from_message(user_message)

    collected_info["topic"] = topic
    new_step = STEP_ASK_LEVEL

    # 构建回复：确认主题，然后给出程度选项
    ai_text = f"好的，「{topic}」是个很棒的学习方向！\n\n接下来请选择你目前的水平程度："

    # 发送 token 流
    for char in ai_text:
        if sse_queue:
            await sse_queue.put({"event": "token", "data": {"token": char}})

    # 发送选项事件，让前端渲染可点击按钮
    if sse_queue:
        await sse_queue.put({
            "event": "options",
            "data": {
                "step": new_step,
                "question": "你的当前水平是？",
                "options": LEVEL_OPTIONS
            }
        })

    # 保存AI回复
    await _save_conversation_turn(
        user_id=user_id, session_id=session_id,
        round_num=round_num + 1, role="assistant",
        content=ai_text,
        collected_info={"topic": topic},
        step=new_step
    )

    return {
        "ai_output": ai_text,
        "context": {
            "current_step": new_step,
            "should_generate": False,
            "collected_info": collected_info,
            "has_options": True,
            "options": LEVEL_OPTIONS
        }
    }


async def _handle_step_level(
    user_id, session_id, user_message, sse_queue, round_num, collected_info
) -> dict:
    """Step 2: 用户选择程度 → 记录 → 跳转到问时间"""
    text = user_message.strip()

    # 匹配程度
    level_map = {
        "beginner": ["初级", "入门", "基础", "beginner", "1", "初级", "零基础", "新手", "初学"],
        "intermediate": ["中级", "进阶", "intermediate", "2", "中级", "中等", "一般"],
        "advanced": ["高级", "精通", "advanced", "3", "高级", "深入", "专家"],
    }

    detected_level = "beginner"  # 默认
    for lv, keywords in level_map.items():
        if any(kw in text for kw in keywords):
            detected_level = lv
            break

    level_labels = {
        "beginner": "初级（零基础入门）",
        "intermediate": "中级（有一定基础）",
        "advanced": "高级（深入精通）"
    }

    collected_info["level"] = detected_level
    new_step = STEP_ASK_TIME

    level_label = level_labels.get(detected_level, "初级")
    ai_text = f"了解了，你的程度是 **{level_label}**。\n\n最后问一下，你每天或每周大概能投入多少时间来学习呢？（比如：每天1小时 / 每周3小时）"

    # 发送 token 流
    for char in ai_text:
        if sse_queue:
            await sse_queue.put({"event": "token", "data": {"token": char}})

    # 发送 step 事件
    if sse_queue:
        await sse_queue.put({
            "event": "step",
            "data": {
                "step": new_step,
                "question": "你能投入多少时间？",
                "hint": "比如：每天1小时 / 每周3小时 / 每天30分钟"
            }
        })

    # 保存
    await _save_conversation_turn(
        user_id=user_id, session_id=session_id,
        round_num=round_num + 1, role="assistant",
        content=ai_text,
        collected_info={"level": detected_level},
        step=new_step
    )

    return {
        "ai_output": ai_text,
        "context": {
            "current_step": new_step,
            "should_generate": False,
            "collected_info": collected_info
        }
    }


async def _handle_step_time(
    user_id, session_id, user_message, sse_queue, round_num, collected_info
) -> dict:
    """Step 3: 用户说时间 → 记录 → 直接生成大纲"""
    time_info = await _extract_time_from_message(user_message)

    if time_info:
        collected_info["time"] = time_info
    else:
        # 用户可能说了其他内容，尽量保留
        collected_info["time"] = user_message.strip()[:60]

    new_step = STEP_GENERATE

    # 提示即将生成
    intro = "好的，信息收集完毕！正在为你生成学习大纲...\n\n"
    for char in intro:
        if sse_queue:
            await sse_queue.put({"event": "token", "data": {"token": char}})

    # 保存
    await _save_conversation_turn(
        user_id=user_id, session_id=session_id,
        round_num=round_num + 1, role="assistant",
        content=intro,
        collected_info={"time": collected_info.get("time", "")},
        step=new_step
    )

    # 直接调用生成
    return await _handle_generate(
        user_id, session_id, user_message, sse_queue, round_num, collected_info
    )


async def _handle_generate(
    user_id, session_id, user_message, sse_queue, round_num, collected_info
) -> dict:
    """Step 4: 生成大纲"""
    topic = collected_info.get("topic", user_message[:50])
    level = collected_info.get("level", "beginner")
    time_info = collected_info.get("time", "")

    llm = _get_llm()
    from langchain_core.messages import HumanMessage, SystemMessage

    system = _build_outline_system_prompt(topic, level, time_info)
    user_msg = f"请为我生成「{topic}」的学习大纲。"

    msgs = [SystemMessage(content=system), HumanMessage(content=user_msg)]

    full_text = ""
    try:
        async for chunk in llm.astream(msgs):
            token = chunk.content if hasattr(chunk, 'content') else str(chunk)
            if token:
                full_text += token
                if sse_queue:
                    await sse_queue.put({"event": "token", "data": {"token": token}})
    except Exception as e:
        logger.error(f"大纲生成失败: {e}", exc_info=True)
        full_text = f"大纲生成失败: {str(e)}"

    # 保存生成的完整大纲
    await _save_conversation_turn(
        user_id=user_id, session_id=session_id,
        round_num=round_num + 1, role="assistant",
        content=full_text,
        collected_info=collected_info,
        step=STEP_GENERATE
    )

    return {
        "ai_output": full_text,
        "context": {
            "current_step": STEP_GENERATE,
            "should_generate": True,
            "collected_info": collected_info
        }
    }


# ─── 大纲解析（保持不变） ───

def parse_outline_to_modules(text: str, topic: str = "", level: str = "beginner") -> dict:
    """将AI生成的大纲文本解析为结构化模块数据"""
    modules = []
    title = topic or "学习大纲"
    current_module = None

    for line in text.split('\n'):
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # 识别标题
        if line_stripped.startswith('# ') and not line_stripped.startswith('## '):
            title = line_stripped.replace('# ', '').strip()
            title = re.sub(r'\s*[-—]\s*学习大纲$', '', title)
            continue

        # 识别模块 (## 模块X: 或 ## 模块X )
        module_match = re.match(r'^##\s*(?:模块\s*)?(\d+)[:：\s]\s*(.+)', line_stripped)
        if module_match:
            if current_module and current_module.get("name"):
                modules.append(current_module)

            module_name = module_match.group(2).strip()
            duration = 20
            # 清除模块名中的时间后缀（各种格式）
            module_name = re.sub(r'\s*[（(]\s*\d+(?:\.\d+)?\s*(?:小时|分钟|h|H|min|MIN)\s*[）)]', '', module_name).strip()
            module_name = re.sub(r'\s+\d+(?:\.\d+)?\s*(?:小时|分钟|h|H)\s*$', '', module_name).strip()

            current_module = {
                "id": len(modules) + 1,
                "name": module_name,
                "duration": duration,
                "difficulty": level or "beginner",
                "keyPoints": [],
                "deliverable": ""
            }
            continue

        # 识别独立时长行：建议时长：X分钟
        if current_module:
            dur_match = re.search(r'(?:建议时长|时长)[：:]\s*(\d+)\s*分钟', line_stripped)
            if dur_match:
                current_module["duration"] = int(dur_match.group(1))
                continue

        # 识别"学完后你能"
        if current_module and ('学完后你能' in line_stripped or '学完后可以' in line_stripped):
            deliverable = re.sub(r'\*{1,2}学完后你[能可][：:]*\*{1,2}\s*', '', line_stripped)
            deliverable = re.sub(r'学完后你[能可][：:]*\s*', '', deliverable)
            current_module["deliverable"] = deliverable.strip()
            continue

        # 识别知识点和练习（支持 -、*、数字列表 以及纯文本 key:value 格式）
        if current_module:
            # Markdown 列表格式
            list_match = re.match(r'^[-*]\s*(.+)', line_stripped)
            # 纯文本格式：知识点X： 或 练习：
            plain_match = re.match(r'^(?:知识点\d*|练习)[：:]\s*(.+)', line_stripped)
            if list_match:
                point = list_match.group(1).strip()
            elif plain_match:
                point = plain_match.group(1).strip()
            else:
                point = None

            if point:
                # 去掉行内的 Markdown ** 和 emoji
                point = re.sub(r'\*{1,2}', '', point)
                point = re.sub(r'^[📖✏️🎯🛠💡🔥✅📝🔧]\s*', '', point)
                current_module["keyPoints"].append(point)
            continue
            point = re.sub(r'^[📖✏️🔧💻📝🎯✅]+\s*', '', point)
            if point and point not in current_module["keyPoints"]:
                current_module["keyPoints"].append(point)

    if current_module and current_module.get("name"):
        modules.append(current_module)

    # 兜底
    if not modules:
        modules = [
            {"id": 1, "name": "基础知识", "duration": 20, "difficulty": level,
             "keyPoints": ["核心概念理解", "基础操作练习"], "deliverable": "掌握基本概念和操作"},
            {"id": 2, "name": "进阶应用", "duration": 25, "difficulty": level,
             "keyPoints": ["实际案例分析", "动手实践"], "deliverable": "能够独立完成简单项目"},
            {"id": 3, "name": "综合项目", "duration": 15, "difficulty": level,
             "keyPoints": ["综合练习", "成果展示"], "deliverable": "完成一个完整项目"},
        ]

    total_duration = sum(m.get("duration", 0) for m in modules)
    return {"title": title, "total_duration": total_duration, "modules": modules}


# ─── PDF 解析 ───

def extract_pdf_text(file_bytes: bytes) -> str:
    """从 PDF 字节流中提取全文"""
    from PyPDF2 import PdfReader
    from io import BytesIO
    reader = PdfReader(BytesIO(file_bytes))
    texts = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            texts.append(t)
    return '\n'.join(texts)


async def generate_outline_from_pdf_text(
    pdf_text: str,
    topic: str,
    level: str,
    filename: str
) -> str:
    """根据 PDF 文本内容生成学习大纲（返回大纲 markdown 文本）"""
    llm = _get_llm()

    # 取 PDF 前 8000 字符作为摘要输入，避免 token 超限
    text_preview = pdf_text[:8000] if len(pdf_text) > 8000 else pdf_text

    system = _build_outline_system_prompt(topic, level, "根据PDF资料")

    prompt = f"""以下是一份学习资料的文本内容（文件名：{filename}）：

=== 资料内容开始 ===
{text_preview}
=== 资料内容结束 ===

请根据以上资料内容，为「{topic}」生成一份学习大纲。
大纲要覆盖资料中的核心知识点，模块划分合理，4-6 个模块。
严格按要求的输出格式返回，禁止使用 Markdown 标记。"""

    from langchain_core.messages import SystemMessage, HumanMessage
    response = await llm.ainvoke([
        SystemMessage(content=system),
        HumanMessage(content=prompt)
    ])
    return response.content
