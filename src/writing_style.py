"""AI Diary - 写作风格管理模块 (V0.0.5 - 重构版)"""
from pathlib import Path
from datetime import datetime
from typing import Optional

from config import DATA_DIR
from logger import get_logger

# 日志
logger = get_logger("ai-diary.writing_style")


class WritingStyleManager:
    """写作风格管理器 - 管理 writing_style.md"""

    DEFAULT_TEMPLATE = """# 写作风格

## 风格描述

用户的写作风格自然、口语化，像朋友间的聊天或自言自语。

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

    def __init__(self, user_id: str) -> None:
        self.user_id = user_id
        self.user_dir = DATA_DIR / user_id
        self.style_file = self.user_dir / "writing_style.md"
        self._cache: Optional[str] = None
        self._cache_time: Optional[datetime] = None

    def load(self) -> str:
        """加载写作风格内容（带缓存）

        Returns:
            写作风格内容
        """
        # 检查缓存
        if self._cache is not None and self._cache_time is not None:
            if (datetime.now() - self._cache_time).seconds < 300:  # 5分钟缓存
                return self._cache

        if not self.style_file.exists():
            content = self._create_default()
        else:
            content = self.style_file.read_text(encoding="utf-8")

        # 更新缓存
        self._cache = content
        self._cache_time = datetime.now()

        return content

    def save(self, content: str) -> bool:
        """保存写作风格内容

        Args:
            content: 写作风格内容

        Returns:
            是否保存成功
        """
        try:
            self.user_dir.mkdir(parents=True, exist_ok=True)
            self.style_file.write_text(content, encoding="utf-8")

            # 更新缓存
            self._cache = content
            self._cache_time = datetime.now()

            logger.info(self.user_id, "STYLE_SAVED", f"size={len(content)}")
            return True
        except Exception as e:
            logger.error(self.user_id, "STYLE_SAVE_FAILED", str(e))
            return False

    def get_style_description(self) -> str:
        """获取风格描述（提取 ## 风格描述 部分）

        Returns:
            风格描述文本
        """
        content = self.load()

        # 尝试提取风格描述部分
        lines = content.split('\n')
        in_description = False
        description_lines = []

        for line in lines:
            if line.startswith('## 风格描述'):
                in_description = True
                continue
            elif line.startswith('## ') and in_description:
                break
            elif in_description:
                description_lines.append(line)

        # 如果找到了描述，返回描述内容
        if description_lines:
            return '\n'.join(line.strip() for line in description_lines if line.strip())

        # 否则返回整个内容（去掉标题）
        return content.replace('# 写作风格', '').strip()

    def get_for_prompt(self) -> str:
        """获取用于 prompt 的写作风格内容

        Returns:
            格式化的写作风格提示
        """
        style = self.get_style_description()
        if style:
            return f"\n【用户写作风格】：\n{style}\n请模仿以上风格。"
        return ""

    def _create_default(self) -> str:
        """创建默认写作风格文件

        Returns:
            默认模板内容
        """
        self.user_dir.mkdir(parents=True, exist_ok=True)
        self.style_file.write_text(self.DEFAULT_TEMPLATE, encoding="utf-8")
        return self.DEFAULT_TEMPLATE


# ========== 便捷函数 ==========

def get_writing_style_manager(user_id: str) -> WritingStyleManager:
    """获取写作风格管理器实例

    Args:
        user_id: 用户ID

    Returns:
        WritingStyleManager 实例
    """
    return WritingStyleManager(user_id)


def get_writing_style(user_id: str) -> str:
    """快速获取写作风格描述（用于 prompt）

    Args:
        user_id: 用户ID

    Returns:
        写作风格提示文本
    """
    manager = WritingStyleManager(user_id)
    return manager.get_for_prompt()
