"""AI Diary - 核心 Agent (V0.0.5 - 重构版)"""
import json
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
from dataclasses import dataclass

from config import DATA_DIR
from logger import get_logger
from retrieval.diary_retriever import SmartContextBuilder
from user_profile import UserProfileManager

# 日志
logger = get_logger("ai-diary.agent")


# ========== 配置 ==========

@dataclass
class AgentConfig:
    """Agent 配置"""
    max_context_tokens: int = 8000


CONFIG = AgentConfig()


# ========== 数据模型 ==========

@dataclass
class Mood:
    """心情数据"""
    level: int  # 1-5
    name: str   # 沮丧、不高兴、正常、有点喜悦、超开心
    description: str  # 一句话描述


# ========== Memory 类 ==========

class Memory:
    """记忆系统 - 管理对话历史"""

    def __init__(self, user_id: str) -> None:
        self.user_id = user_id
        self.conversations_dir = DATA_DIR / "conversations" / user_id
        self.conversations_dir.mkdir(parents=True, exist_ok=True)

    def add_message(self, role: str, content: str) -> None:
        """添加消息到对话历史"""
        file_path = self.conversations_dir / f"{date.today()}.jsonl"
        msg = {"timestamp": datetime.now().isoformat(), "role": role, "content": content}
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(msg, ensure_ascii=False) + "\n")

    def get_conversation(self, day: Optional[str] = None) -> List[Dict[str, str]]:
        """获取指定日期的对话

        Args:
            day: 日期字符串，默认为今天

        Returns:
            消息列表
        """
        file_path = self.conversations_dir / f"{day or date.today()}.jsonl"
        if not file_path.exists():
            return []

        messages: List[Dict[str, str]] = []
        with open(file_path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        # 兼容不同的字段格式
                        if "c" in data:
                            # 来自 llm.py 的格式: t, r, c
                            messages.append({
                                "timestamp": data.get("t"),
                                "role": data.get("r"),
                                "content": data.get("c", "")
                            })
                        elif "content" in data:
                            # 来自 agent.py 的格式: timestamp, role, content
                            messages.append(data)
                    except json.JSONDecodeError as e:
                        logger.warning(self.user_id, "PARSE_ERROR", f"JSON 解析失败: {e}")

        return messages

    def get_context_dynamic(self, max_tokens: int = CONFIG.max_context_tokens) -> List[Dict[str, str]]:
        """根据 token 限制动态获取上下文（默认今天）"""
        return self.get_context_dynamic_for_date(None, max_tokens)

    def get_context_dynamic_for_date(self, day: Optional[str], max_tokens: int = CONFIG.max_context_tokens) -> List[Dict[str, str]]:
        """根据 token 限制动态获取指定日期的上下文

        Args:
            day: 日期字符串
            max_tokens: 最大 token 数

        Returns:
            消息列表
        """
        messages = self.get_conversation(day)
        context: List[Dict[str, str]] = []
        total_tokens = 0

        for msg in reversed(messages):
            content = msg.get("content", "")
            if not content:
                continue
            msg_tokens = len(content) // 4
            if total_tokens + msg_tokens > max_tokens * 0.8:
                break
            context.insert(0, {"role": msg.get("role", "user"), "content": content})
            total_tokens += msg_tokens

        return context

    def get_last_message_time(self, day: Optional[str] = None) -> Optional[datetime]:
        """获取最后一条消息的时间"""
        messages = self.get_conversation(day)
        if not messages:
            return None
        return datetime.fromisoformat(messages[-1]["timestamp"])

    def has_conversation(self, day: Optional[str] = None) -> bool:
        """检查某天是否有对话"""
        return len(self.get_conversation(day)) > 0


# ========== Diary 类 ==========

class Diary:
    """日记存储"""

    def __init__(self, user_id: str) -> None:
        self.user_id = user_id
        self.diaries_dir = DATA_DIR / "diaries" / user_id
        self.diaries_dir.mkdir(parents=True, exist_ok=True)

    def save(self, day: str, diary: Dict[str, Any]) -> None:
        """保存日记

        Args:
            day: 日期字符串
            diary: 日记字典
        """
        with open(self.diaries_dir / f"{day}.json", "w", encoding="utf-8") as f:
            json.dump(diary, f, ensure_ascii=False, indent=2)

    def get(self, day: str) -> Optional[Dict[str, Any]]:
        """获取日记

        Args:
            day: 日期字符串

        Returns:
            日记字典，不存在返回 None
        """
        file_path = self.diaries_dir / f"{day}.json"
        if not file_path.exists():
            return None
        return json.load(open(file_path, encoding="utf-8"))

    def list(self) -> List[str]:
        """列出所有日记日期

        Returns:
            日期字符串列表（降序）
        """
        return sorted([f.stem for f in self.diaries_dir.glob("*.json")], reverse=True)

    def exists(self, day: str) -> bool:
        """检查某天是否已生成日记"""
        return (self.diaries_dir / f"{day}.json").exists()


# ========== DiaryAgent 类 ==========

class DiaryAgent:
    """AI 日记 Agent - V0.0.5 重构版"""

    DEFAULT_SOUL: str = """你是小年，一位温暖的编年日记助手。通过对话引导用户分享今天的事情。
用开放式问题鼓励，积极回应，表达共情。记住对话细节，用于生成日记。
你的名字叫"小年"，产品叫"编年"。"""

    def __init__(self, user_id: str) -> None:
        self.user_id = user_id
        self.memory = Memory(user_id)
        self.diary = Diary(user_id)
        self._soul: Optional[str] = None
        self._soul_mtime: float = 0
        self.context_builder = SmartContextBuilder(user_id)
        self.context_builder.user_id = user_id
        self.user_profile = UserProfileManager(user_id)

    def _load_soul(self) -> str:
        """动态加载人格文件（支持热更新）"""
        soul_file = Path.home() / "ai-diary" / "bianNian" / "diary-soul.md"
        if soul_file.exists():
            mtime = soul_file.stat().st_mtime
            if mtime != self._soul_mtime:
                self._soul = soul_file.read_text(encoding="utf-8")
                self._soul_mtime = mtime

        if not self._soul:
            self._soul = self.DEFAULT_SOUL
        return self._soul

    def should_retrieve_history(self, query: str) -> bool:
        """判断是否需要检索历史日记"""
        history_keywords = ['之前', '以前', '上次', '那天', '记得', '日记', '之前说过', '上次提到']
        return any(kw in query for kw in history_keywords)

    def build_system_prompt(self) -> str:
        """构建完整的 system prompt（人格 + 用户画像）"""
        soul = self._load_soul()
        profile = self.user_profile.get_for_prompt()
        current_date = date.today().strftime("%Y年%m月%d日")
        today_iso = date.today().strftime('%Y-%m-%d')
        return f"{soul}\n{profile}\n\n【重要信息】\n今天是{current_date}，在调用 retrieve_diaries 函数时，请将相对时间转换为具体日期（如昨天→{today_iso}），格式为 'YYYY-MM-DD' 或 'YYYY-MM-DD至YYYY-MM-DD'。\n\n【检索策略】当用户提到人名（如赵璐）、情绪（如被气到、开心、难过）、事件或询问历史时，请主动提取关键词并调用 retrieve_diaries 函数检索相关日记，了解用户的背景信息后再回复。多个关键词用逗号分隔，如'赵璐,气到'。\n\n【生成日记策略】当用户说'生成日记'、'保存日记'、'帮我写日记'、'写日记'、'记录日记'或表达要结束对话（如'结束'、'今天就到这里'、'就这样'、'好了'、'完了'）时，请调用 generate_diary 函数生成并保存日记。"

    def build_context_for_query(self, query: str) -> Tuple[List[Dict[str, str]], Dict[str, Any]]:
        """构建智能上下文 - 包含用户画像

        Args:
            query: 用户查询

        Returns:
            (上下文消息列表, 元数据字典)
        """
        context = [{"role": "system", "content": self.build_system_prompt()}]

        # 动态获取上下文
        recent = self.memory.get_context_dynamic(max_tokens=6000)
        for msg in recent:
            context.append({"role": msg["role"], "content": msg["content"]})

        # 只在必要时检索日记
        meta: Dict[str, int] = {"retrieval_results": 0}
        if self.should_retrieve_history(query):
            retrieved, meta = self.context_builder.build_context(query)
            if retrieved:
                context.insert(1, {"role": "system", "content": f"【历史日记参考】\n{retrieved}"})

        return context, meta

    def get_conversation_text(self, day: Optional[str] = None) -> str:
        """获取格式化的对话文本

        Args:
            day: 日期字符串，默认为今天

        Returns:
            格式化的对话文本
        """
        messages = self.memory.get_conversation(day)
        lines = []
        for msg in messages:
            role = "用户" if msg["role"] == "user" else "小年"
            lines.append(f"{role}: {msg['content']}")
        return "\n".join(lines)

    def evaluate_mood(self, conversation_text: str, llm_client) -> Mood:
        """评估当天心情

        Args:
            conversation_text: 对话文本
            llm_client: LLM 客户端

        Returns:
            Mood 对象
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
            result = llm_client.generate_text(mood_prompt)
            # 解析 JSON
            import re
            json_match = re.search(r'\{[^}]+\}', result)
            if json_match:
                mood_data = json.loads(json_match.group())
                return Mood(
                    level=mood_data.get("level", 3),
                    name=mood_data.get("name", "正常"),
                    description=mood_data.get("description", "情绪平稳")
                )
        except Exception as e:
            logger.error(self.user_id, "MOOD_EVAL_FAILED", str(e))

        return Mood(level=3, name="正常", description="情绪平稳")

    def extract_tags(self, conversation_text: str, llm_client) -> List[str]:
        """提取日记标签

        Args:
            conversation_text: 对话文本
            llm_client: LLM 客户端

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
            result = llm_client.generate_text(tag_prompt)
            tags = [tag.strip() for tag in result.split(",") if tag.strip()]
            return tags[:5]
        except Exception as e:
            logger.error(self.user_id, "TAG_EXTRACT_FAILED", str(e))
            return []

    def update_user_profile(self, day: Optional[str] = None, llm_client=None) -> bool:
        """更新用户画像

        Args:
            day: 日期字符串
            llm_client: LLM 客户端

        Returns:
            是否更新成功
        """
        if llm_client is None:
            return False

        conversation_text = self.get_conversation_text(day)
        if not conversation_text:
            return False

        return self.user_profile.update(conversation_text, llm_client)

    def check_pending_diary(self) -> Tuple[bool, str, int]:
        """检查是否有未生成日记的对话

        Returns:
            (是否有未生成日记, 日期, 对话数量)
        """
        yesterday = (date.today() - timedelta(days=1)).isoformat()

        if not self.memory.has_conversation(yesterday):
            return False, "", 0

        if self.diary.exists(yesterday):
            return False, "", 0

        # 检查最后对话时间是否超过10分钟
        last_time = self.memory.get_last_message_time(yesterday)
        if last_time:
            time_diff = datetime.now() - last_time
            if time_diff < timedelta(minutes=10):
                return False, "", 0

        messages = self.memory.get_conversation(yesterday)
        user_messages = [m for m in messages if m["role"] == "user"]

        return True, yesterday, len(user_messages)
