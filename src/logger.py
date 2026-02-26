"""统一日志管理模块 - V0.0.5"""
import logging
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler

from config import LOG_DIR


class StructuredLogger:
    """结构化日志记录器

    提供统一的日志格式和便捷的日志记录方法。
    """

    def __init__(self, name: str, log_dir: Optional[Path] = None):
        """初始化日志记录器

        Args:
            name: 日志记录器名称
            log_dir: 日志目录，默认为 LOG_DIR
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # 避免重复添加 handler
        if self.logger.handlers:
            return

        # 日志格式
        console_format = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 控制台输出
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(logging.INFO)
        console.setFormatter(console_format)
        self.logger.addHandler(console)

        # 文件输出（按大小轮转，最大10MB，保留5个备份）
        if log_dir:
            log_dir.mkdir(parents=True, exist_ok=True)
            file_handler = RotatingFileHandler(
                log_dir / "ai-diary.log",
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding="utf-8"
            )
            file_handler.setLevel(logging.INFO)

            # 结构化日志格式
            file_format = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - [%(user_id)s] %(action)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)

    def _log(self, level: str, user_id: str, action: str, message: str) -> None:
        """记录日志

        Args:
            level: 日志级别 (debug/info/warning/error)
            user_id: 用户ID
            action: 操作名称
            message: 日志消息
        """
        extra = {"user_id": user_id, "action": action}
        getattr(self.logger, level)(message, extra=extra)

    def debug(self, user_id: str, action: str, message: str = "") -> None:
        """记录调试日志"""
        msg = message or action
        self._log("debug", user_id, action, msg)

    def info(self, user_id: str, action: str, message: str = "") -> None:
        """记录信息日志"""
        msg = message or action
        self._log("info", user_id, action, msg)

    def warning(self, user_id: str, action: str, message: str = "") -> None:
        """记录警告日志"""
        msg = message or action
        self._log("warning", user_id, action, msg)

    def error(self, user_id: str, action: str, message: str = "") -> None:
        """记录错误日志"""
        msg = message or action
        self._log("error", user_id, action, msg)

    def exception(self, user_id: str, action: str, message: str = "") -> None:
        """记录异常日志（包含堆栈信息）"""
        msg = message or action
        self.logger.exception(msg, extra={"user_id": user_id, "action": action})


# 全局日志实例
_logger: Optional[StructuredLogger] = None


def get_logger(name: str = "ai-diary") -> StructuredLogger:
    """获取日志记录器（单例）

    Args:
        name: 日志记录器名称

    Returns:
        StructuredLogger 实例
    """
    global _logger
    if _logger is None:
        _logger = StructuredLogger(name, LOG_DIR)
    return _logger


# 便捷函数

def log(level: str, user_id: str, action: str, detail: str = "") -> None:
    """快速记录日志

    Args:
        level: 日志级别 (debug/info/warning/error)
        user_id: 用户ID
        action: 操作名称
        detail: 详细消息

    Example:
        log("info", "default", "CHAT_START", "用户发送消息")
    """
    logger = get_logger()
    message = detail if detail else action
    logger._log(level, user_id, action, message)


def log_info(user_id: str, action: str, detail: str = "") -> None:
    """快速记录信息日志"""
    log("info", user_id, action, detail)


def log_warning(user_id: str, action: str, detail: str = "") -> None:
    """快速记录警告日志"""
    log("warning", user_id, action, detail)


def log_error(user_id: str, action: str, detail: str = "") -> None:
    """快速记录错误日志"""
    log("error", user_id, action, detail)


def log_exception(user_id: str, action: str, detail: str = "") -> None:
    """快速记录异常日志"""
    logger = get_logger()
    message = detail if detail else action
    logger.exception(user_id, action, message)
