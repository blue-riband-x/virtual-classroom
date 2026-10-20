"""
板书智能体 V2 - 根据模块课程内容，拆分为4块，精炼PPT提示词，喂给豆包生图模型

核心原则：
- 每个模块拆分为4张PPT：1张封面 + 3张知识点页
- LLM先分析模块内容，将其拆分为4个教学段落
- 每个段落精炼出核心知识讲解点，转化为专业PPT生图提示词
- 提示词直接喂给豆包 Seedream 模型，不再由image_gen添加风格前缀/后缀
- 提示词风格：简约工科风PPT，扁平化设计，适合课堂教学
"""
import logging
import json
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

_llm = None


def _get_llm():
    global _llm
    if _llm is None:
        from langchain_deepseek import ChatDeepSeek
        from app.core.config import settings
        _llm = ChatDeepSeek(
            model=settings.DEEPSEEK_MODEL,
            api_key=settings.DEEPSEEK_API_KEY,
            temperature=0.4,
            streaming=False
        )
    return _llm


BOARD_SYSTEM_PROMPT = """你是一位资深的课堂PPT视觉设计专家，擅长将课程内容提炼为高质量的PPT生图提示词。

## 你的任务

分析AI教师的课堂内容，将模块拆分为4个教学段落，为每个段落生成一张PPT幻灯片的生图提示词。

## 工作流程

1. **分析拆分**：阅读教师讲授内容，将其拆分为4个逻辑段落（课程导入/基础概念、核心知识1、核心知识2、实操/总结）
2. **精炼提纯**：提取每个段落的核心知识讲解点
3. **转化提示词**：将知识点转化为专业的PPT生图提示词

## PPT拆分规则

- 第1张：**封面页** — 包含课程主题、模块名称，作为开篇引入
- 第2张：**知识点页** — 前半部分核心概念/原理
- 第3张：**知识点页** — 后半部分核心概念/原理/计算
- 第4张：**总结页** — 代码实操/互动练习/课程总结

## ⚠️ 提示词写作核心规则

提示词将直接输入豆包Seedream文生图模型，必须严格遵循以下规则：

1. **PPT风格明确**：每条提示词必须指定"简约工科风教学PPT"风格
2. **版式描述清晰**：描述整体布局（如"左侧文字区域+右侧插画"、"居中大字标题+下方分栏"）
3. **配色方案具体**：指定配色（如"科技蓝渐变背景"、"蓝白灰配色"、"暖色橙红点缀"）
4. **设计风格统一**：扁平化设计、高清质感、极简风格、无多余装饰
5. **文字极简**：画面中只保留关键标题或3-5个关键词标签，不要出现大段文字
6. **适合教学**：图片用于课堂投影演示，必须清晰、专业、学术
7. **无水印**：明确标注"无水印"

## 提示词模板参考

### 封面页模板
"简约工科风教学PPT封面，{背景描述}，{装饰元素}，居中大字标题"{课程标题}"，副标题"{副标题}"，干净极简，高清质感，扁平化设计，无多余文字，适合课堂教学演示，无水印"

### 知识点页模板
"工科教学PPT页面，{版式描述}，{内容描述（图标/示意图/公式等视觉元素）}，{配色方案}，学术严谨风格，高清扁平化，无水印"

### 计算教学页模板
"工科数学教学PPT页面，极简白底，清晰排版{公式/矩阵等}，{示意图描述}，{重点标注描述}，高清，学术严谨，无多余装饰，无水印"

### 实操总结页模板
"编程教学+课程总结PPT页面，分栏版式，{左栏内容描述}，{右栏内容描述}，{装饰元素}，{配色方案}，极简教学风，高清清晰，版式整洁舒适，无水印"

## 输出格式（严格遵守JSON）

```json
{
  "module_title": "模块名称",
  "sections": [
    {
      "section_name": "段落名称（如：课程导入 & 基础认知）",
      "content_summary": "该段落包含的课堂内容摘要（1-2句话）",
      "key_points": ["知识点1", "知识点2", "知识点3"]
    }
  ],
  "boards": [
    {
      "trigger_keywords": ["关键词1", "关键词2"],
      "title": "幻灯片标题",
      "type": "cover | content | calculation | summary",
      "content": "幻灯片核心知识点概述（简短，用于前端文字回退展示）",
      "image_prompt": "完整的PPT生图提示词（100-200字，详细描述画面布局、风格、配色、视觉元素）",
      "position": 0.0
    }
  ]
}
```

## 字段说明

- sections: 模块内容拆分分析（4个段落），帮助你梳理思路
- boards: 最终4张PPT的配置
- type: 必须是以下之一：
  - "cover" - 封面页
  - "content" - 知识点内容页
  - "calculation" - 计算/公式教学页
  - "summary" - 总结/实操页
- image_prompt: **最核心的字段**！直接输入文生图模型的提示词
- position: 0.0, 0.3, 0.6, 0.9（4张PPT均匀分布）

## 重要

- 只输出JSON，不要输出任何其他文字
- 确保 JSON 格式合法
- 必须生成4张PPT（1封面+2知识点+1总结）
- image_prompt 必须是专业PPT风格的画面描述
- ❌ 绝对不要在image_prompt中出现"1. 2. 3. 4."编号列表
- ❌ 绝对不要让image_prompt变成纯文字排版描述"""


