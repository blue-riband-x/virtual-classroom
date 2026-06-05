"""
DeepSeek API调用模块
负责LLM调用、流式输出、错误处理

支持：
- 普通对话
- 流式输出（用于SSE）
- 错误处理与重试
"""
from typing import List, Optional, Dict, Any, AsyncGenerator
import httpx
import json
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

# ========== 全局HTTP客户端 ==========

_client: Optional[httpx.AsyncClient] = None


async def get_http_client() -> httpx.AsyncClient:
    """获取HTTP客户端（单例）"""
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, connect=10.0),
            limits=httpx.Limits(max_connections=100)
        )
    return _client


async def close_http_client():
    """关闭HTTP客户端"""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


# ========== 核心调用函数 ==========

async def call_deepseek(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    stream: bool = False
) -> Any:
    """
    调用DeepSeek API
    
    Args:
        messages: 对话历史，格式：
            [
                {"role": "system", "content": "..."},
                {"role": "user", "content": "..."}
            ]
        model: 模型名称（默认使用settings.DEEPSEEK_MODEL）
        temperature: 温度参数（0-2）
        max_tokens: 最大token数
        stream: 是否流式输出
    
    Returns:
        如果stream=False: 完整响应字典
        如果stream=True: 异步生成器，逐token输出
    """
    if not settings.DEEPSEEK_API_KEY:
        raise ValueError("DEEPSEEK_API_KEY not configured")
    
    # 准备请求
    url = f"{settings.DEEPSEEK_BASE_URL}/chat/completions"
    headers = settings.get_deepseek_headers()
    
    payload = {
        "model": model or settings.DEEPSEEK_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": stream
    }
    
    client = await get_http_client()
    
    if not stream:
        # 非流式调用
        return await _call_deepseek_sync(client, url, headers, payload)
    else:
        # 流式调用
        return _call_deepseek_stream(client, url, headers, payload)


async def _call_deepseek_sync(
    client: httpx.AsyncClient,
    url: str,
    headers: dict,
    payload: dict
) -> dict:
    """非流式调用DeepSeek"""
    try:
        logger.info(f"🤖 Calling DeepSeek API (model={payload['model']})")
        
        response = await client.post(
            url,
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"✅ DeepSeek API success")
        
        return result
        
    except httpx.HTTPStatusError as e:
        logger.error(f"❌ DeepSeek API error: {e.response.status_code} - {e.response.text}")
        raise ValueError(f"DeepSeek API error: {e.response.status_code}")
    except Exception as e:
        logger.error(f"❌ DeepSeek API exception: {e}")
        raise


async def _call_deepseek_stream(
    client: httpx.AsyncClient,
    url: str,
    headers: dict,
    payload: dict
) -> AsyncGenerator[str, None]:
    """
    流式调用DeepSeek，返回token生成器
    
    Yields:
        每个token的字符串
    """
    try:
        logger.info(f"🌊 Calling DeepSeek API (streaming, model={payload['model']})")
        
        async with client.stream(
            "POST",
            url,
            headers=headers,
            json=payload
        ) as response:
            response.raise_for_status()
            
            # 逐行读取SSE流
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                
                data_str = line[6:]  # 去掉 "data: " 前缀
                
                if data_str == "[DONE]":
                    logger.info("✅ DeepSeek streaming completed")
                    break
                
                try:
                    data = json.loads(data_str)
                    choices = data.get("choices", [])
                    if choices:
                        delta = choices[0].get("delta", {})
                        token = delta.get("content", "")
                        if token:
                            yield token
                except json.JSONDecodeError:
                    logger.warning(f"⚠️ Failed to parse SSE data: {data_str}")
                    continue
                    
    except httpx.HTTPStatusError as e:
        logger.error(f"❌ DeepSeek streaming error: {e.response.status_code} - {e.response.text}")
        raise ValueError(f"DeepSeek API error: {e.response.status_code}")
    except Exception as e:
        logger.error(f"❌ DeepSeek streaming exception: {e}")
        raise


# ========== LangGraph节点集成 ==========

