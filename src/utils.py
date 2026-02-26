"""共享工具函数模块 - V0.0.5"""
import json
import base64
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, date as date_type

from config import DATA_DIR, CONFIG_DIR


# ========== 配置相关 ==========

def get_user_config(user_id: str) -> Dict[str, Any]:
    """获取用户配置

    Args:
        user_id: 用户ID

    Returns:
        用户配置字典
    """
    config_file = CONFIG_DIR / f"{user_id}.json"
    if not config_file.exists():
        return {}

    with open(config_file, encoding="utf-8") as f:
        return json.load(f)


def save_user_config(user_id: str, config: Dict[str, Any]) -> None:
    """保存用户配置

    Args:
        user_id: 用户ID
        config: 配置字典
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # 加密 api_key
    cfg = config.copy()
    if cfg.get("api_key"):
        cfg["api_key"] = encrypt_api_key(cfg["api_key"])

    with open(CONFIG_DIR / f"{user_id}.json", "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


# ========== 对话相关 ==========

def get_conversation(user_id: str, day: Optional[str] = None) -> List[Dict[str, str]]:
    """获取对话记录

    Args:
        user_id: 用户ID
        day: 日期字符串，默认为今天

    Returns:
        消息列表
    """
    target_day = day or date_type.today().isoformat()
    file_path = DATA_DIR / "conversations" / user_id / f"{target_day}.jsonl"

    if not file_path.exists():
        return []

    messages: List[Dict[str, str]] = []
    with open(file_path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    data = json.loads(line)
                    # 兼容不同格式
                    if "c" in data:
                        messages.append({
                            "role": data.get("r", "user"),
                            "content": data.get("c", "")
                        })
                    elif "role" in data and "content" in data:
                        messages.append(data)
                except json.JSONDecodeError:
                    continue

    return messages


def save_message(user_id: str, role: str, content: str, msg_date: Optional[str] = None) -> None:
    """保存对话消息

    Args:
        user_id: 用户ID
        role: 角色 (user/assistant)
        content: 消息内容
        msg_date: 日期字符串，默认为今天
    """
    target_date = msg_date or date_type.today().isoformat()
    file_path = DATA_DIR / "conversations" / user_id / f"{target_date}.jsonl"
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "t": datetime.now().isoformat(),
            "r": role,
            "c": content
        }, ensure_ascii=False) + "\n")


# ========== 日记相关 ==========

def get_diary(user_id: str, day: str) -> Optional[Dict[str, Any]]:
    """获取日记

    Args:
        user_id: 用户ID
        day: 日期字符串

    Returns:
        日记字典，不存在则返回 None
    """
    file_path = DATA_DIR / "diaries" / user_id / f"{day}.json"
    if not file_path.exists():
        return None

    with open(file_path, encoding="utf-8") as f:
        return json.load(f)


def save_diary(user_id: str, diary: Dict[str, Any]) -> None:
    """保存日记

    Args:
        user_id: 用户ID
        diary: 日记字典
    """
    diaries_dir = DATA_DIR / "diaries" / user_id
    diaries_dir.mkdir(parents=True, exist_ok=True)

    diary_date = diary.get("date", date_type.today().isoformat())
    file_path = diaries_dir / f"{diary_date}.json"

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(diary, f, ensure_ascii=False, indent=2)


def list_diaries(user_id: str) -> List[str]:
    """列出用户所有日记日期

    Args:
        user_id: 用户ID

    Returns:
        日期字符串列表（降序）
    """
    diaries_dir = DATA_DIR / "diaries" / user_id
    if not diaries_dir.exists():
        return []

    return sorted([f.stem for f in diaries_dir.glob("*.json")], reverse=True)


# ========== 加密相关 ==========

# TODO: V0.0.6 迁移到环境变量
_SECRET = "AI_DIARY_SECRET_KEY_2024"


def encrypt_api_key(key: str) -> str:
    """加密 API Key（临时方案）

    Args:
        key: 原始 API Key

    Returns:
        加密后的字符串
    """
    if key.startswith("ENC:"):
        return key
    encrypted = "".join(
        chr(ord(c) ^ ord(_SECRET[i % len(_SECRET)]))
        for i, c in enumerate(key)
    )
    return "ENC:" + base64.b64encode(encrypted.encode()).decode()


def decrypt_api_key(encrypted_key: str) -> str:
    """解密 API Key（临时方案）

    Args:
        encrypted_key: 加密后的字符串

    Returns:
        原始 API Key
    """
    if not encrypted_key.startswith("ENC:"):
        return encrypted_key
    decoded = base64.b64decode(encrypted_key[4:]).decode()
    return "".join(
        chr(ord(c) ^ ord(_SECRET[i % len(_SECRET)]))
        for i, c in enumerate(decoded)
    )


# ========== 辅助函数 ==========

def is_garbage_message(content: str) -> bool:
    """判断是否为垃圾消息

    Args:
        content: 消息内容

    Returns:
        是否为垃圾消息
    """
    import re

    GARBAGE_PATTERNS = [
        r"^你好[\s!！]*$",
        r"^在吗[\s?？]*$",
        r"^hi[\s!！]*$",
        r"^hello[\s!！]*$",
        r"^你能做什么[\s?？]*$",
        r"^你是谁[\s?？]*$",
        r"^今天.*[怎么样|如何].*[\s?？]*$",
        r"^测试[\s!！]*$",
        r"^\?+$",
    ]

    return any(re.match(p, content.strip(), re.I) for p in GARBAGE_PATTERNS)


def parse_date_range(date_range: str) -> tuple:
    """解析日期范围

    Args:
        date_range: 日期范围字符串，如 '2024-02-20至2024-02-25'

    Returns:
        (开始日期, 结束日期) 或 (单个日期, None)
    """
    if not date_range:
        return None, None

    if "至" in date_range or "到" in date_range:
        sep = "至" if "至" in date_range else "到"
        parts = date_range.split(sep)
        return parts[0].strip(), parts[1].strip()

    return date_range.strip(), None
