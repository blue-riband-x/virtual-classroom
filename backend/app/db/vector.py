"""
Chroma向量数据库连接与操作
用于历史对话的语义检索

阿里百炼 embedding-v4 用于文本向量化
"""
from typing import List, Optional, Dict, Any
import logging
import chromadb
from chromadb.config import Settings as ChromaSettings

# LangChain可选导入
try:
    from langchain_community.vectorstores import Chroma
    from langchain_community.embeddings import DashScopeEmbeddings
    _HAS_LANGCHAIN = True
except ImportError:
    _HAS_LANGCHAIN = False
    Chroma = None
    DashScopeEmbeddings = None

from app.core.config import settings

logger = logging.getLogger(__name__)

# ========== 全局变量 ==========

# Chroma客户端（持久化）
_chroma_client = None

# Embedding模型（阿里百炼）
_embeddings = None


# ========== 初始化函数 ==========

async def init_chroma():
    """
    初始化Chroma向量数据库
    
    在FastAPI startup时调用：
    ```python
    @asynccontextmanager
    async def lifespan(app):
        await init_chroma()
        yield
        await close_chroma()
    ```
    """
    global _chroma_client, _embeddings
    
    try:
        logger.info("🔧 Initializing Chroma vector database...")
        
        # 1. 创建Chroma客户端（持久化到磁盘）
        _chroma_client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIRECTORY,
            settings=ChromaSettings(
                allow_reset=True,
                is_persistent=True
            )
        )
        logger.info(f"✅ Chroma client created at {settings.CHROMA_PERSIST_DIRECTORY}")
        
        # 2. 初始化Embedding模型（阿里百炼 embedding-v4）
        if not _HAS_LANGCHAIN:
            logger.warning("⚠️ langchain_community not installed — Chroma retrieval disabled")
            return
        
        if not settings.DASHSCOPE_API_KEY:
            logger.warning("⚠️ DASHSCOPE_API_KEY not set, Chroma retrieval disabled")
            return
        
        if not DashScopeEmbeddings:
            logger.warning("⚠️ DashScopeEmbeddings not available")
            return
        
        _embeddings = DashScopeEmbeddings(
            model=settings.DASHSCOPE_EMBEDDING_MODEL,
            dashscope_api_key=settings.DASHSCOPE_API_KEY
        )
        logger.info(f"✅ Embeddings model loaded: {settings.DASHSCOPE_EMBEDDING_MODEL}")
        
        # 3. 测试连接
        test_text = ["test"]
        test_embedding = _embeddings.embed_documents(test_text)
        logger.info(f"✅ Embedding test passed, dimension: {len(test_embedding[0])}")
        
        logger.info("🎉 Chroma vector database initialization completed!")
        
    except Exception as e:
        logger.error(f"❌ Chroma initialization failed: {e}")
        raise


async def close_chroma():
    """关闭Chroma连接"""
    global _chroma_client, _embeddings
    
    logger.info("🔴 Closing Chroma connection...")
    
    _chroma_client = None
    _embeddings = None
    
    logger.info("✅ Chroma connection closed")


# ========== 获取向量数据库实例 ==========

def get_vectorstore(user_id: int) -> Chroma:
    """
    获取指定用户的向量数据库实例
    
    Args:
        user_id: 用户ID
        
    Returns:
        Chroma向量数据库实例
        
    Note:
        每个用户有独立的collection，避免数据混淆
    """
    if _chroma_client is None:
        raise ValueError("Chroma not initialized. Call init_chroma() first.")
    
    if _embeddings is None:
        raise ValueError("Embeddings not initialized. Check DASHSCOPE_API_KEY.")
    
    collection_name = f"user_{user_id}_conversations"
    
    vectorstore = Chroma(
        client=_chroma_client,
        collection_name=collection_name,
        embedding_function=_embeddings,
        persist_directory=settings.CHROMA_PERSIST_DIRECTORY
    )
    
    return vectorstore


# ========== 保存对话 ==========

def save_conversation(
    user_id: int,
    messages: List[Dict[str, Any]]
):
    """
    保存对话到Chroma
    
    Args:
        user_id: 用户ID
        messages: 对话消息列表，格式：
            [
                {
                    "role": "user",
                    "content": "Python列表怎么用？",
                    "timestamp": "2026-05-18T15:00:00"
                },
                {
                    "role": "assistant",
                    "content": "Python列表是...",
                    "timestamp": "2026-05-18T15:00:05"
                }
            ]
    """
    if _embeddings is None:
        logger.warning("⚠️ Embeddings not available, skipping save")
        return
    
    try:
        vectorstore = get_vectorstore(user_id)
        
        # 准备数据
        texts = [msg["content"] for msg in messages]
        metadatas = [
            {
                "role": msg.get("role", "unknown"),
                "timestamp": msg.get("timestamp", ""),
                "session_id": msg.get("session_id", "")
            }
            for msg in messages
        ]
        ids = [f"{user_id}_{msg.get('timestamp', i)}" for i, msg in enumerate(messages)]
        
        # 添加到向量数据库
        vectorstore.add_texts(
            texts=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(f"✅ Saved {len(texts)} messages to Chroma (user={user_id})")
        
    except Exception as e:
        logger.error(f"❌ Failed to save conversation: {e}")


# ========== 检索相关历史 ==========

def retrieve_relevant_history(
    user_id: int,
    query: str,
    k: int = 5
) -> List[Dict[str, Any]]:
    """
    从Chroma检索相关历史对话
    
    Args:
        user_id: 用户ID
        query: 查询文本
        k: 返回最相关的k条记录
        
    Returns:
        相关对话列表，格式：
        [
            {
                "content": "...",
                "metadata": {"role": "user", "timestamp": "..."},
                "distance": 0.123  # 相似度距离
            },
            ...
        ]
    """
    if _embeddings is None:
        logger.warning("⚠️ Embeddings not available, returning empty history")
        return []
    
    try:
        vectorstore = get_vectorstore(user_id)
        
        # 相似度搜索
        docs = vectorstore.similarity_search_with_score(
            query=query,
            k=k
        )
        
        # 格式化结果
        results = [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "distance": score
            }
            for doc, score in docs
        ]
        
        logger.info(f"✅ Retrieved {len(results)} relevant history (user={user_id})")
        return results
        
    except Exception as e:
        logger.error(f"❌ Failed to retrieve history: {e}")
        return []


# ========== 清除用户历史 ==========

def clear_user_history(user_id: int):
    """
    清除指定用户的所有历史对话
    
    Args:
        user_id: 用户ID
    """
    if _chroma_client is None:
        logger.warning("⚠️ Chroma not initialized")
        return
    
    try:
        collection_name = f"user_{user_id}_conversations"
        
        # 删除collection
        _chroma_client.delete_collection(collection_name)
        
        logger.info(f"✅ Cleared history for user {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Failed to clear history: {e}")


# ========== 获取用户历史统计 ==========

def get_user_history_stats(user_id: int) -> Dict[str, Any]:
    """
    获取用户历史对话统计
    
    Args:
        user_id: 用户ID
        
    Returns:
        统计信息字典
    """
    if _chroma_client is None:
        return {"error": "Chroma not initialized"}
    
    try:
        collection_name = f"user_{user_id}_conversations"
        collection = _chroma_client.get_collection(collection_name)
        
        count = collection.count()
        
        return {
            "user_id": user_id,
            "total_conversations": count
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get stats: {e}")
        return {"error": str(e)}
