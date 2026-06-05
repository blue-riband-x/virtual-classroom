"""
用户模型
支持游戏化系统的用户信息
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import BaseModel


class User(BaseModel):
    """用户表"""
    
    __tablename__ = "users"
    
    # 基本信息
    username = Column(String(50), unique=True, index=True, nullable=False, comment="用户名")
    email = Column(String(100), unique=True, index=True, nullable=False, comment="邮箱")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    nickname = Column(String(50), nullable=False, comment="昵称")
    avatar_url = Column(String(255), nullable=True, comment="头像URL")
    
    # 游戏化字段
    xp = Column(Integer, default=0, nullable=False, comment="经验值")
    level = Column(Integer, default=1, nullable=False, comment="等级")
    streak = Column(Integer, default=0, nullable=False, comment="连续学习天数")
    total_learning_hours = Column(Float, default=0.0, nullable=False, comment="总学习时长(小时)")
    xp_to_next_level = Column(Integer, default=100, nullable=False, comment="下一级所需XP")
    
    # 状态字段
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_superuser = Column(Boolean, default=False, comment="是否超级用户")
    last_login = Column(DateTime, nullable=True, comment="最后登录时间")
    last_streak_date = Column(DateTime, nullable=True, comment="最后连续学习日期")
    
    # 3D形象配置
    avatar_3d_config = Column(JSON, nullable=True, comment="3D虚拟形象配置")
    
    # 关系
    learning_plans = relationship("LearningPlan", back_populates="user", cascade="all, delete-orphan")
    learning_records = relationship("LearningRecord", back_populates="user", cascade="all, delete-orphan")
    achievements = relationship("UserAchievement", back_populates="user", cascade="all, delete-orphan")
    scores = relationship("Leaderboard", back_populates="user", cascade="all, delete-orphan")
    outlines = relationship("Outline", back_populates="user", cascade="all, delete-orphan")
    outline_conversations = relationship("OutlineConversation", back_populates="user", cascade="all, delete-orphan")
    teaching_sessions = relationship("TeachingSession", back_populates="user", cascade="all, delete-orphan")
    module_contents = relationship("ModuleContent", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.username}>"
    

class LearningPlan(BaseModel):
    """学习计划表"""
    
    __tablename__ = "learning_plans"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    title = Column(String(200), nullable=False, comment="计划标题")
    description = Column(Text, nullable=True, comment="计划描述")
    topic = Column(String(100), nullable=False, comment="学习主题")
    difficulty = Column(String(20), nullable=False, comment="难度: easy/medium/hard")
    total_hours = Column(Float, default=0.0, comment="总学习时长")
    completed_hours = Column(Float, default=0.0, comment="已完成时长")
    progress = Column(Float, default=0.0, comment="完成进度(0-100)")
    status = Column(String(20), default="pending", comment="状态: pending/active/completed")
    start_date = Column(DateTime, nullable=True, comment="开始日期")
    end_date = Column(DateTime, nullable=True, comment="结束日期")
    ai_generated = Column(Boolean, default=False, comment="是否AI生成")
    config = Column(JSON, nullable=True, comment="额外配置")
    
    # 关系
    user = relationship("User", back_populates="learning_plans")
    records = relationship("LearningRecord", back_populates="plan", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<LearningPlan {self.title}>"
    

class LearningRecord(BaseModel):
    """学习记录表"""
    
    __tablename__ = "learning_records"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    plan_id = Column(Integer, ForeignKey("learning_plans.id"), nullable=True, comment="计划ID")
    topic = Column(String(100), nullable=False, comment="学习主题")
    duration = Column(Integer, nullable=False, comment="学习时长(分钟)")
    score = Column(Float, nullable=True, comment="得分")
    xp_earned = Column(Integer, default=0, comment="获得XP")
    date = Column(DateTime, default=func.now(), comment="学习日期")
    note = Column(Text, nullable=True, comment="学习笔记")
    config = Column(JSON, nullable=True, comment="额外配置")
    
    # 关系
    user = relationship("User", back_populates="learning_records")
    plan = relationship("LearningPlan", back_populates="records")
    
    def __repr__(self):
        return f"<LearningRecord {self.topic}>"
    

class Achievement(BaseModel):
    """成就表"""
    
    __tablename__ = "achievements"
    
    name = Column(String(100), nullable=False, comment="成就名称")
    description = Column(Text, nullable=True, comment="成就描述")
    icon = Column(String(10), nullable=True, comment="成就图标")
    xp_reward = Column(Integer, default=0, comment="XP奖励")
    condition = Column(JSON, default=dict, nullable=False, comment="解锁条件")
    is_active = Column(Boolean, default=True, comment="是否激活")
    
    def __repr__(self):
        return f"<Achievement {self.name}>"
    

class UserAchievement(BaseModel):
    """用户成就关联表"""
    
    __tablename__ = "user_achievements"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False, comment="成就ID")
    unlocked_at = Column(DateTime, default=func.now(), comment="解锁时间")
    
    # 关系
    user = relationship("User", back_populates="achievements")
    achievement = relationship("Achievement")
    
    def __repr__(self):
        return f"<UserAchievement user_id={self.user_id} achievement_id={self.achievement_id}>"
    

class Leaderboard(BaseModel):
    """排行榜表"""
    
    __tablename__ = "leaderboard"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    week = Column(String(10), nullable=False, comment="周标识: 2024-W01")
    month = Column(String(7), nullable=False, comment="月标识: 2024-01")
    xp_earned = Column(Integer, default=0, comment="获得XP")
    study_time = Column(Float, default=0.0, comment="学习时长(小时)")
    rank_week = Column(Integer, nullable=True, comment="周排名")
    rank_month = Column(Integer, nullable=True, comment="月排名")
    
    # 关系
    user = relationship("User", back_populates="scores")
    
    def __repr__(self):
        return f"<Leaderboard user_id={self.user_id} week={self.week}>"
    

class Classroom(BaseModel):
    """课堂表"""
    
    __tablename__ = "classrooms"
    
    name = Column(String(200), nullable=False, comment="课堂名称")
    description = Column(Text, nullable=True, comment="课堂描述")
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="讲师ID")
    max_students = Column(Integer, default=30, comment="最大学生数")
    current_students = Column(Integer, default=0, comment="当前学生数")
    status = Column(String(20), default="active", comment="状态: active/ended")
    start_time = Column(DateTime, nullable=True, comment="开始时间")
    end_time = Column(DateTime, nullable=True, comment="结束时间")
    config = Column(JSON, nullable=True, comment="课堂配置")
    
    def __repr__(self):
        return f"<Classroom {self.name}>"
    