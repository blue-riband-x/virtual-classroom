"""
SSE (Server-Sent Events) 连接管理器
使用asyncio.Queue实现，无需Redis（适合学生实践项目）

功能：
1. 管理多个用户的SSE连接
2. 支持多会话（一个用户可同时有多个SSE会话）
3. 向指定用户/会话推送事件
4. 心跳机制保持连接
"""
import asyncio
import logging
from typing import Dict, List, Optional, AsyncGenerator
from datetime import datetime

logger = logging.getLogger(__name__)


class SSEManager:
    """
    SSE连接管理器（单例模式）
    
    设计：
    - 每个用户可以有多个活跃会话（session_id）
    - 每个会话对应一个asyncio.Queue
    - 通过Queue实现事件推送（无需Redis）
    
    存储结构：
    {
        user_id_1: {
            "session_abc": Queue(),
            "session_xyz": Queue()
        },
        user_id_2: {...}
    }
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # user_id -> {session_id -> asyncio.Queue}
        self.connections: Dict[int, Dict[str, asyncio.Queue]] = {}
        
        # 心跳任务
        self._heartbeat_task = None
        
        self._initialized = True
        logger.info("✅ SSEManager initialized")
    
    async def connect(self, user_id: int, session_id: str) -> asyncio.Queue:
        """
        建立SSE连接
        
        Args:
            user_id: 用户ID
            session_id: 会话ID（用于区分同一用户的多个SSE连接）
        
        Returns:
            asyncio.Queue: 用于接收SSE事件
        """
        if user_id not in self.connections:
            self.connections[user_id] = {}
        
        # 清理同一会话的旧连接（可能前端断开后重连）
        if session_id in self.connections[user_id]:
            old_queue = self.connections[user_id][session_id]
            try:
                old_queue.put_nowait(None)  # 通知旧消费者退出
            except asyncio.QueueFull:
                pass
        
        # 创建新队列
        queue = asyncio.Queue(maxsize=200)
        self.connections[user_id][session_id] = queue
        
        logger.info(f"🟢 SSE connected: user={user_id}, session={session_id}")
        logger.info(f"   活跃连接数: {self._count_total_connections()}")
        
        return queue
    
    def disconnect(self, user_id: int, session_id: str):
        """
        断开SSE连接
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
        """
        if user_id in self.connections:
            if session_id in self.connections[user_id]:
                # 发送结束信号
                try:
                    self.connections[user_id][session_id].put_nowait(None)
                except:
                    pass
                
                # 删除连接
                del self.connections[user_id][session_id]
                logger.info(f"🔴 SSE disconnected: user={user_id}, session={session_id}")
            
            # 清理空用户
            if not self.connections[user_id]:
                del self.connections[user_id]
        
        logger.info(f"   剩余活跃连接: {self._count_total_connections()}")
    
    async def send_event(
        self,
        user_id: int,
        session_id: str,
        event: dict
    ) -> bool:
        """
        向指定用户的指定会话发送SSE事件
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            event: SSE事件字典，格式：
                {
                    "event": "token",  # 事件类型
                    "data": {"token": "...", "progress": 0.5}
                }
        
        Returns:
            bool: 是否发送成功
        """
        if user_id not in self.connections:
            logger.warning(f"⚠️ User {user_id} has no active SSE connections")
            return False
        
        if session_id not in self.connections[user_id]:
            logger.warning(f"⚠️ Session {session_id} not found for user {user_id}")
            return False
        
        queue = self.connections[user_id][session_id]
        
        # None 是终止信号
        if event is None:
            try:
                queue.put_nowait(None)
            except asyncio.QueueFull:
                # 队列满时强制丢弃一个旧事件
                try:
                    queue.get_nowait()
                    queue.put_nowait(None)
                except:
                    pass
            return True
        
        try:
            # 非阻塞放入队列
            queue.put_nowait(event)
            return True
        except asyncio.QueueFull:
            # 队列满时：丢弃最旧的事件，腾出空间给新事件
            try:
                queue.get_nowait()  # 丢弃一个旧事件
                queue.put_nowait(event)  # 放入新事件
                logger.debug(f"📦 SSE queue overflow, dropped oldest event for user={user_id}, session={session_id}")
                return True
            except:
                logger.warning(f"⚠️ SSE queue full and cannot drain for user={user_id}, session={session_id}")
                return False
    
    async def broadcast_to_user(self, user_id: int, event: dict):
        """
        向用户的所有会话广播事件
        
        Args:
            user_id: 用户ID
            event: SSE事件
        """
        if user_id not in self.connections:
            return
        
        for session_id in list(self.connections[user_id].keys()):
            await self.send_event(user_id, session_id, event)
    
    async def broadcast_to_users(self, user_ids: List[int], event: dict):
        """
        向多个用户广播事件
        
        Args:
            user_ids: 用户ID列表
            event: SSE事件
        """
        for user_id in user_ids:
            await self.broadcast_to_user(user_id, event)
    
    def _count_total_connections(self) -> int:
        """统计总连接数"""
        total = 0
        for user_sessions in self.connections.values():
            total += len(user_sessions)
        return total
    
    def get_active_connections(self) -> Dict[int, List[str]]:
        """
        获取所有活跃连接
        
        Returns:
            {user_id: [session_id1, session_id2, ...], ...}
        """
        return {
            user_id: list(sessions.keys())
            for user_id, sessions in self.connections.items()
        }
    
    async def start_heartbeat(self, interval: int = 30):
        """
        启动心跳任务（保持SSE连接 + 清理过期会话）
        
        Args:
            interval: 心跳间隔（秒）
        """
        if self._heartbeat_task is not None:
            return
        
        async def _heartbeat():
            """心跳协程"""
            while True:
                await asyncio.sleep(interval)
                
                # 清理过期/满队列的会话
                self._cleanup_stale_sessions()
                
                if not self.connections:
                    continue
                
                heartbeat_event = {
                    "event": "heartbeat",
                    "data": {
                        "timestamp": datetime.now().isoformat()
                    }
                }
                
                # 向所有连接发送心跳
                for user_id, sessions in self.connections.items():
                    for session_id in sessions.keys():
                        await self.send_event(user_id, session_id, heartbeat_event)
                
                logger.debug(f"💓 SSE heartbeat sent to {self._count_total_connections()} connections")
        
        self._heartbeat_task = asyncio.create_task(_heartbeat())
        logger.info(f"💓 SSE heartbeat started (interval={interval}s)")
    
    def _cleanup_stale_sessions(self):
        """清理过期/满队列的会话（队列满说明没有消费者在读取）"""
        stale_sessions = []
        for user_id, sessions in self.connections.items():
            for session_id, queue in sessions.items():
                # 队列超过 80% 满且不是刚创建的，视为过期
                if queue.qsize() >= int(queue.maxsize * 0.8):
                    stale_sessions.append((user_id, session_id))
        
        for user_id, session_id in stale_sessions:
            self.disconnect(user_id, session_id)
            logger.info(f"🧹 Cleaned up stale SSE session: user={user_id}, session={session_id}")
        
        if stale_sessions:
            logger.info(f"🧹 Cleaned up {len(stale_sessions)} stale sessions, remaining: {self._count_total_connections()}")

    async def stop_heartbeat(self):
        """停止心跳任务"""
        if self._heartbeat_task is not None:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None
            logger.info("💓 SSE heartbeat stopped")


# 全局SSE管理器实例
sse_manager = SSEManager()
