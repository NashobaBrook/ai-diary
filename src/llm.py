"""AI Diary - LLM 接入层 (V0.0.5 - 重构版)"""
import json
import time
import asyncio
import httpx
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import AsyncOpenAI

from config import CONFIG_DIR, DATA_DIR, LOG_DIR, BIANNIAN_DIR
from utils import (
    get_user_config,
    save_user_config,
    get_conversation as utils_get_conversation,
    save_message as utils_save_message,
    get_diary as utils_get_diary,
    save_diary as utils_save_diary,
    list_diaries as utils_list_diaries,
    decrypt_api_key,
    is_garbage_message
)
from logger import get_logger
from function_tools import (
    AVAILABLE_FUNCTIONS,
    handle_function_call,
    should_use_functions,
    get_functions_for_provider
)
from writing_style import WritingStyleManager, get_writing_style

# 日志
logger = get_logger("ai-diary.llm")


# ========== 错误码 ==========

class Err:
    """错误码定义"""
    CONFIG_NOT_FOUND = (4001, "请先配置 LLM")
    NOT_FOUND = (4003, "内容不存在")
    LLM_FAILED = (5001, "AI 服务调用失败")

    @staticmethod
    def msg(code) -> Dict[str, Any]:
        if isinstance(code, tuple):
            return {"code": code[0], "message": code[1]}
        return {"code": code, "message": "成功" if code == 0 else "错误"}


# ========== 配置缓存 ==========

_config_cache: Dict[str, Dict[str, Any]] = {}
_cache_time: Dict[str, float] = {}


def get_user_config_cached(user_id: str) -> Dict[str, Any]:
    """获取用户配置（带缓存）

    Args:
        user_id: 用户ID

    Returns:
        用户配置字典
    """
    now = time.time()
    if user_id in _config_cache and now - _cache_time.get(user_id, 0) < 300:
        return _config_cache[user_id]

    cfg = get_user_config(user_id)
    if cfg.get("api_key"):
        cfg["api_key"] = decrypt_api_key(cfg["api_key"])
        logger.info(user_id, "API_KEY_LOADED", f"decrypted={cfg['api_key'][:20]}...")

    _config_cache[user_id] = cfg
    _cache_time[user_id] = now
    return cfg


def invalidate_config_cache(user_id: str) -> None:
    """使配置缓存失效

    Args:
        user_id: 用户ID
    """
    _config_cache.pop(user_id, None)
    _cache_time.pop(user_id, None)


def save_user_config_with_cache(user_id: str, config: Dict[str, Any]) -> None:
    """保存用户配置（使缓存失效）

    Args:
        user_id: 用户ID
        config: 配置字典
    """
    save_user_config(user_id, config)
    invalidate_config_cache(user_id)


# ========== 存储函数 ==========

def get_conversation(user_id: str, d: Optional[str] = None) -> List[Dict[str, str]]:
    """获取对话记录

    Args:
        user_id: 用户ID
        d: 日期字符串，默认为今天

    Returns:
        消息列表
    """
    return utils_get_conversation(user_id, d)


def save_message(user_id: str, role: str, content: str, msg_date: Optional[str] = None) -> None:
    """保存对话消息

    Args:
        user_id: 用户ID
        role: 角色 (user/assistant)
        content: 消息内容
        msg_date: 日期字符串，默认为今天
    """
    utils_save_message(user_id, role, content, msg_date)


def save_diary(user_id: str, diary: Dict[str, Any]) -> None:
    """保存日记

    Args:
        user_id: 用户ID
        diary: 日记字典
    """
    utils_save_diary(user_id, diary)
    logger.info(user_id, "DIARY_SAVED", diary.get("date", "unknown"))


def get_diary(user_id: str, d: str) -> Optional[Dict[str, Any]]:
    """获取日记

    Args:
        user_id: 用户ID
        d: 日期字符串

    Returns:
        日记字典
    """
    return utils_get_diary(user_id, d)


def get_diaries(user_id: str) -> List[str]:
    """列出用户所有日记日期

    Args:
        user_id: 用户ID

    Returns:
        日期字符串列表（降序）
    """
    return utils_list_diaries(user_id)


