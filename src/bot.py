"""
Bot核心逻辑模块
"""
import re
import asyncio
import inspect
from typing import Dict, Any, List, Optional
import logging
from .onebot_client import OneBotClient
from .claude_handler import ClaudeHandler


class Bot:
    """Bot核心逻辑"""

    def __init__(
        self,
        onebot_client: OneBotClient,
        claude_handler: ClaudeHandler,
        config: Dict[str, Any],
        logger: logging.Logger
    ):
        """
        初始化Bot

        Args:
            onebot_client: OneBot客户端
            claude_handler: Claude处理器
            config: 配置字典
            logger: 日志器
        """
        self.client = onebot_client
        self.claude = claude_handler
        self.config = config
        self.logger = logger

        # Bot配置
        bot_config = config.get('bot', {})
        self.qq_number = bot_config.get('qq_number', '')
        self.auto_reply_private = bot_config.get('auto_reply_private', True)
        self.ignore_temp_session = bot_config.get('ignore_temp_session', True)
        self.command_prefixes = bot_config.get('command_prefix', ['/c', '/claude', '/问', '/ask'])

        # 消息队列（用于处理并发）
        self.processing_messages: set = set()

        # 心跳检测
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.online_status = True
        self.connection_failures = 0
        self.max_connection_failures = bot_config.get('max_connection_failures', 3)
        self.heartbeat_interval = bot_config.get('heartbeat_interval', 60)  # 秒
        self.heartbeat_enabled = bot_config.get('heartbeat_enabled', True)

        # 状态回调（用于WebUI更新）
        self.status_callbacks = []

    def add_status_callback(self, callback):
        """添加状态变化回调"""
        self.status_callbacks.append(callback)

    async def start_heartbeat(self):
        """启动心跳检测"""
        if not self.heartbeat_enabled:
            self.logger.info("心跳检测已禁用")
            return

        if self.heartbeat_task is None or self.heartbeat_task.done():
            self.logger.info("启动心跳检测...")
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def stop_heartbeat(self):
        """停止心跳检测"""
        if self.heartbeat_task and not self.heartbeat_task.done():
            self.logger.info("停止心跳检测...")
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass

    async def _heartbeat_loop(self):
        """心跳循环"""
        while True:
            try:
                # 等待心跳间隔
                await asyncio.sleep(self.heartbeat_interval)

                # 检查连接状态
                is_connected = self.client.is_connected()

                if not is_connected:
                    self._handle_disconnect("NapCat连接已断开")
                    continue

                # 发送心跳测试
                await self._test_connection()

                # 如果之前失败过，现在恢复正常
                if self.connection_failures > 0:
                    self._handle_reconnect()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"心跳检测异常: {e}", exc_info=True)
                self._handle_disconnect(f"心跳异常: {e}")

    async def _test_connection(self):
        """测试连接"""
        try:
            # 使用WebSocket ping作为心跳测试，而不是API调用
            # 这更安全，不依赖特定的API
            if self.client.websocket and not self.client.websocket.closed:
                # 发送WebSocket ping
                await self.client.websocket.ping()
                self.last_heartbeat_time = asyncio.get_event_loop().time()

                # 连接成功，重置失败计数
                if self.connection_failures > 0:
                    self.logger.info(f"NapCat连接已恢复")
                    self.connection_failures = 0
            else:
                raise ConnectionError("WebSocket未连接")

        except Exception as e:
            self.connection_failures += 1
            self.logger.warning(f"心跳测试失败 ({self.connection_failures}/{self.max_connection_failures}): {e}")

            # 连续失败次数超过阈值，判定为掉线
            if self.connection_failures >= self.max_connection_failures:
                self._handle_disconnect("连续心跳失败，判定为掉线")

    def _handle_disconnect(self, reason: str):
        """处理断开连接"""
        if self.online_status:
            self.logger.error(f"QQ/NapCat连接异常: {reason}")
            self.online_status = False
            self._notify_status_change()

    def _handle_reconnect(self):
        """处理重新连接"""
        if not self.online_status:
            self.logger.info("QQ/NapCat连接已恢复正常")
            self.online_status = True
            self.connection_failures = 0
            self._notify_status_change()

    def _notify_status_change(self):
        """通知状态变化"""
        status = {
            "online": self.online_status,
            "connection_failures": self.connection_failures,
            "timestamp": asyncio.get_event_loop().time()
        }

        # 调用所有回调
        for callback in self.status_callbacks:
            try:
                # 使用inspect.iscoroutinefunction代替asyncio.iscoroutinefunction
                if inspect.iscoroutinefunction(callback):
                    asyncio.create_task(callback(status))
                else:
                    callback(status)
            except Exception as e:
                self.logger.error(f"状态回调失败: {e}", exc_info=True)

    def get_status(self) -> Dict[str, Any]:
        """获取Bot状态"""
        return {
            "online": self.online_status,
            "connection_failures": self.connection_failures,
            "heartbeat_interval": self.heartbeat_interval,
            "client_connected": self.client.is_connected(),
            "message_count": len(self.processing_messages),
            "heartbeat_enabled": self.heartbeat_enabled
        }

    async def on_message(self, data: Dict[str, Any]):
        """
        处理OneBot消息

        Args:
            data: OneBot消息数据
        """
        # 检查是否是消息事件
        if data.get('post_type') != 'message':
            return

        message_type = data.get('message_type')
        user_id = data.get('user_id')
        group_id = data.get('group_id')
        sub_type = data.get('sub_type', '')

        # 生成消息唯一ID（防重复处理）
        message_id = f"{message_type}_{user_id}_{group_id or 'private'}"
        if message_id in self.processing_messages:
            self.logger.debug(f"消息已在处理中，跳过: {message_id}")
            return
        self.processing_messages.add(message_id)

        try:
            if message_type == 'private':
                await self.handle_private_message(data)
            elif message_type == 'group':
                await self.handle_group_message(data)
        except Exception as e:
            self.logger.error(f"处理消息失败: {e}", exc_info=True)
        finally:
            self.processing_messages.discard(message_id)

    async def handle_private_message(self, data: Dict[str, Any]):
        """处理私聊消息"""
        user_id = data.get('user_id')
        sub_type = data.get('sub_type', '')
        message = self.extract_message_text(data.get('message', []))

        self.logger.info(f"[私聊] 用户 {user_id}: {message[:50]}...")

        # 忽略临时会话
        if self.ignore_temp_session and sub_type != 'friend':
            self.logger.debug(f"忽略临时会话: {user_id}")
            return

        # 检查是否是命令
        if self.is_command(message):
            await self.handle_command(data, message)
            return

        # 自动回复
        if self.auto_reply_private:
            await self.reply_to_user(user_id, message)
        else:
            self.logger.debug("私聊自动回复已禁用")

    async def handle_group_message(self, data: Dict[str, Any]):
        """处理群聊消息"""
        group_id = data.get('group_id')
        user_id = data.get('user_id')
        message = self.extract_message_text(data.get('message', []))

        # 检查是否@了机器人
        is_mentioned = data.get('to_me', False)

        if not is_mentioned:
            self.logger.debug(f"[群聊 {group_id}] 未@机器人，忽略")
            return

        self.logger.info(f"[群聊 {group_id}] 用户 {user_id} @Bot: {message[:50]}...")

        # 空消息检查
        if not message.strip():
            self.logger.debug("@消息为空，忽略")
            return

        # 检查是否是命令
        if self.is_command(message):
            await self.handle_command(data, message)
            return

        # 回复消息
        await self.reply_to_group(group_id, message)

    async def handle_command(self, data: Dict[str, Any], message: str):
        """处理命令消息"""
        # 去掉命令前缀
        actual_message = self.strip_command_prefix(message)

        if not actual_message.strip():
            await self.send_error(data, "请输入问题，例如：/c 解释一下这段代码")
            return

        self.logger.info(f"[命令] {actual_message[:50]}...")

        message_type = data.get('message_type')
        if message_type == 'private':
            user_id = data.get('user_id')
            await self.reply_to_user(user_id, actual_message)
        elif message_type == 'group':
            group_id = data.get('group_id')
            await self.reply_to_group(group_id, actual_message)

    async def reply_to_user(self, user_id: int, message: str):
        """回复私聊用户"""
        # 发送"正在思考"提示
        await self.client.send_private_message(user_id, "Claude 正在思考...")

        # 调用Claude
        result = await self.claude.call(message)

        if result['success']:
            answer = result['result']

            # 添加成本信息
            cost = result.get('cost_usd', 0)
            if cost > 0:
                answer += f"\n\n[成本] ${cost:.4f}"

            # 分段发送（QQ消息长度限制）
            await self.send_long_message(
                lambda msg: self.client.send_private_message(user_id, msg),
                answer
            )
        else:
            error = result.get('error', '未知错误')
            await self.client.send_private_message(user_id, f"[错误] {error}")

    async def reply_to_group(self, group_id: int, message: str):
        """回复群聊"""
        # 发送"正在思考"提示
        await self.client.send_group_message(group_id, "Claude 正在思考...")

        # 调用Claude
        result = await self.claude.call(message)

        if result['success']:
            answer = result['result']

            # 添加成本信息
            cost = result.get('cost_usd', 0)
            if cost > 0:
                answer += f"\n\n[成本] ${cost:.4f}"

            # 分段发送
            await self.send_long_message(
                lambda msg: self.client.send_group_message(group_id, msg),
                answer
            )
        else:
            error = result.get('error', '未知错误')
            await self.client.send_group_message(group_id, f"[错误] {error}")

    async def send_long_message(self, send_func, message: str, max_length: int = 2000):
        """发送长消息（自动分段）"""
        if len(message) <= max_length:
            await send_func(message)
        else:
            for i in range(0, len(message), max_length):
                await send_func(message[i:i+max_length])
                await asyncio.sleep(0.5)  # 避免触发频率限制

    async def send_error(self, data: Dict[str, Any], error_msg: str):
        """发送错误消息"""
        message_type = data.get('message_type')
        if message_type == 'private':
            user_id = data.get('user_id')
            await self.client.send_private_message(user_id, f"[错误] {error_msg}")
        elif message_type == 'group':
            group_id = data.get('group_id')
            await self.client.send_group_message(group_id, f"[错误] {error_msg}")

    def extract_message_text(self, message_data: List[Dict[str, Any]]) -> str:
        """从消息数据中提取纯文本"""
        text = ""
        for segment in message_data:
            if segment.get('type') == 'text':
                text += segment.get('data', {}).get('text', '')
        return text.strip()

    def is_command(self, message: str) -> bool:
        """检查是否是命令"""
        for prefix in self.command_prefixes:
            if message.startswith(prefix):
                return True
        return False

    def strip_command_prefix(self, message: str) -> str:
        """去掉命令前缀"""
        for prefix in self.command_prefixes:
            if message.startswith(prefix):
                return message[len(prefix):].strip()
        return message
