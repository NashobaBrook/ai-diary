"""统一配置管理模块 - V0.0.5"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import os


@dataclass
class PathConfig:
    """路径配置"""

    home: Path = field(default_factory=lambda: Path.home())
    data_dir: Path = field(init=False)
    diaries_dir: Path = field(init=False)
    conversations_dir: Path = field(init=False)
    config_dir: Path = field(init=False)
    log_dir: Path = field(init=False)
    biannian_dir: Path = field(init=False)
    index_dir: Path = field(init=False)

    def __post_init__(self):
        base = self.home / "ai-diary"
        self.data_dir = base / "data"
        self.diaries_dir = base / "data" / "diaries"
        self.conversations_dir = base / "data" / "conversations"
        self.config_dir = base / "config"
        self.log_dir = base / "logs"
        self.biannian_dir = base / "bianNian"
        self.index_dir = base / "data" / "index"

        # 自动创建目录
        for p in [self.data_dir, self.log_dir, self.config_dir, self.index_dir]:
            p.mkdir(parents=True, exist_ok=True)


@dataclass
class Config:
    """全局配置"""

    path: PathConfig = field(default_factory=PathConfig)
    max_context_tokens: int = 8000
    cache_ttl_seconds: int = 300  # 5分钟缓存
    index_max_chars: int = 2000
    profile_max_size: int = 50 * 1024  # 50KB

    @classmethod
    def from_env(cls) -> "Config":
        """从环境变量加载配置"""
        return cls(
            max_context_tokens=int(os.getenv("MAX_CONTEXT_TOKENS", "8000")),
            cache_ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", "300")),
        )


# 全局配置实例
config = Config.from_env()

# 导出常用路径供外部使用（向后兼容）
DATA_DIR = config.path.data_dir
DIARIES_DIR = config.path.diaries_dir
CONVERSATIONS_DIR = config.path.conversations_dir
CONFIG_DIR = config.path.config_dir
LOG_DIR = config.path.log_dir
BIANNIAN_DIR = config.path.biannian_dir
INDEX_DIR = config.path.index_dir