def get_stats(user_id: str) -> Dict[str, Any]:
    """获取统计数据

    Args:
        user_id: 用户ID

    Returns:
        统计数据字典
    """
    diaries = get_diaries(user_id)
    this_month = date.today().isoformat()[:7]

    # 计算心情分布
    mood_distribution: Dict[str, int] = {}
    diaries_dir = DATA_DIR / "diaries" / user_id
    if diaries_dir.exists():
        for diary_file in diaries_dir.glob("*.json"):
            try:
                with open(diary_file, encoding="utf-8") as f:
                    diary = json.load(f)
                    if "mood" in diary:
                        mood_name = diary["mood"].get("name", "正常")
                        mood_distribution[mood_name] = mood_distribution.get(mood_name, 0) + 1
            except Exception as e:
                logger.warning(user_id, "STATS_READ_ERROR", str(e))

    return {
        "total_diaries": len(diaries),
        "this_month_count": sum(1 for d in diaries if d.startswith(this_month)),
        "mood_distribution": mood_distribution
    }


# ========== System Prompt 加载 ==========

def load_system_prompt() -> str:
    """加载 system prompt

    Returns:
        System prompt 字符串
    """
    system_prompt = ""
    try:
        for f in ["diary-soul.md", "dialogue.md"]:
            file_path = BIANNIAN_DIR / f
            if file_path.exists():
                system_prompt += f"# {f}\n{file_path.read_text(encoding='utf-8')}\n\n"
    except Exception as e:
        logger.warning("system", "LOAD_PROMPT_FAILED", str(e))
        system_prompt = "你是小年，一位温暖的编年日记助手。"

    return system_prompt


SYSTEM_PROMPT = load_system_prompt()


# ========== LLM 客户端 ==========

