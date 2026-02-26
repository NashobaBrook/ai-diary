"""AI Diary - 检索模块 (V0.0.5 - 重构版)"""
import json
import re
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from collections import Counter
from datetime import datetime

from config import INDEX_DIR

# 确保目录存在
INDEX_DIR.mkdir(parents=True, exist_ok=True)


# ========== 停用词 ==========

STOP_WORDS: set = {
    '的', '是', '了', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
    '你', '会', '着', '没有', '看', '好', '自己', '这', '我们', '他', '她', '它', '吗', '呢', '吧', '啊', '呀', '哦', '嗯',
    '什么', '这个', '那个', '可以', '这样', '那样', '然后', '但是', '所以', '因为', '如果', '就是', '还是', '或者', '而且',
    '不过', '已经', '这些', '那些', '他们', '她们', '它们', '我们', '我的', '你的', '他的', '她的', '它的', '自己',
    '今天', '明天', '昨天', '现在', '时候', '地方', '东西', '事情', '问题', '答案', '感觉', '觉得', '知道', '看到',
    '听到', '想到', '开始', '结束', '起来', '出来', '回来', '过来', '下去', '上去'
}


# ========== 辅助函数 ==========

def _extract_keywords(text: str) -> List[str]:
    """提取关键词

    Args:
        text: 待提取文本

    Returns:
        关键词列表
    """
    if not text:
        return []

    chinese = re.findall(r'[\u4e00-\u9fff]+', text.lower())
    english = re.findall(r'[a-zA-Z]+', text.lower())

    keywords: List[str] = []
    for chars in chinese:
        for length in [2, 3, 4]:
            for i in range(len(chars) - length + 1):
                word = chars[i:i+length]
                if word not in STOP_WORDS:
                    keywords.append(word)

    keywords.extend([w for w in english if len(w) > 2])
    return [k for k, _ in Counter(keywords).most_common(10)] if keywords else []


def _extract_entities(text: str) -> List[str]:
    """提取实体（人名、专有名词等）

    Args:
        text: 待提取文本

    Returns:
        实体列表
    """
    # 提取2-4个字符的中文词（可能是人名）
    chinese_names = re.findall(r'[\u4e00-\u9fff]{2,4}', text)
    # 过滤掉常见词
    common_words = {'今天', '昨天', '明天', '现在', '时候', '这个', '那个', '什么', '怎么', '如何', '为什么'}
    entities = [w for w in chinese_names if w not in STOP_WORDS and w not in common_words]
    return entities


def _detect_topic(text: str) -> str:
    """简单的话题检测

    Args:
        text: 待检测文本

    Returns:
        话题名称
    """
    topic_keywords: Dict[str, List[str]] = {
        "工作": ["工作", "项目", "同事", "老板", "会议", "加班", "辞职", "面试"],
        "情感": ["恋爱", "分手", "结婚", "相亲", "对象", "老公", "老婆", "女朋友", "男朋友", "约会"],
        "学习": ["学习", "考试", "考研", "读书", "课程", "培训", "成绩"],
        "健康": ["身体", "生病", "医院", "健身", "运动", "减肥", "健康"],
        "旅行": ["旅游", "旅行", "出差", "度假", "景点", "酒店"],
        "娱乐": ["电影", "音乐", "游戏", "综艺", "电视剧", "小说"],
        "生活": ["做饭", "购物", "租房", "搬家", "养宠物", "猫", "狗"]
    }

    text_lower = text.lower()
    for topic, keywords in topic_keywords.items():
        if any(kw in text_lower for kw in keywords):
            return topic
    return "其他"


# ========== DiaryIndexer 类 ==========

