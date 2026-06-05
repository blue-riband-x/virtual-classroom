"""
用户相关的Pydantic Schema
用于请求/响应验证
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


# ============ 基础Schema ============
class UserBase(BaseModel):
    """用户基础Schema"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    nickname: str = Field(..., min_length=1, max_length=50, description="昵称")
    avatar_url: Optional[str] = Field(None, description="头像URL")


# ============ 创建用户 ============
class UserCreate(UserBase):
    """创建用户请求"""
    password: str = Field(..., min_length=6, max_length=50, description="密码")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "student001",
                "email": "student@example.com",
                "password": "password123",
                "nickname": "小明"
            }
        }


# ============ 用户登录 ============
class UserLogin(BaseModel):
    """用户登录请求"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


# ============ Token响应 ============
class Token(BaseModel):
    """Token响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token数据"""
    username: Optional[str] = None
    user_id: Optional[int] = None


# ============ 用户更新 ============
class UserUpdate(BaseModel):
    """更新用户请求"""
    nickname: Optional[str] = Field(None, min_length=1, max_length=50)
    avatar_url: Optional[str] = None
    email: Optional[EmailStr] = None


# ============ 密码更新 ============
class PasswordUpdate(BaseModel):
    """更新密码请求"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=50, description="新密码")


# ============ 用户响应 ============
class UserResponse(UserBase):
    """用户响应"""
    id: int
    xp: int
    level: int
    streak: int
    total_learning_hours: float
    xp_to_next_level: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    avatar_3d_config: Optional[dict] = None
    
    class Config:
        from_attributes = True


# ============ 用户详情（包含token） ============
class UserWithToken(BaseModel):
    """用户详情（包含token）"""
    user: UserResponse
    token: Token


# ============ 用户游戏化信息 ============
class UserGameInfo(BaseModel):
    """用户游戏化信息"""
    id: int
    username: str
    nickname: str
    avatar_url: Optional[str]
    xp: int
    level: int
    streak: int
    total_learning_hours: float
    xp_to_next_level: int
    
    class Config:
        from_attributes = True


# ============ 用户列表响应 ============
class UserListResponse(BaseModel):
    """用户列表响应"""
    total: int
    users: List[UserResponse]
