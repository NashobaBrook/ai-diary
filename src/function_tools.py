"""AI Diary - Function Call 工具定义 (V0.0.5 - 重构版)"""
import json
import asyncio
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass

from config import DATA_DIR, CONFIG_DIR, INDEX_DIR
from utils import (
    get_conversation as utils_get_conversation,
    save_diary as utils_save_diary,
    decrypt_api_key,
    parse_date_range,
    encrypt_api_key
)
from logger import get_logger
from retrieval.diary_retriever import _extract_entities, _detect_topic, DiaryIndexer

# 日志
logger = get_logger("ai-diary.function_tools")


# ========== Function Call 格式定义 ==========

# OpenAI 格式
RETRIEVE_FUNCTION_OPENAI = {
    "type": "function",
    "function": {
        "name": "retrieve_diaries",
        "description": "根据用户描述的内容，提取关键词，检索相关历史日记。当用户提到人名、事件、情绪（如被气到、开心、难过）或询问历史记录时，主动调用此函数获取相关背景信息。",
        "parameters": {
            "type": "object",
            "properties": {
                "date_range": {
                    "type": "string",
                    "description": "日期范围，格式如 '2024-02-24' 或 '2024-02-20至2024-02-25'，可选"
                },
                "query": {
                    "type": "string",
                    "description": "检索关键词，可以是单个词或多个词（用逗号分隔），如'赵璐'或'赵璐,气到,就业'"
                }
            }
        }
    }
}

GENERATE_DIARY_FUNCTION_OPENAI = {
    "type": "function",
    "function": {
        "name": "generate_diary",
        "description": "根据当前对话生成或重新生成日记。当用户说'生成日记'、'保存日记'、'帮我写日记'或表达要结束对话并生成日记时，调用此函数。",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "日记日期，格式为 YYYY-MM-DD，默认为今天"
                }
            }
        }
    }
}

# Anthropic/MiniMax 格式
RETRIEVE_FUNCTION_ANTHROPIC = {
    "name": "retrieve_diaries",
    "description": "根据用户描述的内容，提取关键词，检索相关历史日记。当用户提到人名、事件、情绪（如被气到、开心、难过）或询问历史记录时，主动调用此函数获取相关背景信息。",
    "input_schema": {
        "type": "object",
        "properties": {
            "date_range": {
                "type": "string",
                "description": "日期范围，格式如 '2024-02-24' 或 '2024-02-20至2024-02-25'，可选"
            },
            "query": {
                "type": "string",
                "description": "检索关键词，可以是单个词或多个词（用逗号分隔），如'赵璐'或'赵璐,气到,就业'"
            }
        }
    }
}

GENERATE_DIARY_FUNCTION_ANTHROPIC = {
    "name": "generate_diary",
    "description": "根据当前对话生成或重新生成日记。当用户说'生成日记'、'保存日记'、'帮我写日记'或表达要结束对话并生成日记时，调用此函数。",
    "input_schema": {
        "type": "object",
        "properties": {
            "date": {
                "type": "string",
                "description": "日记日期，格式为 YYYY-MM-DD，默认为今天"
            }
        }
    }
}


def get_functions_for_provider(provider: str = "", base_url: str = "") -> List[Dict[str, Any]]:
    """根据 provider 选择合适的 Function Call 格式

    Args:
        provider: 提供商名称
        base_url: API 地址

    Returns:
        符合对应 API 格式的 functions 列表
    """
    provider_lower = (provider + base_url).lower()

    if "minimax" in provider_lower:
        return [RETRIEVE_FUNCTION_ANTHROPIC, GENERATE_DIARY_FUNCTION_ANTHROPIC]

    return [RETRIEVE_FUNCTION_OPENAI, GENERATE_DIARY_FUNCTION_OPENAI]