async def generate_boards_for_module(
    module_name: str,
    module_content: str,
    key_points: list,
    duration: int = 20
) -> Optional[Dict]:
    """
    为一个模块生成4张PPT风格板书
    """
    try:
        llm = _get_llm()
        from langchain_core.messages import HumanMessage, SystemMessage

        content_preview = module_content[:4000] if len(module_content) > 4000 else module_content

        user_msg = f"""请为以下课堂内容设计4张PPT幻灯片（1封面+2知识点+1总结）：

模块名称：{module_name}
时长：{duration}分钟
核心知识点：{', '.join(key_points[:8])}

教师讲授内容：
---
{content_preview}
---

⚠️ 提醒：
- 先分析拆分模块内容为4个段落
- 每个段落的image_prompt必须是专业PPT风格的画面描述
- 封面页要有课程标题和副标题
- 知识点页要有具体的视觉元素描述
- 总结页要包含实操/代码/总结元素
- 所有提示词必须适合豆包Seedream模型生成"""

        response = await llm.ainvoke([
            SystemMessage(content=BOARD_SYSTEM_PROMPT),
            HumanMessage(content=user_msg)
        ])

        result_text = response.content if hasattr(response, 'content') else str(response)

        boards_data = _parse_boards_json(result_text)
        if boards_data:
            boards = boards_data.get('boards', [])
            # 确保恰好4张
            if len(boards) > 4:
                logger.info(f"板书数量{len(boards)}超过4张，截取前4张")
                boards_data['boards'] = boards[:4]
            elif len(boards) < 4:
                logger.info(f"板书数量{len(boards)}不足4张，补充默认板书")
                while len(boards_data['boards']) < 4:
                    boards_data['boards'].append(_auto_board(len(boards_data['boards']), module_name, 4))

            # 确保 position 均匀分布
            total = len(boards_data['boards'])
            for i, board in enumerate(boards_data['boards']):
                board['position'] = round(i / (total - 1) * 0.9, 2) if total > 1 else 0.0
                # 确保 image_prompt 存在
                if not board.get('image_prompt'):
                    board['image_prompt'] = _auto_image_prompt(board, module_name)

            logger.info(f"Generated {len(boards_data['boards'])} PPT boards for module '{module_name}'")
            return boards_data

        logger.warning(f"Failed to parse boards JSON for module '{module_name}'")
        return None

    except Exception as e:
        logger.error(f"Board generation failed for module '{module_name}': {e}", exc_info=True)
        return None


def _auto_board(index: int, module_name: str, total: int) -> dict:
    """为缺失的板书位置生成默认结构"""
    types = ['cover', 'content', 'content', 'summary']
    titles = ['课程导入', '核心概念', '深入讲解', '课程总结']
    return {
        "trigger_keywords": [module_name],
        "title": titles[index] if index < 4 else f"知识点{index+1}",
        "type": types[index] if index < 4 else "content",
        "content": f"{module_name} - {titles[index] if index < 4 else '知识点'}",
        "image_prompt": _auto_image_prompt({"type": types[index] if index < 4 else "content"}, module_name),
        "position": round(index / (total - 1) * 0.9, 2) if total > 1 else 0.0
    }