class DiaryIndexer:
    """日记索引器 - 多维度智能检索"""

    def __init__(self, user_id: str) -> None:
        self.user_id = user_id
        self.index_file = INDEX_DIR / f"{user_id}.json"
        self.diary_dates: List[str] = []
        self.contents: List[str] = []
        self.keywords_list: List[List[str]] = []
        self.summaries: List[str] = []
        self.topics: List[Optional[str]] = []
        self.mood_levels: List[int] = []
        self._load()

    def _load(self) -> None:
        """加载索引"""
        if self.index_file.exists():
            try:
                data = json.load(open(self.index_file, encoding="utf-8"))
                self.diary_dates = data.get("dates", [])
                self.contents = data.get("contents", [])
                self.keywords_list = data.get("keywords", [])
                # 新增字段，兼容旧数据
                self.summaries = data.get("summaries", [""] * len(self.diary_dates))
                self.topics = data.get("topics", [None] * len(self.diary_dates))
                self.mood_levels = data.get("mood_levels", [3] * len(self.diary_dates))

                # 兼容旧数据
                if len(self.summaries) < len(self.diary_dates):
                    self.summaries.extend([""] * (len(self.diary_dates) - len(self.summaries)))
                if len(self.topics) < len(self.diary_dates):
                    self.topics.extend([None] * (len(self.diary_dates) - len(self.topics)))
                if len(self.mood_levels) < len(self.diary_dates):
                    self.mood_levels.extend([3] * (len(self.diary_dates) - len(self.mood_levels)))
            except json.JSONDecodeError:
                pass

    def _save(self) -> None:
        """保存索引"""
        json.dump({
            "dates": self.diary_dates,
            "contents": self.contents,
            "keywords": self.keywords_list,
            "summaries": self.summaries,
            "topics": self.topics,
            "mood_levels": self.mood_levels
        }, open(self.index_file, "w", encoding="utf-8"), ensure_ascii=False)

    def index_diary(
        self,
        diary_date: str,
        content: str,
        summary: str = "",
        topic: Optional[str] = None,
        mood_level: int = 3
    ) -> None:
        """索引日记

        Args:
            diary_date: 日记日期
            content: 日记内容
            summary: 摘要
            topic: 主题
            mood_level: 心情等级
        """
        keywords = _extract_keywords(content)
        if diary_date in self.diary_dates:
            idx = self.diary_dates.index(diary_date)
            self.contents[idx] = content
            self.keywords_list[idx] = keywords
            if summary:
                self.summaries[idx] = summary
            if topic:
                self.topics[idx] = topic
            self.mood_levels[idx] = mood_level
        else:
            self.diary_dates.append(diary_date)
            self.contents.append(content)
            self.keywords_list.append(keywords)
            self.summaries.append(summary or "")
            self.topics.append(topic)
            self.mood_levels.append(mood_level)
        self._save()

    def _calc_keyword_scores(self, query: str) -> List[float]:
        """计算关键词相关度分数

        Args:
            query: 查询文本

        Returns:
            分数列表
        """
        query_keywords = set(_extract_keywords(query))
        if not query_keywords:
            query_keywords = set(re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', query.lower()))

        scores: List[float] = []
        for keywords in self.keywords_list:
            if not keywords:
                scores.append(0)
                continue
            score = len(query_keywords & set(keywords))
            scores.append(score)
        return scores

    def _calc_topic_scores(self, current_topic: Optional[str]) -> List[float]:
        """计算话题匹配分数

        Args:
            current_topic: 当前话题

        Returns:
            分数列表
        """
        if not current_topic:
            return [0] * len(self.diary_dates)

        scores: List[float] = []
        for topic in self.topics:
            if topic and topic == current_topic:
                scores.append(1.0)
            elif topic and current_topic in self._get_related_topics(topic):
                scores.append(0.5)
            else:
                scores.append(0)
        return scores

    def _get_related_topics(self, topic: str) -> List[str]:
        """获取相关话题

        Args:
            topic: 话题

        Returns:
            相关话题列表
        """
        related: Dict[str, List[str]] = {
            "工作": ["学习"],
            "情感": ["生活"],
            "学习": ["工作"],
            "健康": ["生活"],
            "旅行": ["娱乐"],
            "娱乐": ["旅行", "生活"],
            "生活": ["情感", "健康", "娱乐"]
        }
        return related.get(topic, [])

    def _calc_mention_scores(self, mentioned_entities: List[str]) -> List[float]:
        """计算主动提及分数

        Args:
            mentioned_entities: 提到的实体列表

        Returns:
            分数列表
        """
        if not mentioned_entities:
            return [0] * len(self.diary_dates)

        scores: List[float] = []
        for content in self.contents:
            entity_count = sum(1 for entity in mentioned_entities if entity in content)
            scores.append(min(entity_count * 0.5, 1.0))
        return scores

    def _calc_time_scores(self) -> List[float]:
        """计算时间近度分数

        Returns:
            分数列表
        """
        if not self.diary_dates:
            return []

        try:
            today = datetime.now()
            scores: List[float] = []
            for date_str in self.diary_dates:
                try:
                    dt = datetime.strptime(date_str, "%Y-%m-%d")
                    days_diff = (today - dt).days
                    # 30天内按时间衰减，30天外给最低分
                    if days_diff <= 30:
                        score = 1 - (days_diff / 30)
                    elif days_diff <= 90:
                        score = 0.3 - ((days_diff - 30) / 60) * 0.3
                    else:
                        score = 0
                    scores.append(score)
                except ValueError:
                    scores.append(0)
            return scores
        except Exception:
            return [0] * len(self.diary_dates)

    def _calc_mood_scores(self) -> List[float]:
        """计算心情极端度分数

        Returns:
            分数列表
        """
        scores: List[float] = []
        for level in self.mood_levels:
            if level in [1, 5]:  # 极端心情
                scores.append(1.0)
            elif level in [2, 4]:  # 轻微波动
                scores.append(0.5)
            else:  # 正常
                scores.append(0.2)
        return scores

    def search_with_context(
        self,
        query: str,
        context: Dict[str, Any],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """多维度智能检索

        Args:
            query: 查询文本
            context: 上下文字典
            top_k: 返回结果数量

        Returns:
            检索结果列表
        """
        if not self.contents:
            return []

        # 1. 计算各维度分数
        keyword_scores = self._calc_keyword_scores(query)
        topic_scores = self._calc_topic_scores(context.get("current_topic"))
        mention_scores = self._calc_mention_scores(context.get("mentioned_entities", []))
        time_scores = self._calc_time_scores()
        mood_scores = self._calc_mood_scores()

        # 2. 加权求和
        weights = {
            "keyword": 0.30,
            "topic": 0.25,
            "mention": 0.20,
            "time": 0.15,
            "mood": 0.10
        }

        results: List[Dict[str, Any]] = []
        for i in range(len(self.diary_dates)):
            # 归一化关键词分数
            max_keyword = max(keyword_scores) if keyword_scores else 1
            if max_keyword > 0:
                score = (
                    (keyword_scores[i] / max_keyword) * weights["keyword"] +
                    topic_scores[i] * weights["topic"] +
                    mention_scores[i] * weights["mention"] +
                    time_scores[i] * weights["time"] +
                    mood_scores[i] * weights["mood"]
                )
            else:
                score = 0

            if score > 0:
                results.append({
                    "date": self.diary_dates[i],
                    "content": self.contents[i],
                    "summary": self.summaries[i] if i < len(self.summaries) else "",
                    "topic": self.topics[i] if i < len(self.topics) else None,
                    "mood_level": self.mood_levels[i] if i < len(self.mood_levels) else 3,
                    "score": round(score, 3)
                })

        # 3. 按分数排序，返回候选列表
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def search(self, query: str, top_k: int = 3) -> List[Tuple[str, str, float]]:
        """兼容旧接口的搜索方法

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            [(日期, 内容, 分数), ...]
        """
        results = self.search_with_context(
            {"query": query, "mentioned_entities": [], "current_topic": None},
            top_k=top_k
        )
        return [(r["date"], r["content"], r["score"]) for r in results]


# ========== SmartContextBuilder 类 ==========

class SmartContextBuilder:
    """智能上下文构建器"""

    def __init__(self, user_id: str) -> None:
        self.indexer = DiaryIndexer(user_id)
        self.max_chars = 2000
        self.current_message: Optional[str] = None

    def build_context(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """构建智能上下文（兼容旧接口）

        Args:
            query: 查询文本
            conversation_history: 对话历史

        Returns:
            (上下文字符串, 元数据字典)
        """
        context = {
            "query": query,
            "mentioned_entities": _extract_entities(query),
            "current_topic": _detect_topic(query)
        }
        return self.build_context_with_context(query, context, conversation_history)

    def build_context_with_context(
        self,
        query: str,
        context: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """构建智能上下文（带对话上下文）

        Args:
            query: 查询文本
            context: 上下文字典
            conversation_history: 对话历史

        Returns:
            (上下文字符串, 元数据字典)
        """
        results = self.indexer.search_with_context(query, context, top_k=5)
        results = [r for r in results if r["score"] >= 0.1]

        # 构建带摘要的上下文
        parts: List[str] = []
        total_chars = 0
        for r in results:
            try:
                dt = datetime.strptime(r["date"], "%Y-%m-%d")
                formatted_date = dt.strftime("%Y年%m月%d日")
            except ValueError:
                formatted_date = r["date"]

            # 优先使用摘要
            summary = r["summary"] if r["summary"] else r["content"][:100]

            entry = f"""【候选：{formatted_date}】(相关性: {r["score"]})
摘要: {summary}
全文: {r["content"]}"""

            if total_chars + len(entry) <= self.max_chars:
                parts.append(entry)
                total_chars += len(entry)

        meta: Dict[str, Any] = {"retrieval_candidates": len(results), "total_chars": total_chars}
        return "\n\n---\n\n".join(parts), meta

    def add_diary_to_index(
        self,
        diary_date: str,
        content: str,
        summary: str = "",
        topic: Optional[str] = None,
        mood_level: int = 3
    ) -> None:
        """添加日记到索引

        Args:
            diary_date: 日记日期
            content: 日记内容
            summary: 摘要
            topic: 主题
            mood_level: 心情等级
        """
        self.indexer.index_diary(diary_date, content, summary, topic, mood_level)