# 兼容旧接口
RETRIEVE_FUNCTION = RETRIEVE_FUNCTION_ANTHROPIC
GENERATE_DIARY_FUNCTION = GENERATE_DIARY_FUNCTION_ANTHROPIC
AVAILABLE_FUNCTIONS = [RETRIEVE_FUNCTION_ANTHROPIC, GENERATE_DIARY_FUNCTION_ANTHROPIC]


# ========== 停用词 ==========

STOP_WORDS = {
    '的', '是', '了', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
    '你', '会', '着', '没有', '看', '好', '自己', '这', '我们', '他', '她', '它', '吗', '呢', '吧', '啊', '呀', '哦', '嗯',
    '什么', '这个', '那个', '可以', '这样', '那样', '然后', '但是', '所以', '因为', '如果', '就是', '还是', '或者', '而且',
    '不过', '已经', '这些', '那些', '他们', '她们', '它们', '我们', '我的', '你的', '他的', '她的', '它的', '自己',
    '今天', '明天', '昨天', '现在', '时候', '地方', '东西', '事情', '问题', '答案', '感觉', '觉得', '知道', '看到',
    '听到', '想到', '开始', '结束', '起来', '出来', '回来', '过来', '下去', '上去'
}


# ========== 辅助函数 ==========

def get_diary_in_range(start_date: str, end_date: Optional[str] = None) -> List[tuple]:
    """获取日期范围内的日记

    Args:
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        [(日期, 内容), ...] 列表
    """
    diaries = []
    diaries_dir = DATA_DIR / "diaries" / "default"

    if not diaries_dir.exists():
        return diaries

    for f in sorted(diaries_dir.glob("*.json"), reverse=True):
        date_str = f.stem
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")

            if start_date:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                if dt < start_dt:
                    continue

            if end_date:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                if dt > end_dt:
                    continue

            with open(f, encoding="utf-8") as file:
                diary = json.load(file)
                diaries.append((date_str, diary.get("content", "")))
        except (ValueError, json.JSONDecodeError) as e:
            logger.warning("default", "READ_DIARY_ERROR", f"{f.name}: {e}")

    return diaries


def get_user_config(user_id: str) -> Dict[str, Any]:
    """获取用户配置（兼容旧接口）"""
    from utils import get_user_config as _get_user_config
    cfg = _get_user_config(user_id)
    if cfg.get("api_key"):
        cfg["api_key"] = decrypt_api_key(cfg["api_key"])
    return cfg


# ========== Function Call 处理 ==========

async def handle_function_call(
    function_name: str,
    arguments: Dict[str, Any],
    context_builder
) -> str:
    """处理 Function Call

    Args:
        function_name: 函数名
        arguments: 函数参数
        context_builder: 上下文构建器

    Returns:
        函数执行结果
    """
    user_id = getattr(context_builder, "user_id", "default")

    if function_name == "retrieve_diaries":
        return await _handle_retrieve_diaries(user_id, arguments, context_builder)

    if function_name == "generate_diary":
        return await _handle_generate_diary(user_id, arguments)

    return f"未知函数: {function_name}"


