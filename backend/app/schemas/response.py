"""
统一响应格式
"""
from typing import TypeVar, Generic, Optional
from pydantic import BaseModel

T = TypeVar("T")

class APIResponse(BaseModel, Generic[T]):
    """统一API响应格式"""
    success: bool = True
    message: str = "success"
    data: Optional[T] = None

class PaginatedData(BaseModel, Generic[T]):
    """分页数据"""
    items: list[T] = []
    total: int = 0
    page: int = 1
    page_size: int = 20
