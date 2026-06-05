# AI虚拟课堂 - LangGraph + FastAPI 后端架构设计（学生实践版）

## 一、架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Vue 3)                      │
│   (Three.js 3D Avatar + SSE EventSource)                 │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS
┌────────────────────────▼────────────────────────────────────┐
│                   FastAPI Application                       │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              API Layer (Router)                      │  │
│  │  /api/v1/auth/*  /api/v1/learn/*  /api/v1/ai/*   │  │
│  └───────────────────┬─────────────────────────────────┘  │
│                      │                                      │
│  ┌───────────────────▼─────────────────────────────────┐  │
│  │         Service Layer (Business Logic)                │  │
│  │  AuthService  UserService  LearningService           │  │
│  └───────────────────┬─────────────────────────────────┘  │
│                      │                                      │
│  ┌───────────────────▼─────────────────────────────────┐  │
│  │         LangGraph Layer (AI Workflow)                │  │
│  │  StateGraph  Nodes  Edges  ConditionalEdges        │  │
│  └───────────────────┬─────────────────────────────────┘  │
│                      │                                      │
│  ┌───────────────────▼─────────────────────────────────┐  │
│  │         SSE Service (Server-Sent Events)             │  │
│  │  EventGenerator  SSEManager  StreamingResponse      │  │
│  │  (使用asyncio.Queue，无需Redis)                   │  │
│  └───────────────────┬─────────────────────────────────┘  │
│                      │                                      │
│  ┌───────────────────▼─────────────────────────────────┐  │
│  │         Data Layer                                    │  │
│  │  ┌─────────────┐  ┌─────────────┐                 │  │
│  │  │ MySQL        │  │ Chroma       │                 │  │
│  │  │ (异步SQLAlchemy)│  │ (向量数据库) │                 │  │
│  │  │ 结构化数据    │  │ 历史对话    │                 │  │
│  │  └─────────────┘  └─────────────┘                 │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│              External Services                               │
│  DeepSeek API  Moonshot API                                │
└─────────────────────────────────────────────────────────────┘
```

## 二、项目目录结构（简化版）

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI应用入口
│   │
│   ├── api/                      # API路由层
│   │   ├── __init__.py
│   │   ├── deps.py               # 依赖注入
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py            # 路由聚合
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── auth.py       # 认证路由（简化）
│   │           ├── users.py     # 用户路由
│   │           ├── learning.py  # 学习管理路由
│   │           ├── gamification.py # 游戏化路由
│   │           ├── ai.py        # AI交互路由（SSE）
│   │           ├── classroom.py # 课堂路由
│   │           └── leaderboard.py # 排行榜路由
│   │
│   ├── core/                     # 核心配置
│   │   ├── __init__.py
│   │   ├── config.py            # 配置管理（Pydantic Settings）
│   │   ├── security.py         # 安全工具（JWT、简化密码）
│   │   └── constants.py        # 常量定义
│   │
│   ├── db/                      # 数据库层
│   │   ├── __init__.py
│   │   ├── session.py          # 异步会话管理（MySQL）
│   │   ├── base.py             # 声明式基类
│   │   └── vector.py          # Chroma向量数据库连接 ⭐新增
│   │
│   ├── models/                  # SQLAlchemy模型（简化）
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── learning_plan.py
│   │   ├── learning_record.py
│   │   ├── achievement.py
│   │   ├── leaderboard.py
│   │   └── classroom.py
│   │
│   ├── schemas/                 # Pydantic Schemas
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── learning.py
│   │   ├── gamification.py
│   │   ├── ai.py              # AI请求/响应Schema
│   │   └── response.py        # 统一响应格式
│   │
│   ├── services/                # 业务逻辑层（简化）
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   ├── auth_service.py
│   │   ├── learning_service.py
│   │   ├── gamification_service.py
│   │   ├── achievement_service.py
│   │   ├── leaderboard_service.py
│   │   └── classroom_service.py
│   │
│   ├── langgraph/               # LangGraph AI工作流层 ⭐
│   │   ├── __init__.py
│   │   ├── config.py           # LangGraph配置
│   │   ├── state.py            # 全局状态定义
│   │   ├── graphs/             # 各个工作流图
│   │   │   ├── __init__.py
│   │   │   ├── tutor_graph.py  # AI导师工作流
│   │   │   ├── outline_graph.py # AI大纲生成工作流
│   │   │   ├── polish_graph.py  # AI润色工作流
│   │   │   └── recommend_graph.py # AI推荐工作流
│   │   ├── nodes/              # 节点函数
│   │   │   ├── __init__.py
│   │   │   ├── input_nodes.py
│   │   │   ├── llm_nodes.py
│   │   │   ├── tool_nodes.py
│   │   │   ├── output_nodes.py
│   │   │   ├── chroma_nodes.py # Chroma检索节点 ⭐新增
│   │   │   └── conditional_nodes.py
│   │   ├── tools/              # LangChain Tools
│   │   │   ├── __init__.py
│   │   │   ├── search_tools.py
│   │   │   ├── code_tools.py
│   │   │   └── database_tools.py
│   │   └── utils/              # LangGraph工具函数
│   │       ├── __init__.py
│   │       ├── stream.py       # 流式输出工具
│   │       └── checkpoint.py   # 检查点保存
│   │
│   ├── sse/                     # SSE服务层 ⭐
│   │   ├── __init__.py
│   │   ├── manager.py          # SSE连接管理器（使用asyncio.Queue）
│   │   ├── generator.py        # SSE事件生成器
│   │   ├── models.py          # SSE数据模型
│   │   └── queue.py          # 事件队列（内存）
│   │
│   ├── middlewares/             # 中间件（简化）
│   │   ├── __init__.py
│   │   ├── logging.py         # 请求日志中间件
│   │   └── error_handler.py  # 全局错误处理
│   │
│   └── utils/                    # 工具函数
│       ├── __init__.py
│       ├── datetime.py
│       └── validators.py
│
├── tests/                        # 测试
│   ├── unit/
│   └── integration/
│
├── scripts/                      # 脚本
│   └── init_db.py              # 初始化数据库
│
├── docs/                         # 文档
│   ├── api.md                  # API文档
│   ├── langgraph_design.md    # LangGraph设计文档
│   ├── sse_design.md          # SSE设计文档
│   └── architecture.md        # 架构文档
│
├── .env.example                 # 环境变量示例
├── .env                         # 环境变量（不提交）
├── requirements.txt             # 依赖清单
└── README.md                   # 项目说明
```

## 三、为什么不用Redis？（学生实践项目）

### 3.1 Redis的典型用途及替代方案

| Redis用途 | 是否需要 | 替代方案（无需Redis） |
|----------|---------|---------------------|
| **SSE事件队列** | ❌ 不需要 | 使用 `asyncio.Queue`（内存） |
| **用户Session缓存** | ❌ 不需要 | JWT Token（无状态） |
| **排行榜缓存** | ❌ 不需要 | 直接MySQL查询（数据量小） |
| **限流** | ❌ 不需要 | 简单的内存计数器 |
| **Pub/Sub** | ❌ 不需要 | 单机直接函数调用 |

### 3.2 SSE实现（无需Redis）

```python
# app/sse/manager.py

import asyncio
from typing import Dict, List
from fastapi import Request

class SSEManager:
    """SSE连接管理器（使用asyncio.Queue，无需Redis）"""
    
    def __init__(self):
        # user_id -> List[asyncio.Queue]
        self.connections: Dict[int, List[asyncio.Queue]] = {}
    
    async def connect(self, user_id: int) -> asyncio.Queue:
        """建立SSE连接"""
        queue = asyncio.Queue()
        if user_id not in self.connections:
            self.connections[user_id] = []
        self.connections[user_id].append(queue)
        return queue
    
    def disconnect(self, user_id: int, queue: asyncio.Queue):
        """断开SSE连接"""
        if user_id in self.connections:
            if queue in self.connections[user_id]:
                self.connections[user_id].remove(queue)
            # 清理空列表
            if not self.connections[user_id]:
                del self.connections[user_id]
    
    async def send_event(self, user_id: int, event: dict):
        """向指定用户发送SSE事件"""
        if user_id in self.connections:
            for queue in self.connections[user_id]:
                await queue.put(event)
    
    async def broadcast(self, event: dict, user_ids: List[int]):
        """广播事件给多个用户"""
        for user_id in user_ids:
            await self.send_event(user_id, event)
```

**优点**：
- ✅ 无需安装Redis
- ✅ 无需管理额外服务
- ✅ 适合单机部署
- ✅ 代码更简单

**缺点**：
- ❌ 多进程/多机器无法共享Queue
- ❌ 重启后所有连接断开

**结论**：学生实践项目完全够用！

---

## 四、Chroma向量数据库设计 ⭐

### 4.1 为什么需要Chroma？

```
问题：用户提问 "Python的列表怎么用？"
     需要找到历史对话中关于"Python列表"的讨论

传统MySQL：
  - 只能用LIKE模糊搜索
  - 无法理解语义（"列表" vs "list" vs "array"）

Chroma向量数据库：
  - 语义搜索：理解意图，找到相关对话
  - 自动嵌入：使用embedding模型（如sentence-transformers）
  - 持久化：保存到磁盘，重启不丢失
```

### 4.2 Chroma集成设计

```python
# app/db/vector.py

import chromadb
from chromadb.config import Settings
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from app.core.config import settings

# 初始化Chroma（持久化到磁盘）
def get_chroma_client():
    """获取Chroma客户端"""
    return chromadb.PersistentClient(
        path=settings.CHROMA_PERSIST_DIRECTORY
    )

def get_vectorstore(user_id: int):
    """获取用户的向量数据库实例"""
    embeddings = SentenceTransformerEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )
    
    return Chroma(
        client=get_chroma_client(),
        collection_name=f"user_{user_id}_conversations",
        embedding_function=embeddings
    )

# 保存对话到Chroma
def save_conversation(user_id: int, messages: list):
    """保存对话到向量数据库"""
    vectorstore = get_vectorstore(user_id)
    
    texts = [msg["content"] for msg in messages]
    metadatas = [{"role": msg["role"], "timestamp": msg["timestamp"]} 
                  for msg in messages]
    
    vectorstore.add_texts(texts=texts, metadatas=metadatas)

# 从Chroma检索相关历史对话
def retrieve_relevant_history(user_id: int, query: str, k: int = 5):
    """检索相关历史对话"""
    vectorstore = get_vectorstore(user_id)
    
    docs = vectorstore.similarity_search(query, k=k)
    
    return [
        {
            "content": doc.page_content,
            "metadata": doc.metadata
        }
        for doc in docs
    ]
```

### 4.3 LangGraph中集成Chroma

```python
# app/langgraph/nodes/chroma_nodes.py

from app.db.vector import retrieve_relevant_history

async def retrieve_context(state: TutorState) -> TutorState:
    """从Chroma检索相关历史对话"""
    
    user_id = state.user_id
    query = state.user_input
    
    # 从Chroma检索相关历史
    relevant_docs = retrieve_relevant_history(
        user_id=user_id,
        query=query,
        k=5  # 检索最相关的5条历史
    )
    
    # 将历史对话添加到state
    context = "\n".join([doc["content"] for doc in relevant_docs])
    state.context = context
    
    return state
```

### 4.4 Chroma在架构中的位置

```
LangGraph工作流程：
┌─────────────────────────────────────────┐
│  用户输入："Python列表怎么用？"          │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│  Node 1: 输入处理                       │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐ ⭐
│  Node 2: Chroma检索相关历史            │
│  - 从vectorstore检索top-5相关对话     │
│  - 将历史添加到context                 │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│  Node 3: LLM生成回答                   │
│  - 输入：user_input + context         │
│  - 调用DeepSeek API                   │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│  Node 4: 保存新对话到Chroma           │ ⭐
│  - 将新对话保存到vectorstore          │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│  Node 5: SSE流式输出                   │
└──────────────┬──────────────────────────┘
               ↓
              END
```

---

## 五、LangGraph + SSE 集成设计

### 5.1 LangGraph核心概念

```
LangGraph StateGraph 核心组件：
┌─────────────────────────────────────────────────┐
│              StateGraph (状态图)                │
├─────────────────────────────────────────────────┤
│  State (状态)                                  │
│  ├── 定义：TypedDict                          │
│  ├── 包含：messages, user_input, ai_output   │
│  ├── 包含：chroma_context (⭐新增)           │
│  └── 持久化：通过checkpoint机制              │
├─────────────────────────────────────────────────┤
│  Nodes (节点)                                  │
│  ├── input_node: 接收用户输入                 │
│  ├── chroma_retrieve_node: 从Chroma检索 ⭐  │
│  ├── llm_node: 调用LLM                       │
│  ├── chroma_save_node: 保存到Chroma ⭐      │
│  ├── output_node: 格式化输出                  │
│  ├── sse_stream_node: 流式输出到SSE          │
│  └── conditional_node: 条件判断               │
├─────────────────────────────────────────────────┤
│  Edges (边)                                    │
│  ├── 普通边：node_a → node_b                 │
│  ├── 条件边：Conditional Edge                │
│  └── 循环边：node_b → node_a (retry)        │
└─────────────────────────────────────────────────┘
```

### 5.2 AI导师工作流完整代码框架

```python
# app/langgraph/graphs/tutor_graph.py

from langgraph.graph import StateGraph, END
from app.langgraph.state import TutorState
from app.langgraph.nodes import (
    input_nodes,
    chroma_nodes,  # ⭐ 新增
    llm_nodes,
    output_nodes,
    sse_nodes
)

def create_tutor_graph():
    """创建AI导师工作流图"""
    
    # 定义状态图
    graph = StateGraph(TutorState)
    
    # 添加节点
    graph.add_node("input_processor", input_nodes.process_user_input)
    graph.add_node("chroma_retriever", chroma_nodes.retrieve_context)  # ⭐
    graph.add_node("llm_generator", llm_nodes.generate_ai_response)
    graph.add_node("chroma_saver", chroma_nodes.save_conversation)  # ⭐
    graph.add_node("response_formatter", output_nodes.format_response)
    graph.add_node("sse_streamer", sse_nodes.stream_to_sse)
    
    # 添加边
    graph.add_edge("input_processor", "chroma_retriever")
    graph.add_edge("chroma_retriever", "llm_generator")
    graph.add_edge("llm_generator", "chroma_saver")
    graph.add_edge("chroma_saver", "response_formatter")
    graph.add_edge("response_formatter", "sse_streamer")
    graph.add_edge("sse_streamer", END)
    
    # 设置入口
    graph.set_entry_point("input_processor")
    
    return graph.compile()
```

### 5.3 State状态设计（加入Chroma字段）

```python
# app/langgraph/state.py

from typing import List, Optional, Dict, Any
from langchain_core.messages import BaseMessage
from pydantic import BaseModel

class TutorState(BaseModel):
    """AI导师状态"""
    
    # 用户ID
    user_id: int
    
    # 消息历史
    messages: List[BaseMessage]
    
    # 用户输入
    user_input: str
    
    # Chroma检索的上下文 ⭐ 新增
    chroma_context: Optional[str] = None
    
    # 其他上下文（非向量数据）
    context: Optional[Dict[str, Any]] = None
    
    # AI输出
    ai_output: Optional[str] = None
    
    # SSE事件队列
    sse_queue: Optional[asyncio.Queue] = None
    
    # 中间步骤
    intermediate_steps: List[Dict[str, Any]] = []
    
    # 错误状态
    error: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True
```

---

## 六、SSE设计（无需Redis）

### 6.1 SSE端点

```python
# app/api/v1/endpoints/ai.py

from fastapi import APIRouter, Depends, Request
from sse_starlette.sse import EventSourceResponse
from app.sse.manager import sse_manager
from app.langgraph.graphs.tutor_graph import create_tutor_graph

router = APIRouter()

@router.post("/ai/tutor/{session_id}")
async def start_tutor_session(
    session_id: str,
    request: Request,
    input_data: TutorInput,
    current_user = Depends(get_current_user)
):
    """启动AI导师会话（非流式，用于初始化）"""
    # 创建SSE队列
    queue = await sse_manager.connect(current_user.id)
    
    # 启动LangGraph工作流（异步）
    asyncio.create_task(
        run_tutor_workflow(
            user_id=current_user.id,
            session_id=session_id,
            user_input=input_data.message,
            sse_queue=queue
        )
    )
    
    return {"session_id": session_id, "status": "started"}

@router.get("/ai/tutor/stream/{session_id}")
async def tutor_sse_stream(
    session_id: str,
    request: Request,
    current_user = Depends(get_current_user)
):
    """AI导师SSE流式输出"""
    
    # 获取该用户的SSE队列
    queue = await sse_manager.get_queue(current_user.id, session_id)
    
    # 创建事件生成器
    async def event_generator():
        try:
            # 发送初始连接成功事件
            yield {
                "event": "connected",
                "data": {"session_id": session_id}
            }
            
            # 循环读取队列中的事件
            while True:
                if await request.is_disconnected():
                    break
                
                # 从队列获取事件（等待最多1秒）
                try:
                    event = await asyncio.wait_for(
                        queue.get(), 
                        timeout=1.0
                    )
                    yield event
                except asyncio.TimeoutError:
                    # 发送心跳
                    yield {"event": "heartbeat", "data": ""}
            
        finally:
            sse_manager.disconnect(current_user.id, session_id)
    
    return EventSourceResponse(event_generator())
```

### 6.2 LangGraph → SSE 集成

```python
# app/langgraph/nodes/sse_nodes.py

import asyncio
from app.sse.manager import sse_manager

async def stream_to_sse(state: TutorState) -> TutorState:
    """将LangGraph输出流式推送到SSE"""
    
    user_id = state.user_id
    sse_queue = state.sse_queue
    ai_output = state.ai_output
    
    # 按token流式输出
    tokens = list(ai_output)  # 简单按字符分割
    total_tokens = len(tokens)
    
    for i in range(0, total_tokens, 5):  # 每次5个字符
        token_chunk = "".join(tokens[i:i+5])
        progress = i / total_tokens
        
        event = {
            "event": "token",
            "data": {
                "token": token_chunk,
                "progress": round(progress, 2)
            }
        }
        
        # 发送到SSE队列
        await sse_manager.send_event(user_id, event)
        
        await asyncio.sleep(0.05)  # 控制流速
    
    # 发送完成事件
    await sse_manager.send_event(user_id, {
        "event": "done",
        "data": {"full_text": ai_output}
    })
    
    return state
```

---

## 七、数据库设计（MySQL + Chroma）

### 7.1 MySQL表结构（简化）

```python
# app/models/user.py

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, Text
from sqlalchemy.sql import func
from app.db.base import BaseModel

class User(BaseModel):
    """用户表（简化版）"""
    
    __tablename__ = "users"
    
    # 基本信息
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)  # 简化：明文或简单哈希
    nickname = Column(String(50), nullable=False)
    avatar_url = Column(String(255), nullable=True)
    
    # 游戏化字段
    xp = Column(Integer, default=0)
    level = Column(Integer, default=1)
    streak = Column(Integer, default=0)
    total_learning_hours = Column(Float, default=0.0)
    
    # 3D形象配置
    avatar_3d_config = Column(JSON, nullable=True)
```

### 7.2 Chroma集合设计

```
Chroma Collections:
┌─────────────────────────────────────────────────┐
│  Collection: user_{user_id}_conversations      │
├─────────────────────────────────────────────────┤
│  Document: "用户问：Python列表怎么用？"       │
│  Metadata: {                                  │
│    "role": "user",                           │
│    "timestamp": "2026-05-18T15:00:00"      │
│    "session_id": "abc123"                    │
│  }                                           │
├─────────────────────────────────────────────────┤
│  Document: "AI答：Python列表是..."            │
│  Metadata: {                                  │
│    "role": "assistant",                      │
│    "timestamp": "2026-05-18T15:00:05"      │
│    "session_id": "abc123"                    │
│  }                                           │
└─────────────────────────────────────────────────┘
```

---

## 八、技术栈总结（学生实践版）

| 层级 | 技术选型 | 说明 |
|------|-----------|------|
| **Web框架** | FastAPI | 高性能、自动生成OpenAPI文档 |
| **AI工作流** | LangGraph + LangChain | 状态管理、复杂工作流编排 |
| **SSE** | sse-starlette | 支持Starlette/FastAPI的SSE |
| **关系数据库** | MySQL + SQLAlchemy (Async) | 异步数据库操作 |
| **向量数据库** | Chroma | 轻量级，无需服务器 ⭐ |
| **LLM** | DeepSeek / Moonshot | 根据需求选择 |
| **认证** | JWT (python-jose) | 无状态认证（简化版） |
| **密码存储** | 明文或简单哈希 | 学生项目，暂不强调安全性 |
| **数据验证** | Pydantic v2 | 请求/响应验证 |
| **SSE队列** | asyncio.Queue | 内存队列，无需Redis ⭐ |
| **日志** | logging | 简单日志 |

---

## 九、下一步行动

1. **确认架构设计** - 这个简化版是否符合你的需求？
2. **开始编码** - 我可以帮你实现具体模块（如LangGraph工作流、SSE、Chroma集成等）
3. **调整设计** - 如果有需要修改的地方

**请告诉我你的想法！** 🚀