async def _handle_retrieve_diaries(
    user_id: str,
    arguments: Dict[str, Any],
    context_builder
) -> str:
    """处理日记检索

    Args:
        user_id: 用户ID
        arguments: 函数参数
        context_builder: 上下文构建器

    Returns:
        检索结果
    """
    date_range = arguments.get("date_range", "")
    query = arguments.get("query", "").strip()

    if not date_range and not query:
        return "请提供日期范围或查询关键词。"

    start_date, end_date = parse_date_range(date_range)

    # 如果有日期范围，获取该范围内的日记
    if start_date:
        diaries = get_diary_in_range(start_date, end_date)

        if not diaries:
            return f"未找到{date_range}的日记记录。"

        if not query:
            parts = []
            for date_str, content in diaries:
                try:
                    dt = datetime.strptime(date_str, "%Y-%m-%d")
                    formatted_date = dt.strftime("%Y年%m月%d日")
                except ValueError:
                    formatted_date = date_str
                parts.append(f"【{formatted_date}】\n{content}")
            return "\n\n".join(parts)

        # 处理多个关键词
        query_normalized = query.replace("，", ",").replace(",", " ")

        # 构建检索上下文
        current_message = getattr(context_builder, "current_message", "") or ""
        context = {
            "query": current_message,
            "mentioned_entities": _extract_entities(current_message),
            "current_topic": _detect_topic(current_message)
        }
        results = context_builder.indexer.search_with_context(query_normalized, context, top_k=5)

        # 过滤日期范围
        filtered_results = []
        for r in results:
            try:
                dt = datetime.strptime(r["date"], "%Y-%m-%d")
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")

                if end_date:
                    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                    if start_dt <= dt <= end_dt:
                        filtered_results.append(r)
                else:
                    if dt == start_dt:
                        filtered_results.append(r)
            except ValueError:
                pass

        if not filtered_results:
            return f"在{date_range}未找到与'{query}'相关的日记记录。"

        # 构建返回结果
        parts = []
        for r in filtered_results:
            try:
                dt = datetime.strptime(r["date"], "%Y-%m-%d")
                formatted_date = dt.strftime("%Y年%m月%d日")
            except ValueError:
                formatted_date = r["date"]

            summary = r.get("summary", "") or r["content"][:100]
            entry = f"""【{formatted_date}】(相关性: {r["score"]})
摘要: {summary}
全文: {r["content"]}"""
            parts.append(entry)

        return "\n\n---\n\n".join(parts)

    # 没有日期范围，执行全局关键词搜索
    query_normalized = query.replace("，", ",").replace(",", " ")

    current_message = getattr(context_builder, "current_message", "") or ""
    context = {
        "query": current_message,
        "mentioned_entities": _extract_entities(current_message),
        "current_topic": _detect_topic(current_message)
    }
    results = context_builder.indexer.search_with_context(query_normalized, context, top_k=5)

    if not results:
        return "未找到相关日记记录。"

    parts = []
    for r in results:
        try:
            dt = datetime.strptime(r["date"], "%Y-%m-%d")
            formatted_date = dt.strftime("%Y年%m月%d日")
        except ValueError:
            formatted_date = r["date"]

        summary = r.get("summary", "") or r["content"][:100]
        entry = f"""【{formatted_date}】(相关性: {r["score"]})
摘要: {summary}
全文: {r["content"]}"""
        parts.append(entry)

    return "\n\n---\n\n".join(parts)


async def _handle_generate_diary(user_id: str, arguments: Dict[str, Any]) -> str:
    """处理日记生成

    Args:
        user_id: 用户ID
        arguments: 函数参数

    Returns:
        生成结果
    """
    from datetime import date as date_type
    from llm import LLMClient
    from writing_style import get_writing_style

    date_str = arguments.get("date", "")
    target_date = date_str or date_type.today().isoformat()

    # 生成日记文本和摘要
    result = await generate_diary_text(user_id, target_date)

    if not result.get("success"):
        return f"生成日记失败：{result.get('error', '未知错误')}"

    diary_content = result["content"]
    diary_summary = result.get("summary", "")

    # 评估心情
    conversation = utils_get_conversation(user_id, target_date)
    conversation_text = "\n".join([f"{'用户' if m['role'] == 'user' else '小年'}: {m['content']}" for m in conversation])

    mood = await evaluate_mood(conversation_text, user_id)
    tags = extract_tags(conversation_text, user_id)
    current_topic = _detect_topic(conversation_text)

    # 构建日记数据
    diary_data = {
        "date": target_date,
        "content": diary_content,
        "mood": {
            "level": mood["level"],
            "name": mood["name"],
            "description": mood["description"]
        },
        "tags": tags,
        "created_at": datetime.now().isoformat()
    }

    # 保存日记
    utils_save_diary(user_id, diary_data)

    # 添加到索引
    add_diary_to_index(user_id, target_date, diary_content, diary_summary, current_topic, mood["level"])

    # 异步更新用户画像
    llm_client = get_llm_client(user_id)
    asyncio.create_task(_update_profile_async(user_id, target_date, llm_client))

    return f"日记已成功生成并保存！\n\n【{target_date}】\n{diary_content}"