async def call_llm_node(state: dict) -> dict:
    """
    用于LangGraph节点的LLM调用
    
    Args:
        state: LangGraph状态，包含messages字段
    
    Returns:
        更新后的状态，添加ai_output字段
    """
    messages = state.get("messages", [])
    user_input = state.get("user_input", "")
    chroma_context = state.get("chroma_context", "")
    teacher_style = state.get("teacher_style", "")
    
    # 构建消息列表
    llm_messages = []
    
    # 系统提示词 - 根据教师风格选择
    if teacher_style == "humorous":
        system_prompt = """你是AI虚拟课堂的幽默导师，风格风趣搞笑，像脱口秀演员。
你的任务是帮助用户学习编程、解答问题、提供学习建议。
请用幽默、生动的方式回答，可以适当加入玩笑、比喻、俏皮话，让学习变得有趣。
但不要只搞笑不讲干货——要在欢乐中传递知识，深入浅出。"""
    elif teacher_style == "rigorous":
        system_prompt = """你是AI虚拟课堂的严谨导师，风格严肃认真，像大学教授。
你的任务是帮助用户学习编程、解答问题、提供学习建议。
请用严谨、系统、专业的方式回答，注重逻辑性和准确性。
回答要有条理，分点阐述，引用准确，不轻易下结论，必要时指出知识边界。"""
    else:
        system_prompt = """你是AI虚拟课堂的智能导师。
你的任务是帮助用户学习编程、解答问题、提供学习建议。
请友好、耐心、专业地回答用户的问题。"""
    
    if chroma_context:
        system_prompt += f"\n\n相关历史对话：\n{chroma_context}"
    
    llm_messages.append({"role": "system", "content": system_prompt})
    
    # 添加历史消息（最多10条）
    recent_messages = messages[-10:] if len(messages) > 10 else messages
    for msg in recent_messages:
        if isinstance(msg, dict):
            llm_messages.append(msg)
        else:
            # LangChain消息对象
            llm_messages.append({
                "role": "user" if msg.type == "human" else "assistant",
                "content": msg.content
            })
    
    # 添加当前用户输入
    if user_input and (not llm_messages or llm_messages[-1].get("content") != user_input):
        llm_messages.append({"role": "user", "content": user_input})
    
    # 调用LLM
    response = await call_deepseek(
        messages=llm_messages,
        stream=False
    )
    
    # 提取回答
    ai_output = response["choices"][0]["message"]["content"]
    
    # 更新状态
    state["ai_output"] = ai_output
    state["messages"].append({"role": "assistant", "content": ai_output})
    
    return state


async def call_llm_stream_node(state: dict) -> dict:
    """
    用于LangGraph节点的LLM流式调用
    将token推送到SSE队列
    """
    messages = state.get("messages", [])
    user_input = state.get("user_input", "")
    sse_queue = state.get("sse_queue")
    
    # 构建消息列表（同上）
    llm_messages = []
    llm_messages.append({"role": "system", "content": "你是AI虚拟课堂的智能导师..."})
    # ... (省略消息构建代码)
    llm_messages.append({"role": "user", "content": user_input})
    
    # 流式调用LLM
    ai_output = ""
    async for token in await call_deepseek(
        messages=llm_messages,
        stream=True
    ):
        ai_output += token
        
        # 推送到SSE队列
        if sse_queue:
            await sse_queue.put({
                "event": "token",
                "data": {"token": token}
            })
    
    # 完成
    if sse_queue:
        await sse_queue.put({
            "event": "done",
            "data": {"full_text": ai_output}
        })
    
    state["ai_output"] = ai_output
    return state


# ========== 测试函数 ==========

async def test_deepseek():
    """测试DeepSeek API调用"""
    print("🧪 Testing DeepSeek API...")
    
    try:
        # 测试非流式
        response = await call_deepseek(
            messages=[{"role": "user", "content": "你好，请介绍一下自己"}],
            stream=False
        )
        print(f"✅ Non-stream response: {response['choices'][0]['message']['content'][:50]}...")
        
        # 测试流式
        print("\n🧪 Testing streaming...")
        tokens = []
        async for token in await call_deepseek(
            messages=[{"role": "user", "content": "数到5"}],
            stream=True
        ):
            tokens.append(token)
            print(token, end="", flush=True)
        
        print(f"\n\n✅ Streaming completed, total tokens: {len(tokens)}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_deepseek())
