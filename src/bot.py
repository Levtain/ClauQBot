"""
Bot核心逻辑模块
"""
import re
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
                import asyncio
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