def should_use_functions(message: str) -> bool:
    """快速判断是否应该启用 Function Call

    Args:
        message: 用户消息

    Returns:
        是否启用 Function Call
    """
    # 情绪相关关键词
    emotion_keywords = [
        "气到", "生气", "开心", "难过", "伤心", "委屈", "郁闷",
        "激动", "紧张", "焦虑", "担心", "害怕", "失望",
        "兴奋", "平静", "疲惫", "烦躁", "后悔", "内疚"
    ]

    # 询问历史相关
    history_keywords = [
        "之前", "以前", "上次", "那天", "记得", "日记",
        "之前说过", "上次提到", "以前说", "之前聊",
        "上个月", "上周", "昨天", "前几天"
    ]

    # 事件/项目相关
    event_keywords = [
        "那个项目", "那件事", "那个人", "关于", "讨论",
        "提到", "说到", "谈到"
    ]

    # 生成日记相关
    generate_keywords = [
        "生成日记", "保存日记", "帮我写日记", "写日记", "记录日记",
        "结束", "就这样", "今天就到这里", "好了", "完了"
    ]

    message_lower = message.lower()

    if any(keyword in message_lower for keyword in emotion_keywords):
        return True
    if any(keyword in message_lower for keyword in history_keywords):
        return True
    if any(keyword in message_lower for keyword in event_keywords):
        return True

    # 检查是否提到人名
    chinese_names = re.findall(r'[\u4e00-\u9fa5]{2,4}', message)
    if chinese_names:
        return True

    if any(keyword in message_lower for keyword in generate_keywords):
        return True

    return False


# ========== 日记生成相关 ==========

async def generate_diary_text(user_id: str, target_date: str) -> Dict[str, Any]:
    """生成日记文本和摘要

    Args:
        user_id: 用户ID
        target_date: 目标日期

    Returns:
        包含 content 和 summary 的字典
    """
    from llm import LLMClient
    from writing_style import get_writing_style

    conversation = utils_get_conversation(user_id, target_date)
    user_msgs = [m for m in conversation if m["role"] == "user"]

    if not user_msgs:
        return {"success": False, "error": "没有对话内容，无法生成日记"}

    user_content = "\n".join(f"- {m['content']}" for m in user_msgs)

    # 从写作风格获取提示
    style_prompt = get_writing_style(user_id)

    prompt = f"""请根据以下内容生成日记：

{user_content}{style_prompt}

日期：{target_date}

直接输出日记正文（不要有任何说明文字）："""

    try:
        llm = LLMClient(user_id)

        # 并行生成日记正文和摘要
        diary_task = llm.chat([
            {"role": "system", "content": "你是一位专业的日记编辑，整理用户分享的内容生成连贯日记。" + ("请模仿用户写作风格。" if style_prompt else "")},
            {"role": "user", "content": prompt}
        ])

        summary_prompt = f"""请为以下日记生成一句话摘要（30字以内），概括这一天最重要的内容：

{user_content}

只输出摘要，不要其他内容："""

        summary_task = llm.chat([
            {"role": "system", "content": "你是一位日记摘要专家。"},
            {"role": "user", "content": summary_prompt}
        ])

        diary_result, summary_result = await asyncio.gather(diary_task, summary_task)

        if isinstance(diary_result, dict) and "code" in diary_result:
            return {"success": False, "error": diary_result.get("message", "生成失败")}

        # 清理摘要
        summary = summary_result.strip().strip('"').strip("'") if summary_result else ""

        return {"success": True, "content": diary_result, "summary": summary}
    except Exception as e:
        logger.error(user_id, "GENERATE_DIARY_FAILED", str(e))
        return {"success": False, "error": str(e)}