class LLMClient:
    """LLM 客户端封装"""

    def __init__(self, user_id: str):
        self.user_id = user_id

    async def chat(self, messages: List[Dict[str, str]]) -> str:
        """普通对话

        Args:
            messages: 消息列表

        Returns:
            AI 回复内容
        """
        cfg = get_user_config_cached(self.user_id)
        if not cfg.get("api_key"):
            return Err.msg(Err.CONFIG_NOT_FOUND)

        if "minimax" in cfg.get("provider", "").lower() or "minimaxi" in cfg.get("base_url", ""):
            return await self._chat_minimax(messages, cfg)

        try:
            client = AsyncOpenAI(api_key=cfg["api_key"], base_url=cfg.get("base_url") or None)
            params = {"model": cfg.get("model", "gpt-3.5-turbo"), "temperature": 0.8}
            if cfg.get("thinking"):
                params["extra_body"] = {"thinking": {"type": "continuous"}}

            rsp = await client.chat.completions.create(messages=messages, **params)
            logger.info(self.user_id, "LLM_SUCCESS", f"model={cfg.get('model')}")
            return rsp.choices[0].message.content
        except Exception as e:
            logger.error(self.user_id, "LLM_FAILED", str(e)[:200])
            return Err.msg(Err.LLM_FAILED)

    async def chat_with_functions(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict[str, Any]]] = None,
        agent=None
    ) -> Dict[str, Any]:
        """支持 Function Call 的对话

        Args:
            messages: 消息列表
            functions: 可用函数列表
            agent: Agent 实例（用于获取 context_builder）

        Returns:
            包含回复内容的字典
        """
        cfg = get_user_config_cached(self.user_id)
        if not cfg.get("api_key"):
            return {"error": Err.msg(Err.CONFIG_NOT_FOUND)}

        # MiniMax 使用 Anthropic API 格式
        if "minimax" in cfg.get("provider", "").lower() or "minimaxi" in cfg.get("base_url", ""):
            return await self._chat_minimax_with_functions(messages, functions, cfg, agent)

        # OpenAI 兼容格式
        try:
            client = AsyncOpenAI(api_key=cfg["api_key"], base_url=cfg.get("base_url") or None)
            params = {
                "model": cfg.get("model", "gpt-3.5-turbo"),
                "temperature": 0.8,
                "messages": messages
            }

            if functions:
                params["tools"] = functions
                params["tool_choice"] = "auto"

            rsp = await client.chat.completions.create(**params)
            message = rsp.choices[0].message

            # 检查是否有 function call
            if message.tool_calls:
                tool_call = message.tool_calls[0]
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)

                logger.info(self.user_id, "FUNCTION_CALL", f"{function_name}: {arguments}")

                # 执行 function
                result = await handle_function_call(function_name, arguments, agent.context_builder)

                # 将结果加入上下文
                messages.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [{
                        "id": tool_call.id,
                        "type": "function",
                        "function": {"name": function_name, "arguments": tool_call.function.arguments}
                    }]
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })

                # 第二次调用获取最终回复
                final_rsp = await client.chat.completions.create(
                    model=cfg.get("model", "gpt-3.5-turbo"),
                    temperature=0.8,
                    messages=messages
                )
                return {"content": final_rsp.choices[0].message.content, "function_called": function_name}

            return {"content": message.content}

        except Exception as e:
            logger.error(self.user_id, "LLM_FAILED", str(e)[:200])
            return {"error": Err.msg(Err.LLM_FAILED)}

    async def _chat_minimax(self, messages: List[Dict[str, str]], cfg: Dict[str, Any]) -> str:
        """使用 MiniMax API

        Args:
            messages: 消息列表
            cfg: 配置字典

        Returns:
            AI 回复内容
        """
        url = f"{cfg['base_url']}/v1/messages"
        headers = {
            "x-api-key": cfg['api_key'],
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }

        # 转换消息格式为 Anthropic 格式
        anthropic_messages = []
        system_content = None
        for m in messages:
            if m["role"] == "system":
                system_content = m["content"]
            else:
                anthropic_messages.append({
                    "role": m["role"],
                    "content": [{"type": "text", "text": m["content"]}]
                })

        payload = {
            "model": cfg.get("model", "MiniMax-M2.5"),
            "max_tokens": 4096,
            "messages": anthropic_messages
        }
        if system_content:
            payload["system"] = system_content
        if cfg.get("thinking"):
            payload["thinking"] = {"type": "enabled", "budget_tokens": 1024}

        try:
            async with httpx.AsyncClient() as client:
                rsp = await client.post(url, headers=headers, json=payload, timeout=60)
                data = rsp.json()

                if "error" in data:
                    error_msg = data["error"].get("message", "API 调用失败")
                    logger.error(self.user_id, "MINIMAX_ERROR", error_msg)
                    return ""

                # 解析响应
                content = ""
                if "content" in data:
                    for block in data["content"]:
                        if block.get("type") == "text":
                            content += block.get("text", "")

                if not content:
                    logger.warning(self.user_id, "EMPTY_RESPONSE", f"data={str(data)[:100]}")
                    return ""

                logger.info(self.user_id, "LLM_SUCCESS", f"len={len(content)}")
                return content
        except Exception as e:
            logger.error(self.user_id, "LLM_FAILED", str(e)[:100])
            return Err.msg(Err.LLM_FAILED)

    async def _chat_minimax_with_functions(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict[str, Any]]],
        cfg: Dict[str, Any],
        agent
    ) -> Dict[str, Any]:
        """使用 MiniMax API 支持 Function Call

        Args:
            messages: 消息列表
            functions: 可用函数列表
            cfg: 配置字典
            agent: Agent 实例

        Returns:
            包含回复内容的字典
        """
        url = f"{cfg['base_url']}/v1/messages"
        headers = {
            "x-api-key": cfg['api_key'],
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }

        # 转换消息格式
        anthropic_messages = []
        system_content = None
        for m in messages:
            if m["role"] == "system":
                system_content = m["content"]
            else:
                anthropic_messages.append({
                    "role": m["role"],
                    "content": [{"type": "text", "text": m["content"]}]
                })

        payload = {
            "model": cfg.get("model", "MiniMax-M2.5"),
            "max_tokens": 4096,
            "messages": anthropic_messages
        }
        if system_content:
            payload["system"] = system_content
        if cfg.get("thinking"):
            payload["thinking"] = {"type": "enabled", "budget_tokens": 1024}

        if functions:
            payload["tools"] = functions
            payload["tool_choice"] = {"type": "auto"}

        try:
            async with httpx.AsyncClient() as client:
                rsp = await client.post(url, headers=headers, json=payload, timeout=60)
                data = rsp.json()

                if "error" in data:
                    error_msg = data["error"].get("message", "API 调用失败")
                    logger.error(self.user_id, "MINIMAX_ERROR", error_msg)
                    return {"error": Err.msg(Err.LLM_FAILED)}

                # 解析响应
                content = ""
                has_tool_use = False
                tool_use_block = None

                if "content" in data:
                    for block in data["content"]:
                        block_type = block.get("type")
                        if block_type == "text":
                            content += block.get("text", "")
                        elif block_type == "tool_use":
                            has_tool_use = True
                            tool_use_block = block

                if has_tool_use and tool_use_block:
                    # 执行 function call
                    function_name = tool_use_block.get("name")
                    arguments = tool_use_block.get("input", {})

                    logger.info(self.user_id, "FUNCTION_CALL", f"{function_name}: {arguments}")

                    # 执行 function
                    result = await handle_function_call(function_name, arguments, agent.context_builder)

                    # 构建工具响应
                    anthropic_messages.append({"role": "assistant", "content": data["content"]})
                    anthropic_messages.append({
                        "role": "user",
                        "content": [{
                            "type": "tool_result",
                            "tool_use_id": tool_use_block.get("id"),
                            "content": result
                        }]
                    })

                    # 第二次调用
                    payload2 = {
                        "model": cfg.get("model", "MiniMax-M2.5"),
                        "max_tokens": 4096,
                        "messages": anthropic_messages
                    }
                    if system_content:
                        payload2["system"] = system_content

                    rsp2 = await client.post(url, headers=headers, json=payload2, timeout=60)
                    data2 = rsp2.json()

                    if "error" in data2:
                        error_msg = data2["error"].get("message", "API 调用失败")
                        logger.error(self.user_id, "MINIMAX_ERROR", error_msg)
                        return {"error": Err.msg(Err.LLM_FAILED)}

                    # 解析最终回复
                    final_content = ""
                    if "content" in data2:
                        for block in data2["content"]:
                            if block.get("type") == "text":
                                final_content += block.get("text", "")

                    logger.info(self.user_id, "LLM_SUCCESS", f"len={len(final_content)}")
                    return {"content": final_content, "function_called": function_name}

                if not content:
                    logger.warning(self.user_id, "EMPTY_RESPONSE", f"data={str(data)[:100]}")
                    return {"error": Err.msg(Err.LLM_FAILED)}

                logger.info(self.user_id, "LLM_SUCCESS", f"len={len(content)}")
                return {"content": content}

        except Exception as e:
            logger.error(self.user_id, "LLM_FAILED", str(e)[:200])
            return {"error": Err.msg(Err.LLM_FAILED)}

    def generate_text(self, prompt: str) -> str:
        """同步生成文本（用于心情评估、标签提取等）

        Args:
            prompt: 提示词

        Returns:
            生成文本
        """
        cfg = get_user_config_cached(self.user_id)
        if not cfg.get("api_key"):
            return ""

        try:
            url = "https://api.minimaxi.com/anthropic/v1/messages"
            api_key = decrypt_api_key(cfg["api_key"])

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "x-vm-protocol": "openai"
            }

            payload = {
                "model": cfg.get("model", "MiniMax-M2.5"),
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": prompt}]
            }

            with httpx.Client() as client:
                rsp = client.post(url, headers=headers, json=payload, timeout=30)
                data = rsp.json()

                if "error" in data:
                    logger.error(self.user_id, "GENERATE_FAILED", data["error"].get("message", ""))
                    return ""

                content = ""
                if "content" in data:
                    for block in data["content"]:
                        if block.get("type") == "text":
                            content += block.get("text", "")

                return content
        except Exception as e:
            logger.error(self.user_id, "GENERATE_FAILED", str(e)[:100])
            return ""


