"""
AI Diary - 飞书接入模块
基于 nanobot 思路实现
"""

import json
import asyncio
import logging
import os
from pathlib import Path
from typing import Any
from datetime import datetime

logger = logging.getLogger("ai-diary")

# ============== 飞书 SDK ==============
try:
    import lark_oapi as lark
    from lark_oapi.api.im.v1 import (
        CreateMessageRequest,
        CreateMessageRequestBody,
    )
    FEISHU_AVAILABLE = True
except ImportError:
    FEISHU_AVAILABLE = False
    lark = None

# ============== 配置 ==============
class FeishuConfig:
    """飞书配置"""
    def __init__(self, app_id: str = "", app_secret: str = "", encrypt_key: str = ""):
        self.app_id = app_id
        self.app_secret = app_secret
        self.encrypt_key = encrypt_key
    
    @classmethod
    def from_env(cls):
        return cls(
            app_id=os.getenv("FEISHU_APP_ID", ""),
            app_secret=os.getenv("FEISHU_APP_SECRET", ""),
            encrypt_key=os.getenv("FEISHU_ENCRYPT_KEY", "")
        )

# ============== 飞书客户端 ==============
class FeishuClient:
    """
    飞书客户端 - 基于 nanobot 简化
    功能：接收消息、发送消息
    """
    
    def __init__(self, config: FeishuConfig):
        self.config = config
        self._client = None
        self._ws_client = None
        self._running = False
        
        if not FEISHU_AVAILABLE:
            logger.warning("飞书 SDK 未安装: pip install lark-oapi")
            return
        
        if not config.app_id or not config.app_secret:
            logger.warning("飞书 app_id 或 app_secret 未配置")
            return
        
        # 创建客户端
        self._client = lark.Client.builder() \
            .app_id(config.app_id) \
            .app_secret(config.app_secret) \
            .log_level(lark.LogLevel.INFO) \
            .build()
        
        logger.info("飞书客户端创建成功")
    
    def is_ready(self) -> bool:
        """检查是否可用"""
        return self._client is not None
    
    # --- 发送消息 ---
    def send_message(self, receive_id: str, receive_id_type: str = "open_id", content: str = "") -> bool:
        """
        发送文本消息
        基于 nanobot 的 _send_message_sync
        
        Args:
            receive_id: 接收者 ID (open_id 或 chat_id)
            receive_id_type: "open_id" (用户) 或 "chat_id" (群聊)
            content: 消息内容
        """
        if not self._client:
            logger.error("飞书客户端未初始化")
            return False
        
        try:
            # 构建消息内容
            msg_content = json.dumps({"text": content}, ensure_ascii=False)
            
            # 发送请求
            request = CreateMessageRequest.builder() \
                .receive_id_type(receive_id_type) \
                .request_body(
                    CreateMessageRequestBody.builder()
                    .receive_id(receive_id)
                    .msg_type("text")
                    .content(msg_content)
                    .build()
                ).build()
            
            response = self._client.im.v1.message.create(request)
            
            if response.success():
                logger.debug(f"飞书消息发送成功 to {receive_id}")
                return True
            else:
                logger.error(f"飞书消息发送失败: code={response.code}, msg={response.msg}")
                return False
                
        except Exception as e:
            logger.error(f"飞书消息发送异常: {e}")
            return False
    
    def send_card(self, receive_id: str, receive_id_type: str = "open_id", 
                  title: str = "", content: str = "") -> bool:
        """
        发送富文本卡片消息
        """
        if not self._client:
            return False
        
        try:
            # 构建卡片
            card = {
                "config": {"wide_screen_mode": True},
                "header": {
                    "title": {"tag": "plain_text", "content": title},
                    "template": "blue"
                },
                "elements": [
                    {
                        "tag": "markdown",
                        "content": content
                    }
                ]
            }
            
            msg_content = json.dumps(card, ensure_ascii=False)
            
            request = CreateMessageRequest.builder() \
                .receive_id_type(receive_id_type) \
                .request_body(
                    CreateMessageRequestBody.builder()
                    .receive_id(receive_id)
                    .msg_type("interactive")
                    .content(msg_content)
                    .build()
                ).build()
            
            response = self._client.im.v1.message.create(request)
            return response.success()
            
        except Exception as e:
            logger.error(f"飞书卡片发送异常: {e}")
            return False

    # --- WebSocket 接收消息 (简化版) ---
    async def start_websocket(self, on_message_callback):
        """
        启动 WebSocket 长连接接收消息
        基于 nanobot 的 start 方法
        
        Args:
            on_message_callback: 消息回调函数 (user_id, content) => response
        """
        if not FEISHU_AVAILABLE:
            logger.error("飞书 SDK 未安装，无法启动 WebSocket")
            return
        
        if not self._client:
            logger.error("飞书客户端未初始化，无法启动 WebSocket")
            return
        
        self._running = True
        
        # 创建事件处理器
        from lark_oapi.event import EventDispatcherHandler
        
        event_handler = EventDispatcherHandler.Builder(
            self.config.encrypt_key or "",
            ""
        ).register_p2_im_message_receive_v1(
            lambda data: self._on_message(data, on_message_callback)
        ).build()
        
        # 创建 WebSocket 客户端
        self._ws_client = lark.ws.Client(
            self.config.app_id,
            self.config.app_secret,
            event_handler=event_handler,
            log_level=lark.LogLevel.INFO
        )
        
        # 启动
        import threading
        
        def run_ws():
            while self._running:
                try:
                    self._ws_client.start()
                except Exception as e:
                    logger.warning(f"飞书 WebSocket 错误: {e}")
                if self._running:
                    import time
                    time.sleep(5)
        
        thread = threading.Thread(target=run_ws, daemon=True)
        thread.start()
        
        logger.info("飞书 WebSocket 已启动")
    
    def _on_message(self, data, callback):
        """处理收到的消息"""
        try:
            event = data.event
            message = event.message
            sender = event.sender
            
            # 跳过机器人消息
            if sender.sender_type == "bot":
                return
            
            # 获取发送者 ID
            user_id = sender.sender_id.open_id if sender.sender_id else "unknown"
            
            # 解析消息内容
            content = ""
            msg_type = message.message_type
            
            if msg_type == "text":
                try:
                    content_json = json.loads(message.content) if message.content else {}
                    content = content_json.get("text", "")
                except:
                    content = message.content or ""
            
            if not content:
                return
            
            logger.info(f"收到飞书消息 from {user_id}: {content[:30]}")
            
            # 调用回调获取回复
            response = callback(user_id, content)
            
            # 发送回复
            if response:
                self.send_message(user_id, "open_id", response)
                logger.info(f"发送飞书回复: {response[:30]}")
                
        except Exception as e:
            logger.error(f"处理飞书消息异常: {e}")
    
    def stop(self):
        """停止"""
        self._running = False
        if self._ws_client:
            try:
                self._ws_client.stop()
            except:
                pass


# ============== 使用示例 ==============
"""
# 1. 配置
config = FeishuConfig(
    app_id="cli_xxx",
    app_secret="xxx"
)

# 2. 创建客户端
client = FeishuClient(config)

# 3. 发送消息
client.send_message("ou_xxx", "open_id", "你好！")

# 4. 接收消息（需要 WebSocket）
async def handle(user_id, content):
    # 这里调用 AI
    return "收到: " + content

await client.start_websocket(handle)
"""