def add_diary_to_index(
    user_id: str,
    diary_date: str,
    content: str,
    summary: str = "",
    topic: Optional[str] = None,
    mood_level: int = 3
) -> None:
    """添加日记到检索索引

    Args:
        user_id: 用户ID
        diary_date: 日记日期
        content: 日记内容
        summary: 摘要
        topic: 主题
        mood_level: 心情等级
    """
    indexer = DiaryIndexer(user_id)
    indexer.index_diary(diary_date, content, summary, topic, mood_level)


# ========== 心情评估 ==========

@dataclass
class Mood:
    """心情数据"""
    level: int
    name: str
    description: str


def get_llm_client(user_id: str):
    """获取 LLM 客户端"""
    from llm import LLMClient
    return LLMClient(user_id)


async def evaluate_mood(conversation_text: str, user_id: str) -> Dict[str, Any]:
    """评估当天心情

    Args:
        conversation_text: 对话文本
        user_id: 用户ID

    Returns:
        心情字典
    """
    mood_prompt = f"""基于以下当天对话内容，评估用户当天的心情等级。

对话内容：
{conversation_text}

心情等级定义：
1 - 沮丧：情绪低落，可能遇到挫折或困难
2 - 不高兴：心情不太好，有些烦恼
3 - 正常：情绪平稳，没有特别波动
4 - 有点喜悦：心情不错，有开心的事情
5 - 超开心：非常愉快，可能有好消息或好事发生

请输出 JSON 格式：
{{
    "level": 1-5,
    "name": "对应等级名称",
    "description": "一句话描述当天心情"
}}

只输出 JSON，不要其他内容。"""

    try:
        llm = get_llm_client(user_id)
        result = await llm.chat([
            {"role": "system", "content": "你是一位情绪分析专家。"},
            {"role": "user", "content": mood_prompt}
        ])

        if isinstance(result, dict) and "code" in result:
            return {"level": 3, "name": "正常", "description": "情绪平稳"}

        json_match = re.search(r'\{[^}]+\}', result)
        if json_match:
            mood_data = json.loads(json_match.group())
            return {
                "level": mood_data.get("level", 3),
                "name": mood_data.get("name", "正常"),
                "description": mood_data.get("description", "情绪平稳")
            }
    except Exception as e:
        logger.error(user_id, "EVALUATE_MOOD_FAILED", str(e))

    return {"level": 3, "name": "正常", "description": "情绪平稳"}


def extract_tags(conversation_text: str, user_id: str = "default") -> List[str]:
    """提取日记标签

    Args:
        conversation_text: 对话文本
        user_id: 用户ID

    Returns:
        标签列表
    """
    tag_prompt = f"""基于以下对话内容，提取 3-5 个关键词作为日记标签。

对话内容：
{conversation_text}

要求：
1. 标签应该概括对话主题
2. 可以是：工作、情感、健康、运动、学习、旅行等
3. 输出格式：tag1, tag2, tag3

只输出标签，用逗号分隔，不要其他内容。"""

    try:
        llm = get_llm_client(user_id)
        result = llm.generate_text(tag_prompt)
        tags = [tag.strip() for tag in result.split(",") if tag.strip()]
        return tags[:5]
    except Exception as e:
        logger.error(user_id, "EXTRACT_TAGS_FAILED", str(e))
        return []


async def _update_profile_async(user_id: str, target_date: str, llm_client) -> None:
    """异步更新用户画像

    Args:
        user_id: 用户ID
        target_date: 目标日期
        llm_client: LLM 客户端
    """
    try:
        from user_profile import UserProfileManager

        profile_manager = UserProfileManager(user_id)

        # 获取对话内容
        conversation = utils_get_conversation(user_id, target_date)
        conversation_text = "\n".join([f"{'用户' if m['role'] == 'user' else '小年'}: {m['content']}" for m in conversation])

        if not conversation_text:
            return

        # 在后台线程中执行更新
        await asyncio.to_thread(profile_manager.update, conversation_text, llm_client)
    except Exception as e:
        logger.error(user_id, "UPDATE_PROFILE_FAILED", str(e))
