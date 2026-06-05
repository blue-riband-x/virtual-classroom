"""
API v1 路由聚合 - Python 后端只保留 AI 相关业务
传统 CRUD（认证/用户/大纲管理/排行榜）已迁移到 Java Spring Boot
"""
from fastapi import APIRouter
from app.api.v1.endpoints import ai, outline

api_router = APIRouter()

# AI 核心（教学/评分/推荐）
api_router.include_router(ai.router)

# 大纲 AI 生成（generate/stream/pdf-generate）
api_router.include_router(outline.router)