# ========== FastAPI 应用 ==========

app = FastAPI()
_agent_cache: Dict[str, Any] = {}


def get_agent(user_id: str):
    """获取 Agent 实例（带缓存）"""
    from agent import DiaryAgent
    if user_id not in _agent_cache:
        _agent_cache[user_id] = DiaryAgent(user_id)
    return _agent_cache[user_id]


# ========== 请求模型 ==========

class ChatReq(BaseModel):
    user_id: str
    message: str
    date: Optional[str] = None


class ConfigReq(BaseModel):
    user_id: str
    provider: str = ""
    base_url: str = ""
    api_key: str = ""
    model: str = ""
    thinking: bool = False


class DiaryUpdateReq(BaseModel):
    content: Optional[str] = None
    mood: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


# ========== API 路由 ==========

@app.post("/chat")
async def chat(req: ChatReq):
    """聊天接口"""
    logger.info(req.user_id, "CHAT_START", req.message[:50])

    target_date = req.date or date.today().isoformat()

    # 检查是否是未来日期
    if target_date > date.today().isoformat():
        return {"code": 4002, "message": "不能记录未来的日记"}

    save_message(req.user_id, "user", req.message, target_date)

    agent = get_agent(req.user_id)

    # 构建上下文
    context = [{"role": "system", "content": agent.build_system_prompt()}]
    recent = agent.memory.get_context_dynamic_for_date(target_date, max_tokens=6000)
    for msg in recent:
        context.append({"role": msg["role"], "content": msg["content"]})
    context.append({"role": "user", "content": req.message})

    # 判断是否启用 Function Call
    enable_functions = should_use_functions(req.message)

    if enable_functions:
        agent.context_builder.current_message = req.message
        cfg = get_user_config_cached(req.user_id)
        functions = get_functions_for_provider(cfg.get("provider", ""), cfg.get("base_url", ""))

        result = await LLMClient(req.user_id).chat_with_functions(
            messages=context,
            functions=functions,
            agent=agent
        )

        if "error" in result:
            return result["error"]

        reply = result.get("content", "")
        if result.get("function_called"):
            logger.info(req.user_id, "RETRIEVAL_USED", f"Function: {result['function_called']}")
    else:
        result = await LLMClient(req.user_id).chat(context)
        if isinstance(result, dict) and "code" in result:
            return result
        reply = result
        if isinstance(reply, str) and ("login fail" in reply or not reply):
            return Err.msg(Err.LLM_FAILED)

    save_message(req.user_id, "assistant", reply, target_date)
    return {"reply": reply}


