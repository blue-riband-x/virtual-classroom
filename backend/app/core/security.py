"""安全工具：JWT Token、简化的用户认证"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings

security = HTTPBearer(auto_error=False)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建JWT access token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def verify_token(token: str) -> Optional[dict]:
    """验证JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """
    获取当前用户（依赖注入）
    
    简化版：开发环境下不强制认证。
    生产环境应改为强制认证。
    """
    if settings.DEBUG:
        # 开发模式：尝试解析 token，失败也返回模拟用户
        if credentials is not None:
            payload = verify_token(credentials.credentials)
            if payload:
                return {
                    "id": payload.get("user_id", 0),
                    "username": payload.get("username", "unknown"),
                    "nickname": payload.get("nickname", "用户"),
                    "is_active": True
                }
        return {
            "id": 1,
            "username": "dev_user",
            "nickname": "开发者",
            "is_active": True
        }
    
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证凭据"
        )
    
    payload = verify_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据"
        )
    
    return {
        "id": payload.get("user_id", 0),
        "username": payload.get("username", "unknown"),
        "nickname": payload.get("nickname", "用户"),
        "is_active": True
    }
