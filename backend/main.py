"""
AI虚拟课堂 - FastAPI主应用（多智能体架构）
Virtual Classroom Backend with Multi-Agent System
"""
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.db.base import Base
from app.api.v1.api import api_router
from app.langgraph import setup
from app.models import user, outline, conversation  # 确保所有模型被 SQLAlchemy 发现

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    startup: 应用启动时执行
    shutdown: 应用关闭时执行
    """
    # ========== Startup ==========
    logger.info("🚀 Starting up Virtual Classroom Backend (Multi-Agent)...")
    
    try:
        # 1. 初始化数据库（异步引擎）
        from app.db.session import engine
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database tables created/verified")
        
        # 2. 初始化Chroma向量数据库
        from app.db.vector import init_chroma
        await init_chroma()
        logger.info("✅ Chroma vector database initialized")
        
        # 3. 初始化多智能体系统
        setup.setup_agents()
        logger.info("✅ Multi-Agent system initialized")
        
        # 4. 启动SSE心跳（保持连接）
        from app.sse.manager import sse_manager
        await sse_manager.start_heartbeat(interval=30)
        logger.info("✅ SSE heartbeart started")
        
        logger.info("🎉 Virtual Classroom Backend startup completed!")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    yield  # 应用运行期间
    
    # ========== Shutdown ==========
    logger.info("🛑 Shutting down Virtual Classroom Backend...")
    
    try:
        # 1. 停止SSE心跳
        await sse_manager.stop_heartbeat()
        
        # 2. 关闭数据库连接
        await engine.dispose()
        
        # 3. 关闭Chroma连接
        from app.db.vector import close_chroma
        await close_chroma()
        
        logger.info("✅ Cleanup completed")
        
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")
    
    logger.info("👋 Virtual Classroom Backend shutdown completed!")


# ========== 创建FastAPI应用 ==========

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="""
    AI虚拟课堂系统后端API（多智能体架构）
    
    功能模块：
    - 🔐 用户认证与授权
    - 👤 用户管理与游戏化系统
    - 🤖 多智能体AI交互（Tutor/Grader/Recommender/...）
    - 📚 学习计划管理
    - 🏆 排行榜与成就系统
    - 💬 SSE流式输出支持
    """,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# ========== 中间件配置 ==========

# CORS配置（允许前端跨域请求）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求日志中间件
@app.middleware("http")
async def logging_middleware(request, call_next):
    """记录每个请求的日志"""
    start_time = datetime.now()
    
    # 处理请求
    response = await call_next(request)
    
    # 计算耗时
    process_time = (datetime.now() - start_time).total_seconds() * 1000
    
    # 记录日志
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.2f}ms"
    )
    
    return response


# ========== 路由注册 ==========

# 健康检查
@app.get("/health", tags=["Health"])
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "features": [
            "multi-agent",
            "sse",
            "chroma",
            "langgraph"
        ]
    }


# 根路径
@app.get("/", tags=["Root"])
async def root():
    """API根路径"""
    return {
        "message": "Welcome to Virtual Classroom API (Multi-Agent System)",
        "docs": "/docs",
        "version": settings.VERSION,
        "features": {
            "multi_agent": True,
            "sse_streaming": True,
            "chroma_vector_db": True,
            "langgraph_workflow": True
        }
    }


# 注册API路由
app.include_router(api_router, prefix=settings.API_V1_STR)


# ========== 启动入口 ==========

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