@app.post("/config")
async def set_config(req: ConfigReq):
    """设置用户配置"""
    config = {k: v.strip().strip("`") if isinstance(v, str) else v for k, v in req.model_dump().items() if k != "user_id"}

    # 如果 api_key 为空，保留原有的加密密钥
    if not config.get("api_key"):
        f = CONFIG_DIR / f"{req.user_id}.json"
        if f.exists():
            raw_cfg = json.load(open(f, encoding="utf-8"))
            if raw_cfg.get("api_key"):
                config["api_key"] = raw_cfg["api_key"]
                logger.info(req.user_id, "CONFIG_SAVE", "preserving existing api_key")

    save_user_config_with_cache(req.user_id, config)
    return {"ok": True, **Err.msg(0)}


@app.get("/config/{user_id}")
async def get_config(user_id: str):
    """获取用户配置"""
    return get_user_config_cached(user_id)


@app.get("/diaries")
async def list_diaries(user_id: str):
    """列出日记"""
    return {"dates": get_diaries(user_id)}


@app.get("/conversation/{d}")
async def get_convo(user_id: str, d: Optional[str] = None):
    """获取对话"""
    return {"date": d or "today", "messages": get_conversation(user_id, d)}


@app.get("/stats")
async def stats(user_id: str):
    """获取统计"""
    return get_stats(user_id)


# ========== 飞书配置接口（暂未开放）==========
# TODO: V0.0.6 实现飞书集成

# @app.get("/feishu/config")
# async def get_feishu_config():
#     """获取飞书配置"""
#     return {"enabled": False, "app_id": "", "app_secret": ""}
#
#
# @app.post("/feishu/config")
# async def set_feishu_config(config: dict):
#     """设置飞书配置"""
#     return {"ok": True, **Err.msg(0)}


# ========== 用户风格接口 ==========

@app.get("/user/style/{user_id}")
async def get_user_style(user_id: str):
    """获取用户写作风格"""
    manager = WritingStyleManager(user_id)
    content = manager.load()
    style = manager.get_style_description()
    return {"style": style, "content": content}


@app.post("/user/style/{user_id}")
async def save_user_style(user_id: str, request: dict):
    """保存用户写作风格"""
    content = request.get("content", "")
    if not content:
        return {"ok": False, "message": "内容不能为空", **Err.msg(1)}

    manager = WritingStyleManager(user_id)
    success = manager.save(content)

    if success:
        return {"ok": True, "message": "保存成功", **Err.msg(0)}
    else:
        return {"ok": False, "message": "保存失败", **Err.msg(1)}


