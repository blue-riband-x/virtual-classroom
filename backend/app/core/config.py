"""
应用配置管理
使用Pydantic Settings管理环境变量和配置
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置类"""
    
    # ========== 项目信息 ==========
    PROJECT_NAME: str = "Virtual Classroom API"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    
    # ========== 服务器配置 ==========
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # ========== 安全配置 ==========
    SECRET_KEY: str = "virtual-classroom-jwt-secret-key-2024"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # ========== 数据库配置 ==========
    DATABASE_URL: str = "mysql+aiomysql://root:root@localhost:3306/virtual_classroom"
    
    # ========== 向量数据库配置 ==========
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_db"
    EMBEDDING_MODEL: str = "text-embedding-v4"  # 阿里百炼embedding模型
    
    # ========== CORS配置 ==========
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:5173",  # Vite默认端口
        "http://localhost:8080",
        "http://localhost:8081",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8081",
    ]
    
    # ========== 信任主机 ==========
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # ========== 文件上传配置 ==========
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/gif"]
    
    # ========== 阿里百炼（DashScope）配置 ========== ⭐ 新增
    DASHSCOPE_API_KEY: Optional[str] = None
    DASHSCOPE_BASE_URL: str = "https://dashscope.aliyuncs.com/api/v1"
    # 向量模型（用于Chroma embedding）
    DASHSCOPE_EMBEDDING_MODEL: str = "text-embedding-v4"
    
    # ========== DeepSeek配置 ========== ⭐ 新增
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    # DeepSeek模型选择
    DEEPSEEK_MODEL: str = "deepseek-chat"  # 或 "deepseek-coder"
    
    # ========== 豆包（火山方舟）文生图配置 ==========
    ARK_API_KEY: Optional[str] = None
    ARK_BASE_URL: str = "https://ark.cn-beijing.volces.com/api/v3"
    ARK_IMAGE_MODEL: str = "doubao-seedream-5-0-260128"  # 豆包文生图模型
    
    # ========== 游戏化配置 ==========
    XP_PER_MINUTE: int = 10
    XP_PER_CORRECT_ANSWER: int = 50
    STREAK_BONUS_MULTIPLIER: float = 1.5
    LEVEL_BASE_XP: int = 100
    LEVEL_XP_MULTIPLIER: float = 1.5
    
    # ========== SSE/WebSocket配置 ==========
    WS_HEARTBEAT_INTERVAL: int = 30  # 秒
    WS_MAX_CONNECTIONS_PER_USER: int = 3
    
    # ========== 日志配置 ==========
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # 允许 .env 中有未定义的额外字段
    
    @property
    def async_database_url(self) -> str:
        """获取异步数据库URL"""
        return self.DATABASE_URL
    
    def get_token_expire_minutes(self) -> int:
        """获取token过期分钟数"""
        return self.ACCESS_TOKEN_EXPIRE_MINUTES
    
    def calculate_level_xp(self, level: int) -> int:
        """计算指定等级所需的XP"""
        return int(self.LEVEL_BASE_XP * (self.LEVEL_XP_MULTIPLIER ** (level - 1)))
    
    def get_dashscope_headers(self) -> dict:
        """获取阿里百炼请求头"""
        if not self.DASHSCOPE_API_KEY:
            raise ValueError("DASHSCOPE_API_KEY not configured")
        return {
            "Authorization": f"Bearer {self.DASHSCOPE_API_KEY}",
            "Content-Type": "application/json"
        }
    
    def get_deepseek_headers(self) -> dict:
        """获取DeepSeek请求头"""
        if not self.DEEPSEEK_API_KEY:
            raise ValueError("DEEPSEEK_API_KEY not configured")
        return {
            "Authorization": f"Bearer {self.DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }


@lru_cache()
def get_settings() -> Settings:
    """
    获取配置单例
    使用lru_cache确保配置只加载一次
    """
    return Settings()


settings = get_settings()
