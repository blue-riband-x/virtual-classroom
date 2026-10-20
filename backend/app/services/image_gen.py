"""
AI图片生成服务 - 使用豆包(火山方舟) Seedream 5.0 生成PPT风格板书图片

核心策略：
- 直接 HTTP 调用火山方舟 API（与官方示例一致）
- 模型：doubao-seedream-5-0-260128
- 板书助手已精炼提示词，此处直接透传
- 尺寸：2K（高清PPT横版）
"""
import logging
import os
import asyncio
import requests
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

# 板书图片保存目录
BOARD_IMAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "boards")

def _get_ark_image_api_url():
    """获取火山方舟文生图API地址"""
    return f"{settings.ARK_BASE_URL}/images/generations"


def ensure_board_dir():
    """确保板书图片目录存在"""
    os.makedirs(BOARD_IMAGE_DIR, exist_ok=True)


async def generate_board_image(
    prompt: str,
    outline_id: int,
    module_index: int,
    board_index: int,
) -> Optional[str]:
    """
    使用豆包 Seedream 生成PPT风格板书图片

    Args:
        prompt: 图片生成提示词（中文，已由板书助手精炼）
        outline_id: 大纲ID
        module_index: 模块序号
        board_index: 板书序号

    Returns:
        图片相对URL路径，失败返回None
    """
    ensure_board_dir()

    filename = f"board_{outline_id}_{module_index}_{board_index}.png"
    filepath = os.path.join(BOARD_IMAGE_DIR, filename)

    # 如果图片已存在，直接返回
    if os.path.exists(filepath):
        logger.info(f"板书图片已存在，直接使用: {filename}")
        return f"/static/boards/{filename}"

    try:
        api_key = settings.ARK_API_KEY
        if not api_key:
            logger.warning("ARK_API_KEY未配置，无法生成板书图片")
            return None

        model = settings.ARK_IMAGE_MODEL
        logger.info(f"豆包生图请求: model={model}, prompt前100字={prompt[:100]}...")

        # 按照火山方舟官方示例构造请求
        payload = {
            "model": model,
            "prompt": prompt,
            "sequential_image_generation": "disabled",
            "response_format": "url",
            "size": "1920x1920",
            "stream": False,
            "watermark": False,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        # 在线程池中执行同步HTTP请求
        loop = asyncio.get_event_loop()
        api_url = _get_ark_image_api_url()
        resp = await loop.run_in_executor(
            None,
            lambda: requests.post(api_url, json=payload, headers=headers, timeout=120)
        )

        if resp.status_code != 200:
            logger.error(f"豆包生图API返回非200: HTTP {resp.status_code}, body={resp.text[:500]}")
            return None

        result = resp.json()

        # 解析返回结果
        data = result.get("data", [])
        if not data or len(data) == 0:
            logger.error(f"豆包生图未返回图片数据: {result}")
            return None

        image_url = data[0].get("url")
        if not image_url:
            logger.error(f"豆包生图URL为空: {data[0]}")
            return None

        # 下载图片到本地
        img_resp = requests.get(image_url, timeout=60)
        if img_resp.status_code == 200:
            with open(filepath, "wb") as f:
                f.write(img_resp.content)
            file_size = len(img_resp.content)
            logger.info(f"豆包生图已保存: {filename} ({file_size} bytes)")
            return f"/static/boards/{filename}"
        else:
            logger.error(f"下载豆包生图失败: HTTP {img_resp.status_code}")
            return None

    except requests.exceptions.Timeout:
        logger.error(f"豆包生图请求超时")
        return None
    except Exception as e:
        error_msg = str(e)
        if '401' in error_msg or 'Authentication' in error_msg or 'auth' in error_msg.lower():
            logger.error(f"豆包API认证失败(401)：API Key无效。请检查ARK_API_KEY配置。错误: {error_msg}")
        elif '429' in error_msg or 'rate' in error_msg.lower():
            logger.error(f"豆包API限流(429)：请求过于频繁。错误: {error_msg}")
        else:
            logger.error(f"豆包生图异常: {e}", exc_info=True)
        return None


async def generate_boards_images(
    boards: list,
    outline_id: int,
    module_index: int,
) -> list:
    """
    为一批板书生成PPT图片（串行，避免API限流）
    """
    tasks = []
    for i, board in enumerate(boards):
        prompt = board.get("image_prompt", "")
        if prompt:
            tasks.append((i, prompt))

    if not tasks:
        return boards

    logger.info(f"开始生成{len(tasks)}张板书图片，outline={outline_id} module={module_index}")

    # 串行生成，避免并发限流
    for idx, prompt in tasks:
        image_url = await generate_board_image(prompt, outline_id, module_index, idx)
        if image_url:
            boards[idx]["image_url"] = image_url
        else:
            logger.warning(f"板书{idx}图片生成失败")

    return boards