@app.post("/user/analyze-style")
async def analyze_user_style(user_id: str):
    """分析用户写作风格"""
    agent = get_agent(user_id)

    conversations_dir = DATA_DIR / "conversations" / user_id
    if not conversations_dir.exists():
        return {"ok": False, "message": "暂无对话数据", **Err.msg(1)}

    # 获取最近30天的对话
    recent_conversations = []
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    for f in sorted(conversations_dir.glob("*.jsonl"), reverse=True):
        date_str = f.stem
        if date_str < thirty_days_ago:
            continue
        try:
            conv = get_conversation(user_id, date_str)
            user_messages = [{"role": msg["role"], "content": msg["content"]}
                           for msg in conv if msg["role"] == "user"]
            recent_conversations.extend(user_messages)
        except Exception:
            pass

    if len(recent_conversations) < 5:
        return {"ok": False, "message": "对话数据不足", **Err.msg(1)}

    user_texts = "\n\n".join([msg["content"] for msg in recent_conversations[:20]])

    prompt = f"""请分析以下用户的写作风格，并用简洁的语言描述：

{user_texts[:3000]}

请从以下维度分析，用100-200字描述：
1. 语言特点（正式/随意/幽默/感性等）
2. 句式风格（短句/长句/排比等）
3. 表达习惯（喜欢用比喻/直白/含蓄等）
4. 情感倾向（积极/消极/中性等）

只返回风格描述，不要有其他内容。"""

    try:
        client = LLMClient(user_id)
        style = await client.chat([{"role": "system", "content": "你是一个写作风格分析专家。"},
                                   {"role": "user", "content": prompt}])

        if style and not style.startswith("错误"):
            manager = WritingStyleManager(user_id)
            content = f"""# 写作风格

## 风格描述

{style}

## 语言特点

- 整体比较随意、口语化
- 像是朋友间的聊天或自言自语
- 不正式，但也不是完全随意

## 句式风格

- 短句为主
- 有些长句但不多
- 句子之间有些跳跃

## 表达习惯

- 比较直白
- 善于自我对话和反思

## 内容偏好

- 喜欢讨论AI、技术趋势
- 关注个人成长和产品思考
"""
            manager.save(content)
            return {"ok": True, "style": style, **Err.msg(0)}
        else:
            return {"ok": False, "message": "分析失败", **Err.msg(1)}
    except Exception as e:
        logger.error(user_id, "ANALYZE_STYLE_ERROR", str(e))
        return {"ok": False, "message": f"分析失败：{str(e)}", **Err.msg(1)}


# ========== 日历接口 ==========

@app.get("/calendar/{year}/{month}")
async def get_calendar(user_id: str, year: int, month: int):
    """获取指定月份日历数据"""
    diaries = {}
    diaries_dir = DATA_DIR / "diaries" / user_id
    if diaries_dir.exists():
        for f in diaries_dir.glob("*.json"):
            try:
                diary = json.load(open(f, encoding="utf-8"))
                diaries[diary["date"]] = diary
            except Exception:
                pass

    # 获取对话日期
    conversations_dir = DATA_DIR / "conversations" / user_id
    conversation_dates = set()
    if conversations_dir.exists():
        for f in conversations_dir.glob("*.jsonl"):
            date_str = f.stem
            if len(date_str) == 10:
                conversation_dates.add(date_str)

    # 构建日历数据
    from calendar import monthrange
    _, last_day = monthrange(year, month)

    days = {}
    for day in range(1, last_day + 1):
        date_str = f"{year}-{month:02d}-{day:02d}"
        diary = diaries.get(date_str)
        has_conversation = date_str in conversation_dates

        days[date_str] = {
            "has_diary": diary is not None,
            "has_conversation": has_conversation,
            "mood_level": diary.get("mood", {}).get("level") if diary else None,
            "mood_name": diary.get("mood", {}).get("name") if diary else None
        }

    return {"year": year, "month": month, "days": days}


# ========== 日记接口 ==========

@app.get("/diary/pending")
async def check_pending_diary(user_id: str):
    """检查未生成日记"""
    agent = get_agent(user_id)
    has_pending, pending_date, msg_count = agent.check_pending_diary()
    return {
        "has_pending": has_pending,
        "date": pending_date,
        "message_count": msg_count,
        "message": f"您昨天有 {msg_count} 条对话记录未生成日记。" if has_pending else ""
    }


@app.get("/diary/{d}")
async def get_diary_by_date(user_id: str, d: str):
    """获取日记"""
    diary = get_diary(user_id, d)
    if not diary:
        raise HTTPException(status_code=404, detail={"code": 4003, "message": "内容不存在"})
    return diary


