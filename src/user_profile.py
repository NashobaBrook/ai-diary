"""AI Diary - 用户画像管理模块 (V0.0.5 - 重构版)"""
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional

from config import DATA_DIR
from logger import get_logger

# 日志
logger = get_logger("ai-diary.user_profile")


class UserProfileManager:
    """用户画像管理器 - 管理 user.md"""

    DEFAULT_TEMPLATE = """# 用户画像

## 基本信息
- 姓名：
- 职业：
- 年龄阶段：
- 所在城市：

## 兴趣爱好
-

## 生活习惯
-

## 重要经历
-

## 社交关系
-

## 其他备注
-
"""

    def __init__(self, user_id: str) -> None:
        self.user_id = user_id
        self.user_dir = DATA_DIR / user_id
        self.profile_file = self.user_dir / "user.md"
        self.backup_dir = self.user_dir / "backups"
        self.max_size = 50 * 1024  # 50KB
        self._cache: Optional[str] = None
        self._cache_time: Optional[datetime] = None

    def load(self) -> str:
        """加载用户画像内容（带缓存）

        Returns:
            用户画像内容
        """
        # 检查缓存
        if self._cache is not None and self._cache_time is not None:
            if (datetime.now() - self._cache_time).seconds < 300:  # 5分钟缓存
                return self._cache

        if not self.profile_file.exists():
            content = self._create_default()
        else:
            content = self.profile_file.read_text(encoding="utf-8")

        # 更新缓存
        self._cache = content
        self._cache_time = datetime.now()

        return content

    def update(self, conversation_content: str, llm_client) -> bool:
        """基于对话内容更新用户画像

        Args:
            conversation_content: 对话内容
            llm_client: LLM 客户端

        Returns:
            是否更新成功
        """
        try:
            # 1. 读取现有内容
            current_profile = self.load()

            # 2. 调用 LLM 提取新信息
            update_prompt = f"""基于以下当天对话内容，提取用户的新信息，更新用户画像。

现有用户画像：
{current_profile}

当天对话内容：
{conversation_content}

请：
1. 分析对话中透露的新信息（兴趣爱好、生活习惯、重要事件等）
2. 与现有画像合并，避免重复
3. 按模板格式输出更新后的完整画像
4. 保持简洁，重点记录重要信息

输出格式：
# 用户画像
[更新后的完整内容]"""

            new_profile = llm_client.generate_text(update_prompt)

            # 3. 检查 LLM 是否成功返回内容
            if not new_profile or not new_profile.strip():
                logger.warning(self.user_id, "PROFILE_UPDATE", "LLM 返回空内容，跳过更新")
                return False

            # 4. 检查大小，必要时压缩
            if len(new_profile.encode('utf-8')) > self.max_size:
                new_profile = self._compress(new_profile, llm_client)

                if not new_profile or not new_profile.strip():
                    logger.warning(self.user_id, "PROFILE_UPDATE", "压缩后内容为空，跳过更新")
                    return False

            # 5. 备份旧版本
            self._backup()

            # 6. 保存新版本
            self.profile_file.write_text(new_profile, encoding="utf-8")

            # 7. 更新缓存
            self._cache = new_profile
            self._cache_time = datetime.now()

            logger.info(self.user_id, "PROFILE_UPDATED", f"size={len(new_profile)}")
            return True

        except Exception as e:
            logger.error(self.user_id, "PROFILE_UPDATE_FAILED", str(e))
            return False

    def _compress(self, content: str, llm_client) -> str:
        """压缩内容到 50KB 以内

        Args:
            content: 待压缩内容
            llm_client: LLM 客户端

        Returns:
            压缩后的内容
        """
        compress_prompt = f"""请将以下用户画像内容压缩，保留核心信息，删除冗余描述。

当前内容：
{content}

压缩要求：
1. 保留所有标题和结构
2. 每条信息保留最关键的部分
3. 合并相似或重复的内容
4. 删除过于详细的描述
5. 确保输出不超过 {self.max_size} 字节

输出压缩后的完整内容："""

        return llm_client.generate_text(compress_prompt)

    def _backup(self) -> None:
        """备份当前版本"""
        if not self.profile_file.exists():
            return

        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # 生成备份文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"user.md.{timestamp}"

        # 复制文件
        shutil.copy2(self.profile_file, backup_file)

        # 只保留最近 3 个备份
        backups = sorted(self.backup_dir.glob("user.md.*"), key=lambda p: p.stat().st_mtime, reverse=True)
        for old_backup in backups[3:]:
            old_backup.unlink()

    def _create_default(self) -> str:
        """创建默认用户画像

        Returns:
            默认模板内容
        """
        self.user_dir.mkdir(parents=True, exist_ok=True)
        self.profile_file.write_text(self.DEFAULT_TEMPLATE, encoding="utf-8")
        return self.DEFAULT_TEMPLATE

    def get_for_prompt(self) -> str:
        """获取用于 prompt 的用户画像内容

        Returns:
            格式化后的用户画像
        """
        content = self.load()
        return f"\n\n## 用户画像\n{content}\n"
