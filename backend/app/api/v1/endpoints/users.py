"""
用户相关端点：游戏化数据、学习记录、成就
"""
from fastapi import APIRouter, Depends
from app.core.security import get_current_user
from app.schemas.response import APIResponse

router = APIRouter(prefix="/users", tags=["用户与游戏化"])

# 模拟游戏化数据
MOCK_DATA = {
    "user_info": {
        "id": 1, "username": "dev", "nickname": "学习小达人",
        "avatar_url": None, "level": 15, "xp": 2850, "xpToNextLevel": 3000,
        "streak": 7, "totalLearningHours": 42.5
    },
    "learning_history": [
        {"id": 1, "topic": "Python基础语法", "date": "2026-05-10", "duration": 45, "score": 92, "xp": 68},
        {"id": 2, "topic": "数据结构-二叉树", "date": "2026-05-09", "duration": 60, "score": 85, "xp": 72},
        {"id": 3, "topic": "算法复杂度分析", "date": "2026-05-08", "duration": 40, "score": 78, "xp": 48},
    ],
    "achievements": [
        {"id": "ach_001", "name": "首课完成", "icon": "🎯", "desc": "完成第一节课", "tier": "bronze", "unlocked": True, "progress": 100},
        {"id": "ach_002", "name": "百课达成", "icon": "💯", "desc": "完成100节课", "tier": "gold", "unlocked": False, "progress": 32},
        {"id": "ach_003", "name": "提问达人", "icon": "❓", "desc": "累计提问50次", "tier": "silver", "unlocked": True, "progress": 100},
    ],
}

@router.get("/profile", response_model=APIResponse)
async def get_profile(current_user: dict = Depends(get_current_user)):
    """获取用户资料（游戏化数据）"""
    return APIResponse(success=True, data=MOCK_DATA["user_info"])

@router.get("/history", response_model=APIResponse)
async def get_history(current_user: dict = Depends(get_current_user)):
    """获取学习历史"""
    return APIResponse(success=True, data=MOCK_DATA["learning_history"])

@router.get("/achievements", response_model=APIResponse)
async def get_achievements(current_user: dict = Depends(get_current_user)):
    """获取成就列表"""
    return APIResponse(success=True, data=MOCK_DATA["achievements"])
