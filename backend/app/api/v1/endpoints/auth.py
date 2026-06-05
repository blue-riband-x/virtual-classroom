"""
认证端点：登录、注册、Token刷新
"""
from fastapi import APIRouter, Depends, HTTPException
from app.core.security import create_access_token, get_current_user
from app.core.config import settings
from app.schemas.response import APIResponse
from app.schemas.user import UserLogin, UserCreate

router = APIRouter(prefix="/auth", tags=["认证"])

# 开发环境模拟用户
MOCK_USERS = {
    "dev": {"id": 1, "username": "dev", "password": "123456", "nickname": "开发者"},
    "student": {"id": 2, "username": "student", "password": "123456", "nickname": "小明"},
}

@router.post("/login", response_model=APIResponse)
async def login(data: UserLogin):
    """用户登录 - 简化版（开发用）"""
    
    user = MOCK_USERS.get(data.username)
    if not user or user["password"] != data.password:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    token = create_access_token({
        "user_id": user["id"],
        "username": user["username"],
        "nickname": user["nickname"]
    })
    
    return APIResponse(
        success=True,
        message="登录成功",
        data={
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "nickname": user["nickname"]
            }
        }
    )

@router.post("/register", response_model=APIResponse)
async def register(data: UserCreate):
    """用户注册"""
    return APIResponse(
        success=True,
        message="注册成功",
        data={"id": 3, "username": data.username, "nickname": data.nickname}
    )

@router.get("/me", response_model=APIResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """获取当前用户信息"""
    return APIResponse(success=True, data=current_user)
