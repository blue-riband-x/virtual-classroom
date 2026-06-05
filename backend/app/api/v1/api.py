"""
API v1 路由聚合
"""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, ai, outline

api_router = APIRouter()

# 注册所有端点
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(ai.router)
api_router.include_router(outline.router)
