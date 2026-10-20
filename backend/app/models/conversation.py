"""
对话上下文模型
用于存储大纲生成过程中的对话轮次，实现智能体记忆
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.base import BaseModel
from datetime import datetime, timezone


class OutlineConversation(BaseModel):
    """大纲生成对话上下文 - 记录每一轮问答"""
    __tablename__ = "outline_conversations"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    session_id = Column(String(100), nullable=False, index=True, comment="会话ID")
    round_num = Column(Integer, default=1, comment="对话轮次")
    role = Column(String(20), nullable=False, comment="角色: user / assistant")
    content = Column(Text, nullable=False, comment="消息内容")
    # 收集到的用户信息 (JSON)
    collected_info = Column(JSON, nullable=True, comment="本轮收集到的用户信息")
    # 已问过的问题列表 (JSON数组)
    asked_questions = Column(JSON, nullable=True, comment="本轮已问过的问题")
    # 时间戳
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), comment="创建时间")

    user = relationship("User", back_populates="outline_conversations")

    def __repr__(self):
        return f"<OutlineConversation round={self.round_num} role={self.role}>"


class TeachingSession(BaseModel):
    """教师教学会话 - 记录教学过程中的对话"""
    __tablename__ = "teaching_sessions"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    outline_id = Column(Integer, ForeignKey("outlines.id"), nullable=False, comment="关联的大纲ID")
    session_id = Column(String(100), nullable=False, index=True, comment="会话ID")
    current_module = Column(Integer, default=1, comment="当前教学模块序号")
    module_progress = Column(Integer, default=0, comment="当前模块进度(0-100)")
    total_modules = Column(Integer, default=0, comment="总模块数")
    completed_modules = Column(JSON, nullable=True, comment="已完成的模块序号列表")
    status = Column(String(20), default="active", comment="状态: active / paused / completed")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), comment="创建时间")
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), comment="更新时间")

    user = relationship("User", back_populates="teaching_sessions")
    outline = relationship("Outline", back_populates="teaching_sessions")

    def __repr__(self):
        return f"<TeachingSession outline={self.outline_id} module={self.current_module}>"


class ModuleContent(BaseModel):
    """AI预生成的模块教学内容"""
    __tablename__ = "module_contents"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    outline_id = Column(Integer, ForeignKey("outlines.id"), nullable=False, comment="关联的大纲ID")
    module_index = Column(Integer, nullable=False, comment="模块序号(1-based)")
    module_name = Column(String(200), nullable=False, comment="模块名称")
    content = Column(Text, nullable=True, comment="AI生成的完整教学内容(Markdown)")
    teacher_style = Column(String(50), default="default", comment="教师风格")
    board_data = Column(JSON, nullable=True, comment="板书智能体生成的板书序列数据")
    status = Column(String(20), default="pending", comment="状态: pending/generating/completed/failed")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), comment="创建时间")
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), comment="更新时间")

    user = relationship("User", back_populates="module_contents")
    outline = relationship("Outline", back_populates="module_contents")

    def __repr__(self):
        return f"<ModuleContent outline={self.outline_id} module={self.module_index}>"
