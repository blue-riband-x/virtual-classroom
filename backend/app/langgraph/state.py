"""
多智能体共享状态定义
所有Agent通过此状态进行通信和数据共享
"""
from typing import List, Optional, Dict, Any
try:
    from langchain_core.messages import BaseMessage
except ImportError:
    BaseMessage = dict  # fallback
from pydantic import BaseModel, Field


class AgentMessage(BaseModel):
    """
    Agent间传递的消息
    
    用于Agent之间的通信，支持：
    - 请求（request）：Agent A请求Agent B处理
    - 响应（response）：Agent B返回结果给Agent A
    - 交接（handoff）：Agent A无法处理，转交给Agent B
    """
    from_agent: str = Field(..., description="发送方Agent名称")
    to_agent: str = Field(..., description="接收方Agent名称")
    message_type: str = Field(..., description="消息类型: request/response/handoff")
    content: str = Field(..., description="消息内容")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")
    timestamp: Optional[float] = Field(default=None, description="消息时间戳")


class MultiAgentState(BaseModel):
    """
    多智能体共享状态
    
    此状态在LangGraph的多个Agent之间传递和共享。
    每个Agent可以读取和修改这个状态。
    """
    
    # ========== 基础字段 ==========
    # 用户ID
    user_id: int = Field(..., description="用户ID")
    
    # 当前活跃Agent
    current_agent: str = Field(..., description="当前正在处理任务的Agent类型")
    
    # ========== 消息历史 ==========
    # LangChain消息历史（所有Agent共享）
    messages: List[BaseMessage] = Field(
        default_factory=list,
        description="对话消息历史"
    )
    
    # ========== 用户输入 ==========
    user_input: str = Field(..., description="用户输入")
    user_input_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="用户输入的额外元数据"
    )
    
    # ========== Agent间通信 ==========
    # Agent间消息队列
    agent_messages: List[AgentMessage] = Field(
        default_factory=list,
        description="Agent间传递的消息队列"
    )
    
    # 各Agent的输出（key: agent_type, value: output）
    agent_outputs: Dict[str, Any] = Field(
        default_factory=dict,
        description="各Agent的输出结果"
    )
    
    # ========== 上下文 ==========
    # Chroma检索的上下文（向量数据库）
    chroma_context: Optional[str] = Field(
        default=None,
        description="从Chroma检索的相关历史对话"
    )
    
    # 教师风格（humorous / rigorous / default）
    teacher_style: Optional[str] = Field(
        default=None,
        description="教师风格: humorous(幽默) / rigorous(严谨) / default(默认)"
    )
    
    # 其他上下文（非向量数据，如用户资料、学习计划等）
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="其他上下文信息"
    )
    
    # ========== AI输出 ==========
    # 当前Agent的AI输出
    ai_output: Optional[str] = Field(
        default=None,
        description="当前AI输出（最终返回给用户的内容）"
    )
    
    # 中间步骤（用于调试和前端展示）
    intermediate_steps: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="中间处理步骤"
    )
    
    # ========== SSE相关 ==========
    # SSE事件队列（用于流式输出到前端）
    sse_queue: Optional[Any] = Field(
        default=None,
        description="SSE事件队列（asyncio.Queue）"
    )
    
    session_id: Optional[str] = Field(
        default=None,
        description="SSE会话ID"
    )
    
    # ========== 错误状态 ==========
    error: Optional[str] = Field(
        default=None,
        description="错误信息"
    )
    
    warning: Optional[str] = Field(
        default=None,
        description="警告信息（非致命错误）"
    )
    
    # ========== 配置 ==========
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="额外配置参数"
    )
    
    class Config:
        """Pydantic配置"""
        arbitrary_types_allowed = True  # 允许LangChain等外部类型
    
    def add_agent_message(
        self,
        from_agent: str,
        to_agent: str,
        msg_type: str,
        content: str,
        metadata: Optional[Dict] = None
    ):
        """添加Agent间消息"""
        msg = AgentMessage(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=msg_type,
            content=content,
            metadata=metadata or {},
            timestamp=None  # TODO: 添加时间戳
        )
        self.agent_messages.append(msg)
    
    def get_agent_output(self, agent_type: str) -> Optional[Any]:
        """获取指定Agent的输出"""
        return self.agent_outputs.get(agent_type)
    
    def set_agent_output(self, agent_type: str, output: Any):
        """设置指定Agent的输出"""
        self.agent_outputs[agent_type] = output
    
    def add_intermediate_step(self, step: Dict[str, Any]):
        """添加中间步骤"""
        self.intermediate_steps.append(step)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为可序列化的字典（用于日志、调试）"""
        return {
            "user_id": self.user_id,
            "current_agent": self.current_agent,
            "user_input": self.user_input,
            "messages_count": len(self.messages),
            "agent_messages_count": len(self.agent_messages),
            "agent_outputs_keys": list(self.agent_outputs.keys()),
            "has_chroma_context": self.chroma_context is not None,
            "has_context": self.context is not None,
            "has_ai_output": self.ai_output is not None,
            "intermediate_steps_count": len(self.intermediate_steps),
            "has_sse_queue": self.sse_queue is not None,
            "session_id": self.session_id,
            "error": self.error,
            "warning": self.warning,
        }
