"""
多智能体协调器（Orchestrator）
负责Agent注册、路由、协调多个Agent的工作
"""
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    """Agent类型枚举"""
    TUTOR = "tutor"               # AI导师
    GRADER = "grader"             # 评分Agent
    RECOMMENDER = "recommender"   # 推荐Agent
    OUTLINE = "outline"           # 大纲生成Agent
    POLISH = "polish"             # 润色Agent
    CODE_REVIEW = "code_review"   # 代码审查Agent


class AgentInfo(BaseModel):
    """Agent信息"""
    agent_type: AgentType
    graph: Any  # CompiledGraph
    description: str
    capabilities: List[str] = Field(default_factory=list)
    is_active: bool = True


class AgentOrchestrator:
    """
    多智能体协调器（单例模式）
    
    功能：
    1. Agent注册与发现
    2. 任务路由（选择最合适的Agent）
    3. 多Agent流水线执行
    4. Agent间通信管理
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Agent注册表: AgentType -> AgentInfo
        self.agents: Dict[AgentType, AgentInfo] = {}
        
        # 路由规则: 关键词 -> AgentType
        self.routing_rules: Dict[str, AgentType] = {
            "评分": AgentType.GRADER,
            "打分": AgentType.GRADER,
            "批改": AgentType.GRADER,
            "推荐": AgentType.RECOMMENDER,
            "建议": AgentType.RECOMMENDER,
            "大纲": AgentType.OUTLINE,
            "目录": AgentType.OUTLINE,
            "润色": AgentType.POLISH,
            "优化": AgentType.POLISH,
            "代码": AgentType.CODE_REVIEW,
            "编程": AgentType.CODE_REVIEW,
        }
        
        self._initialized = True
        logger.info("✅ AgentOrchestrator initialized")
    
    def register_agent(
        self,
        agent_type: AgentType,
        graph: Any,
        description: str,
        capabilities: List[str] = None
    ):
        """
        注册Agent
        
        Args:
            agent_type: Agent类型
            graph: 编译好的LangGraph图
            description: Agent功能描述
            capabilities: Agent能力列表
        """
        self.agents[agent_type] = AgentInfo(
            agent_type=agent_type,
            graph=graph,
            description=description,
            capabilities=capabilities or []
        )
        logger.info(f"📝 Registered agent: {agent_type} - {description}")
    
    async def route_to_agent(
        self,
        user_input: str,
        context: Optional[Dict] = None
    ) -> AgentType:
        """
        路由到合适的Agent
        
        路由策略（优先级从高到低）：
        1. 显式指定（context中包含agent_type）
        2. 关键词匹配（routing_rules）
        3. LLM分类（可选，如果启用）
        4. 默认Agent（Tutor）
        
        Args:
            user_input: 用户输入
            context: 上下文（可包含指定agent_type）
        
        Returns:
            最合适的AgentType
        """
        # 策略1：显式指定
        if context and "agent_type" in context:
            specified = context["agent_type"]
            if specified in self.agents:
                logger.info(f"🎯 Routing by explicit spec: {specified}")
                return specified
        
        # 策略2：关键词匹配
        for keyword, agent_type in self.routing_rules.items():
            if keyword in user_input:
                logger.info(f"🎯 Routing by keyword '{keyword}': {agent_type}")
                return agent_type
        
        # 策略3：LLM分类（可选，这里用简单启发式）
        # TODO: 可以调用LLM进行意图分类
        
        # 策略4：默认Agent
        logger.info(f"🎯 Routing to default: {AgentType.TUTOR}")
        return AgentType.TUTOR
    
    async def run_agent(
        self,
        agent_type: AgentType,
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        运行指定Agent
        
        Args:
            agent_type: Agent类型
            state: 输入状态（dict 或 MultiAgentState）
        
        Returns:
            输出状态（dict）
        """
        if agent_type not in self.agents:
            raise ValueError(f"Agent {agent_type} not registered")
        
        if not self.agents[agent_type].is_active:
            raise ValueError(f"Agent {agent_type} is inactive")
        
        graph = self.agents[agent_type].graph
        
        logger.info(f"🚀 Running agent: {agent_type}")
        
        # 如果传入的是 Pydantic model，转成 dict
        if hasattr(state, 'model_dump'):
            state_dict = state.model_dump()
        elif hasattr(state, 'dict'):
            state_dict = state.dict()
        else:
            state_dict = state
        
        # 确保 sse_queue 是原始对象（不是序列化后的值）
        # LangGraph ainvoke 支持 dict 输入，内部会做类型转换
        
        try:
            result = await graph.ainvoke(state_dict)
        except Exception as e:
            logger.error(f"❌ Agent {agent_type} failed: {e}", exc_info=True)
            raise
        
        logger.info(f"✅ Agent {agent_type} completed")
        return result
    
    async def run_pipeline(
        self,
        agent_sequence: List[AgentType],
        initial_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        按顺序运行多个Agent（流水线模式）
        
        示例场景：
        1. 大纲生成 → 内容润色 → 推荐相关资料
        2. 代码生成 → 代码审查 → 代码优化
        
        Args:
            agent_sequence: Agent执行顺序
            initial_state: 初始状态
        
        Returns:
            最终状态（包含所有Agent的输出）
        """
        state = initial_state.copy()
        
        for i, agent_type in enumerate(agent_sequence):
            logger.info(f"🔄 Pipeline step {i+1}/{len(agent_sequence)}: {agent_type}")
            
            # 运行当前Agent
            result = await self.run_agent(agent_type, state)
            
            # 将当前Agent的输出合并到state
            state.update(result)
            
            # 添加Agent间消息
            if "agent_messages" not in state:
                state["agent_messages"] = []
            
            state["agent_messages"].append({
                "from_agent": agent_type,
                "to_agent": agent_sequence[i+1] if i+1 < len(agent_sequence) else None,
                "message_type": "handoff",
                "content": f"Step {i+1} completed",
                "metadata": {"output": result}
            })
        
        logger.info(f"✅ Pipeline completed: {' → '.join(agent_sequence)}")
        return state
    
    async def handoff(
        self,
        from_agent: AgentType,
        to_agent: AgentType,
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Agent间交接（Handoff）
        
        场景：Agent A发现自己无法处理，移交给Agent B
        
        Args:
            from_agent: 当前Agent
            to_agent: 目标Agent
            state: 当前状态
        
        Returns:
            目标Agent的输出
        """
        logger.info(f"🤝 Handoff: {from_agent} → {to_agent}")
        
        # 添加handoff消息
        if "agent_messages" not in state:
            state["agent_messages"] = []
        
        state["agent_messages"].append({
            "from_agent": from_agent,
            "to_agent": to_agent,
            "message_type": "handoff",
            "content": f"Handoff from {from_agent} to {to_agent}",
            "metadata": {}
        })
        
        # 更新当前Agent
        state["current_agent"] = to_agent
        
        # 运行目标Agent
        result = await self.run_agent(to_agent, state)
        return result
    
    def get_agent_info(self, agent_type: AgentType) -> Optional[AgentInfo]:
        """获取Agent信息"""
        return self.agents.get(agent_type)
    
    def list_agents(self) -> List[AgentInfo]:
        """列出所有已注册的Agent"""
        return list(self.agents.values())
    
    def deactivate_agent(self, agent_type: AgentType):
        """停用Agent"""
        if agent_type in self.agents:
            self.agents[agent_type].is_active = False
            logger.info(f"⏸️  Deactivated agent: {agent_type}")
    
    def activate_agent(self, agent_type: AgentType):
        """激活Agent"""
        if agent_type in self.agents:
            self.agents[agent_type].is_active = True
            logger.info(f"▶️  Activated agent: {agent_type}")


# 全局协调器实例
orchestrator = AgentOrchestrator()