@app.put("/diary/{d}")
async def update_diary(user_id: str, d: str, req: DiaryUpdateReq):
    """更新日记"""
    diary = get_diary(user_id, d)
    if not diary:
        raise HTTPException(status_code=404, detail={"code": 4003, "message": "日记不存在"})

    if req.content:
        diary["content"] = req.content
    if req.mood:
        diary["mood"] = req.mood
    if req.tags:
        diary["tags"] = req.tags

    diary["updated_at"] = datetime.now().isoformat()
    diary["is_edited"] = True

    # 记录调整历史
    adjustment_history = diary.get("adjustment_history", [])
    if req.mood and req.mood.get("level") != diary.get("mood", {}).get("level"):
        adjustment_history.append({
            "field": "mood",
            "old_value": diary.get("mood"),
            "new_value": req.mood,
            "timestamp": datetime.now().isoformat()
        })
        diary["mood_adjusted"] = True

    if req.tags and set(req.tags) != set(diary.get("tags", [])):
        adjustment_history.append({
            "field": "tags",
            "old_value": diary.get("tags"),
            "new_value": req.tags,
            "timestamp": datetime.now().isoformat()
        })
        diary["tags_adjusted"] = True

    diary["adjustment_history"] = adjustment_history
    save_diary(user_id, diary)

    # 重新索引
    agent = get_agent(user_id)
    agent.context_builder.add_diary_to_index(
        d,
        diary["content"],
        diary.get("summary", ""),
        diary.get("topic"),
        diary.get("mood", {}).get("level", 3)
    )

    logger.info(user_id, "DIARY_UPDATED", d)
    return {"success": True, "diary": diary}


@app.post("/diary/{d}/regenerate")
async def regenerate_diary(user_id: str, d: str):
    """重新生成日记"""
    diary = get_diary(user_id, d)
    if not diary:
        raise HTTPException(status_code=404, detail={"code": 4003, "message": "日记不存在"})

    conversation = get_conversation(user_id, d)
    user_msgs = [m for m in conversation if m["role"] == "user" and not is_garbage_message(m["content"])]

    if not user_msgs:
        raise HTTPException(status_code=400, detail={"code": 400, "message": "没有有效的对话内容"})

    user_content = "\n".join(f"- {m['content']}" for m in user_msgs)
    style_prompt = get_writing_style(user_id)

    llm = LLMClient(user_id)

    prompt = f"""请根据以下内容生成日记：

{user_content}{style_prompt}

日期：{d}

直接输出日记正文（不要有任何说明文字）："""

    summary_prompt = f"""请为以下日记生成一句话摘要（30字以内），概括这一天最重要的内容：

{user_content}

只输出摘要，不要其他内容："""

    diary_result, summary_result = await asyncio.gather(
        llm.chat([
            {"role": "system", "content": "你是一位专业的日记编辑，整理用户分享的内容生成连贯日记。" + ("请模仿用户写作风格。" if style_prompt else "")},
            {"role": "user", "content": prompt}
        ]),
        llm.chat([
            {"role": "system", "content": "你是一位日记摘要专家。"},
            {"role": "user", "content": summary_prompt}
        ])
    )

    if isinstance(diary_result, dict) and "code" in diary_result:
        raise HTTPException(status_code=500, detail=diary_result)

    summary = summary_result.strip().strip('"').strip("'") if summary_result else ""

    # 评估心情
    conversation_text = "\n".join([f"{'用户' if m['role'] == 'user' else '小年'}: {m['content']}" for m in conversation])
    from function_tools import evaluate_mood, extract_tags, _detect_topic
    mood = await evaluate_mood(conversation_text, user_id)
    tags = extract_tags(conversation_text, user_id)
    topic = _detect_topic(conversation_text)

    diary["content"] = diary_result
    diary["mood"] = {"level": mood["level"], "name": mood["name"], "description": mood["description"]}
    diary["tags"] = tags
    diary["updated_at"] = datetime.now().isoformat()
    diary["is_edited"] = False
    diary["summary"] = summary
    diary["topic"] = topic

    save_diary(user_id, diary)

    agent = get_agent(user_id)
    agent.context_builder.add_diary_to_index(d, diary_result, summary, topic, mood["level"])

    logger.info(user_id, "DIARY_REGENERATED", d)
    return {"success": True, "diary": diary}


