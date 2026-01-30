"""
OneBot WebSocket客户端
"""
import json
import asyncio
import websockets
from typing import Callable, Dict, Any, Optional
import logging


class OneBotClient:
    """OneBot WebSocket客户端"""

    def __init__(
        self,
        ws_url: str,
        on_message: Callable[[Dict[str, Any]], None],
        logger: logging.Logger,
        reconnect_interval: int = 5,
        timeout: int = 30
    ):
        """
        初始化OneBot客户端

        Args:
            ws_url: WebSocket地址（ws://host:port）
            on_message: 消息回调函数
            logger: 日志器
            reconnect_interval: 重连间隔（秒）
            timeout: 连接超时（秒）
        """
        self.ws_url = ws_url
        self.on_message = on_message
        self.logger = logger
        self.reconnect_interval = reconnect_interval
        self.timeout = timeout
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.running = False
        self.heartbeat_task = None

    async def connect(self):
        """连接到OneBot服务器"""
        while self.running:
            try:
                self.logger.info(f"正在连接到 OneBot: {self.ws_url}")
                self.websocket = await asyncio.wait_for(
                    websockets.connect(self.ws_url),
                    timeout=self.timeout
                )
                self.logger.info("OneBot 连接成功")
                break
            except Exception as e:
                self.logger.error(f"OneBot 连接失败: {e}, {self.reconnect_interval}秒后重试...")
                await asyncio.sleep(self.reconnect_interval)

    async def disconnect(self):
        """断开连接"""
        self.running = False
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
            self.heartbeat_task = None

        if self.websocket:
            await self.websocket.close()
            self.logger.info("OneBot 连接已断开")

    async def listen(self):
        """监听消息"""
        if not self.websocket:
            raise RuntimeError("WebSocket未连接")

        self.running = True
        self.heartbeat_task = asyncio.create_task(self._heartbeat())

        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self.on_message(data)
                except json.JSONDecodeError as e:
                    self.logger.error(f"解析消息失败: {e}")
                except Exception as e:
                    self.logger.error(f"处理消息失败: {e}", exc_info=True)
        except websockets.exceptions.ConnectionClosed:
            self.logger.warning("OneBot 连接已关闭")
            await self._reconnect()
        except Exception as e:
            self.logger.error(f"OneBot 监听错误: {e}", exc_info=True)
            await self._reconnect()

    async def _heartbeat(self):
        """心跳保活"""
        while self.running and self.websocket:
            try:
                await asyncio.sleep(30)  # 30秒一次心跳
                if self.websocket and not self.websocket.closed:
                    # 发送心跳
                    await self.websocket.ping()
                    self.logger.debug("心跳发送成功")
            except Exception as e:
                self.logger.error(f"心跳失败: {e}")
                break

    async def _reconnect(self):
        """重新连接"""
        if not self.running:
            return

        self.logger.info("尝试重新连接...")
        await self.connect()
        if self.running:
            await self.listen()

    async def send(self, data: Dict[str, Any]):
        """
        发送消息到OneBot

        Args:
            data: 消息数据（会自动添加action字段）
        """
        if not self.websocket or self.websocket.closed:
            self.logger.error("WebSocket未连接，无法发送消息")
            return

        try:
            message = json.dumps(data, ensure_ascii=False)
            await self.websocket.send(message)
            self.logger.debug(f"发送消息: {message}")
        except Exception as e:
            self.logger.error(f"发送消息失败: {e}")

    async def send_private_message(self, user_id: int, message: str):
        """发送私聊消息"""
        await self.send({
            "action": "send_private_msg",
            "params": {
                "user_id": user_id,
                "message": message
            }
        })

    async def send_group_message(self, group_id: int, message: str):
        """发送群聊消息"""
        await self.send({
            "action": "send_group_msg",
            "params": {
                "group_id": group_id,
                "message": message
            }
        })

    async def get_friend_list(self) -> Optional[Dict[str, Any]]:
        """获取好友列表"""
        await self.send({"action": "get_friend_list"})
        # 注意：这里需要等待响应，实际实现需要更复杂的事件处理

    async def get_group_list(self) -> Optional[Dict[str, Any]]:
        """获取群列表"""
        await self.send({"action": "get_group_list"})
