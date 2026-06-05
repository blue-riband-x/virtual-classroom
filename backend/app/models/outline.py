"""大纲规划模型"""
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.base import BaseModel
from datetime import datetime, timezone


class Outline(BaseModel):
    """学习大纲表"""
    __tablename__ = "outlines"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    title = Column(String(200), nullable=False, comment="大纲标题")
    topic = Column(String(100), nullable=False, comment="学习主题")
    subject = Column(String(50), default="", comment="学科分类")
    level = Column(String(20), default="beginner", comment="难度: beginner/intermediate/advanced")
    total_duration = Column(Integer, default=0, comment="总时长(分钟)")
    module_count = Column(Integer, default=0, comment="模块数量")
    modules_data = Column(JSON, nullable=True, comment="模块详情(JSON数组)")
    ai_generated = Column(Boolean, default=True, comment="是否AI生成")
    status = Column(String(20), default="active", comment="状态: active/archived")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), comment="创建时间")
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), comment="更新时间")

    user = relationship("User", back_populates="outlines")
    teaching_sessions = relationship("TeachingSession", back_populates="outline", cascade="all, delete-orphan")
    module_contents = relationship("ModuleContent", back_populates="outline", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Outline {self.title}>"