@app.post("/diary/generate")
async def generate_diary(user_id: str, target_date: Optional[str] = None):
    """生成日记"""
    target = target_date or date.today().isoformat()
    conversation = get_conversation(user_id, target)

    user_msgs = [m for m in conversation if m["role"] == "user" and not is_garbage_message(m["content"])]
    if not user_msgs:
        raise HTTPException(status_code=400, detail={"code": 400, "message": "没有有效的日记内容"})

    user_content = "\n".join(f"- {m['content']}" for m in user_msgs)
    style_prompt = get_writing_style(user_id)

    prompt = f"""请根据以下内容生成日记：

{user_content}{style_prompt}

日期：{target}

直接输出日记正文（不要有任何说明文字）："""

    result = await LLMClient(user_id).chat([
        {"role": "system", "content": "你是一位专业的日记编辑，整理用户分享的内容生成连贯日记。" + ("请模仿用户写作风格。" if style_prompt else "")},
        {"role": "user", "content": prompt}
    ])

    if isinstance(result, dict) and "code" in result:
        return result

    # 获取 agent 和 llm_client
    agent = get_agent(user_id)
    llm_client = LLMClient(user_id)

    # 评估心情
    conversation_text = agent.get_conversation_text(target)
    mood = agent.evaluate_mood(conversation_text, llm_client)
    tags = agent.extract_tags(conversation_text, llm_client)

    diary_data = {
        "date": target,
        "content": result,
        "mood": {"level": mood.level, "name": mood.name, "description": mood.description},
        "tags": tags,
        "created_at": datetime.now().isoformat()
    }

    save_diary(user_id, diary_data)
    agent.context_builder.add_diary_to_index(target, result)

    # 更新用户画像（异步）
    asyncio.create_task(_update_profile_async(agent, target, llm_client))

    return {"diary": diary_data, "message": "日记生成成功"}


async def _update_profile_async(agent, target_date: str, llm_client):
    """异步更新用户画像"""
    try:
        await asyncio.to_thread(agent.update_user_profile, target_date, llm_client)
    except Exception as e:
        logger.error(agent.user_id, "PROFILE_UPDATE_FAILED", str(e)[:100])


# ========== 定时任务 ==========

async def auto_generate_diaries():
    """每天 23:59:59 检查并自动生成日记"""
    while True:
        now = datetime.now()
        target = now.replace(hour=23, minute=59, second=59, microsecond=0)
        if now >= target:
            target = target + timedelta(days=1)

        wait_seconds = (target - now).total_seconds()
        logger.info("system", "AUTO_DIARY", f"下次检查: {target}, 等待 {wait_seconds} 秒")
        await asyncio.sleep(wait_seconds)

        # 检查所有用户
        try:
            if CONFIG_DIR.exists():
                for config_file in CONFIG_DIR.glob("*.json"):
                    user_id = config_file.stem
                    try:
                        agent = get_agent(user_id)
                        has_pending, pending_date, msg_count = agent.check_pending_diary()

                        if has_pending and pending_date:
                            logger.info(user_id, "AUTO_GENERATE", f"自动生成 {pending_date}")

                            conversation = get_conversation(user_id, pending_date)
                            user_msgs = [m for m in conversation if m["role"] == "user" and not is_garbage_message(m["content"])]

                            if user_msgs:
                                user_content = "\n".join(f"- {m['content']}" for m in user_msgs)
                                prompt = f"""请根据以下内容生成日记：

{user_content}

日期：{pending_date}

直接输出日记正文："""

                                client = LLMClient(user_id)
                                result = await client.chat([
                                    {"role": "system", "content": "你是一位专业的日记编辑。"},
                                    {"role": "user", "content": prompt}
                                ])

                                if not isinstance(result, dict):
                                    diary_data = {
                                        "date": pending_date,
                                        "content": result,
                                        "created_at": datetime.now().isoformat(),
                                        "auto_generated": True
                                    }
                                    save_diary(user_id, diary_data)
                                    logger.info(user_id, "AUTO_GENERATE_SUCCESS", pending_date)
                    except Exception as e:
                        logger.error(user_id, "AUTO_GENERATE_FAILED", str(e)[:100])

        except Exception as e:
            logger.error("system", "AUTO_DIARY_ERROR", str(e)[:100])


@app.on_event("startup")
async def startup_event():
    """启动定时任务"""
    asyncio.create_task(auto_generate_diaries())
    logger.info("system", "STARTUP", "定时任务已启动")


if __name__ == "__main__":
    import uvicorn
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    uvicorn.run(app, host="0.0.0.0", port=8080)