def _auto_image_prompt(board: dict, module_name: str = "课程") -> str:
    """为缺少image_prompt的板书自动生成PPT风格提示词"""
    board_type = board.get('type', 'content')
    title = board.get('title', module_name)

    prompts = {
        'cover': (
            f'简约工科风教学PPT封面，科技蓝渐变背景，线条几何元素装饰，'
            f'居中大字标题"{title}"，副标题"{module_name}"，'
            f'干净极简，高清质感，扁平化设计，适合课堂教学演示，无水印'
        ),
        'content': (
            f'工科教学PPT页面，白底简约版式，左侧文字排版区域，右侧扁平化插画，'
            f'画面包含"{title}"相关的图标和示意图元素，'
            f'配色清爽蓝白灰，学术严谨风格，高清扁平化，无水印'
        ),
        'calculation': (
            f'工科数学教学PPT页面，极简白底，清晰排版公式和计算步骤，'
            f'搭配示意图标注，蓝灰色重点标注，高清，学术严谨，无多余装饰，无水印'
        ),
        'summary': (
            f'课程总结PPT页面，分栏版式，左侧展示知识点总结清单，'
            f'右侧展示思维导图或要点图标，蓝白主色调，极简教学风，高清清晰，无水印'
        ),
    }
    return prompts.get(board_type, prompts['content'])


def _parse_boards_json(text: str) -> Optional[Dict]:
    """解析LLM输出的板书JSON"""
    import re

    try:
        data = json.loads(text)
        if _validate_boards(data):
            return data
    except json.JSONDecodeError:
        pass

    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if json_match:
        try:
            data = json.loads(json_match.group(1).strip())
            if _validate_boards(data):
                return data
        except json.JSONDecodeError:
            pass

    start = text.find('{')
    end = text.rfind('}')
    if start >= 0 and end > start:
        try:
            data = json.loads(text[start:end+1])
            if _validate_boards(data):
                return data
        except json.JSONDecodeError:
            pass

    return None


def _validate_boards(data: Dict) -> bool:
    """验证板书数据结构"""
    if not isinstance(data, dict):
        return False
    boards = data.get('boards', [])
    if not isinstance(boards, list) or len(boards) == 0:
        return False

    required_fields = {'trigger_keywords', 'title', 'type', 'content', 'position'}
    valid_types = {'cover', 'content', 'calculation', 'summary'}

    for board in boards:
        if not isinstance(board, dict):
            return False
        if not required_fields.issubset(board.keys()):
            return False
        if board['type'] not in valid_types:
            # 尝试映射旧类型
            old_type_map = {'outline': 'content', 'diagram': 'content', 'illustration': 'content', 'summary': 'summary'}
            board['type'] = old_type_map.get(board['type'], 'content')

        if 'image_prompt' not in board or not board['image_prompt']:
            board['image_prompt'] = _auto_image_prompt(board)

    boards.sort(key=lambda b: b.get('position', 0.5))
    data['boards'] = boards

    return True


def match_board_by_progress(boards: List[Dict], progress: float) -> Optional[Dict]:
    """根据教学进度（0.0-1.0）匹配当前应展示的PPT"""
    if not boards:
        return None

    matched = boards[0]
    for board in boards:
        if board.get('position', 0) <= progress:
            matched = board
        else:
            break

    return matched


def match_board_by_text(boards: List[Dict], text: str) -> Optional[Dict]:
    """根据当前讲到的文本内容匹配PPT"""
    if not boards:
        return None

    best_board = None
    best_score = 0

    text_lower = text.lower()

    for board in boards:
        keywords = board.get('trigger_keywords', [])
        score = sum(1 for kw in keywords if kw.lower() in text_lower)
        if score > best_score:
            best_score = score
            best_board = board

    if best_score > 0:
        return best_board

    return None
