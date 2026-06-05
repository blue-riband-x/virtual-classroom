"""
初始化所有Agent并注册到Orchestrator
使用重构后的 V2 版本智能体
"""
import logging
from app.langgraph.orchestrator import orchestrator, AgentType

logger = logging.getLogger(__name__)

try:
    from langgraph.graph import StateGraph, END
    _HAS_LANGGRAPH = True
except ImportError:
    _HAS_LANGGRAPH = False
    logger.warning("⚠️ langgraph not installed")


def _get_llm():
    """获取DeepSeek LLM实例（用于简单Agent）"""
    from langchain_deepseek import ChatDeepSeek
    from app.core.config import settings
    return ChatDeepSeek(
        model=settings.DEEPSEEK_MODEL,
        api_key=settings.DEEPSEEK_API_KEY,
        temperature=0.7,
        streaming=True
    )


def create_grader_graph():
    """评分Agent - 独立职责，只评分不教学"""
    from app.langgraph.state import MultiAgentState
    from langchain_core.messages import HumanMessage, SystemMessage

    graph = StateGraph(MultiAgentState)

    async def grade_node(state: MultiAgentState) -> MultiAgentState:
        llm = _get_llm()
        system = """你是AI虚拟课堂的评分专家。你的职责是对学生的回答进行评分。

评分规则：
- 正确性（40分）：答案是否准确
- 完整性（30分）：是否覆盖了要点
- 表达（20分）：表达是否清晰
- 深度（10分）：是否有深入思考

请给出总分（1-100）和每个维度的得分，以及改进建议。
注意：你只负责评分，不要教学。"""
        msg = [
            SystemMessage(content=system),
            HumanMessage(content=f"请对以下回答评分：\n{state.user_input}")
        ]
        full = ""
        async for chunk in llm.astream(msg):
            t = chunk.content if hasattr(chunk, 'content') else str(chunk)
            if t:
                full += t
                if state.sse_queue:
                    await state.sse_queue.put({"event": "token", "data": {"token": t}})
        state.ai_output = full
        if state.sse_queue:
            await state.sse_queue.put({"event": "done", "data": {"full_text": full}})
        return state

    graph.add_node("grade", grade_node)
    graph.set_entry_point("grade")
    graph.add_edge("grade", END)
    return graph.compile()


def create_recommender_graph():
    """推荐Agent - 独立职责，只推荐不教学"""
    from app.langgraph.state import MultiAgentState
    from langchain_core.messages import HumanMessage, SystemMessage

    graph = StateGraph(MultiAgentState)

    async def recommend_node(state: MultiAgentState) -> MultiAgentState:
        llm = _get_llm()
        system = """你是AI虚拟课堂的学习资源推荐专家。

根据学生的学习情况和当前进度，推荐：
1. 配套学习资源（书籍、视频、文章）
2. 练习项目建议
3. 下一步学习方向

注意：你只负责推荐，不要教学。"""
        msg = [
            SystemMessage(content=system),
            HumanMessage(content=f"请根据以下情况推荐学习资源：\n{state.user_input}")
        ]
        full = ""
        async for chunk in llm.astream(msg):
            t = chunk.content if hasattr(chunk, 'content') else str(chunk)
            if t:
                full += t
                if state.sse_queue:
                    await state.sse_queue.put({"event": "token", "data": {"token": t}})
        state.ai_output = full
        if state.sse_queue:
            await state.sse_queue.put({"event": "done", "data": {"full_text": full}})
        return state

    graph.add_node("recommend", recommend_node)
    graph.set_entry_point("recommend")
    graph.add_edge("recommend", END)
    return graph.compile()


def setup_agents():
    """初始化所有Agent并注册到Orchestrator"""
    logger.info("🚀 开始初始化多智能体系统 V2..." +
                 (" LangGraph模式" if _HAS_LANGGRAPH else " 占位模式"))

    try:
        # ═══════════ 大纲智能体 V3 ═══════════
        # V3 不再使用 LangGraph 图，改为直接调用 run_outline_workflow()
        # 这里注册一个简单的占位图（保持 orchestrator 兼容性）
        from app.langgraph.state import MultiAgentState
        placeholder_graph = StateGraph(MultiAgentState)
        async def _placeholder_node(state: MultiAgentState) -> MultiAgentState:
            return state
        placeholder_graph.add_node("placeholder", _placeholder_node)
        placeholder_graph.set_entry_point("placeholder")
        placeholder_graph.add_edge("placeholder", END)
        orchestrator.register_agent(
            AgentType.OUTLINE,
            placeholder_graph.compile(),
            "大纲生成Agent V3：简洁三步流程（问知识→选程度→问时间→生成大纲），支持选项点击",
            ["大纲生成", "课程规划", "学习路径设计", "需求分析"]
        )
        logger.info("📝 Outline Agent V3 registered")

        # ═══════════ 教师智能体 V2 ═══════════
        from app.langgraph.tutor_agent import create_tutor_graph_v2
        orchestrator.register_agent(
            AgentType.TUTOR,
            create_tutor_graph_v2(),
            "教师Agent V2：严格基于大纲模块教学+进度跟踪+向量检索历史",
            ["问答教学", "概念解释", "代码示例", "模块教学", "进度管理"]
        )
        logger.info("👨‍🏫 Tutor Agent V2 registered")

        # ═══════════ 评分Agent ═══════════
        orchestrator.register_agent(
            AgentType.GRADER,
            create_grader_graph(),
            "评分Agent：对学生回答进行多维度评分（正确性/完整性/表达/深度）",
            ["作业评分", "答案批改", "反馈生成"]
        )
        logger.info("📊 Grader Agent registered")

        # ═══════════ 推荐Agent ═══════════
        orchestrator.register_agent(
            AgentType.RECOMMENDER,
            create_recommender_graph(),
            "推荐Agent：根据学习进度推荐配套资源和练习项目",
            ["资源推荐", "学习路径规划", "练习建议"]
        )
        logger.info("🔍 Recommender Agent registered")

        logger.info(f"✅ 多智能体系统 V2 初始化完成 — 已注册 {len(orchestrator.list_agents())} Agent")

    except Exception as e:
        logger.error(f"❌ 多智能体系统初始化失败: {e}")
        raise
