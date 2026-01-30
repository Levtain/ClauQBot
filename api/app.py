"""
FastAPI后端服务
"""
import asyncio
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, WebSocket
from pydantic import BaseModel
from pathlib import Path
import sys
import logging

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import config
from src.logger import setup_logger, get_logger
from src.onebot_client import OneBotClient
from src.claude_handler import ClaudeHandler
from src.bot import Bot


# 日志
logger = get_logger(__name__)

# FastAPI应用
app = FastAPI(
    title="ClauQBot API",
    description="ClauQBot 后端API",
    version="0.2.0"
)

# 全局变量
bot_client: Optional[Bot] = None
bot_task: Optional[asyncio.Task] = None


class ConfigModel(BaseModel):
    """配置模型"""
    network: Optional[Dict[str, Any]] = None
    proxy: Optional[Dict[str, Any]] = None
    claude: Optional[Dict[str, Any]] = None
    bot: Optional[Dict[str, Any]] = None
    daemon: Optional[Dict[str, Any]] = None
    logging: Optional[Dict[str, Any]] = None
    webui: Optional[Dict[str, Any]] = None
    api: Optional[Dict[str, Any]] = None


@app.on_event("startup")
async def startup():
    """启动事件"""
    global bot_client, bot_task

    logger.info("FastAPI 服务启动中...")

    # 启动Bot
    await start_bot()


@app.on_event("shutdown")
async def shutdown():
    """关闭事件"""
    global bot_client, bot_task

    logger.info("FastAPI 服务关闭中...")

    # 停止Bot
    await stop_bot()


@app.get("/")
async def root():
    """根路径"""
    return {
        "status": "running",
        "service": "ClauQBot",
        "version": "0.2.0"
    }


@app.get("/status")
async def get_status():
    """
    获取服务状态（简化版）
    """
    return {
        "bot_running": bot_client is not None,
        "bot_task_running": bot_task is not None and not bot_task.done()
    }


@app.get("/status/detailed")
async def get_detailed_status():
    """
    获取详细的服务状态（包含心跳和连接信息）
    """
    if bot_client is None:
        return {
            "bot_running": False,
            "message": "Bot未运行"
        }

    # 获取Bot详细状态
    bot_status = bot_client.get_status()

    # 获取Claude重试统计
    claude_stats = bot_client.claude.get_retry_stats()

    return {
        "bot_running": True,
        "bot_status": bot_status,
        "claude_handler": claude_stats,
        "onebot": {
            "connected": bot_client.client.is_connected(),
            "last_heartbeat": bot_client.client.get_last_heartbeat_time()
        },
        "timestamp": asyncio.get_event_loop().time()
    }


@app.get("/config")
async def get_config():
    """获取配置"""
    return config.to_dict()


@app.post("/config")
async def update_config(config_data: ConfigModel):
    """更新配置"""
    config_dict = config_data.dict(exclude_unset=True)
    for key, value in config_dict.items():
        config.set(key, value)
    return {"status": "success", "message": "配置已更新"}


@app.post("/bot/start")
async def start_bot():
    """启动Bot"""
    global bot_client, bot_task

    if bot_client is not None:
        return {"status": "error", "message": "Bot已在运行"}

    try:
        # 创建OneBot客户端
        onebot_client = OneBotClient(
            ws_url=config.get('network.onebot_ws_url'),
            on_message=lambda data: asyncio.create_task(bot_client.on_message(data)),
            logger=logger,
            reconnect_interval=config.get('network.reconnect_interval', 5),
            timeout=config.get('network.timeout', 30)
        )

        # 创建Claude处理器（带重试）
        claude_handler = ClaudeHandler(
            cli_path=config.get('claude.cli_path', 'claude'),
            work_dir=config.get('claude.work_dir', '.'),
            timeout=config.get('claude.timeout', 300),
            max_retries=config.get('claude.max_retries', 3),
            initial_backoff=config.get('claude.initial_backoff', 1.0),
            max_backoff=config.get('claude.max_backoff', 60.0),
            logger=logger
        )

        # 创建Bot
        bot_client = Bot(
            onebot_client=onebot_client,
            claude_handler=claude_handler,
            config=config.to_dict(),
            logger=logger
        )

        # 连接OneBot
        await onebot_client.connect()

        # 启动监听任务
        bot_task = asyncio.create_task(onebot_client.listen())

        # 启动心跳检测
        await bot_client.start_heartbeat()

        logger.info("Bot启动成功，心跳检测已启用")

        return {"status": "success", "message": "Bot已启动"}
    except Exception as e:
        logger.error(f"启动Bot失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/bot/stop")
async def stop_bot():
    """停止Bot"""
    global bot_client, bot_task

    if bot_client is None:
        return {"status": "error", "message": "Bot未运行"}

    try:
        # 停止心跳检测
        if bot_client:
            await bot_client.stop_heartbeat()

        # 断开OneBot连接
        await bot_client.client.disconnect()

        # 取消任务
        if bot_task:
            bot_task.cancel()
            try:
                await bot_task
            except asyncio.CancelledError:
                pass

        bot_client = None
        bot_task = None

        logger.info("Bot已停止")

        return {"status": "success", "message": "Bot已停止"}
    except Exception as e:
        logger.error(f"停止Bot失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/bot/restart")
async def restart_bot():
    """重启Bot"""
    await stop_bot()
    await asyncio.sleep(1)
    await start_bot()
    return {"status": "success", "message": "Bot已重启"}


if __name__ == "__main__":
    import uvicorn

    # 加载配置
    config_path = Path(__file__).parent.parent / "config.yaml"
    config.load(str(config_path))

    # 配置日志
    setup_logger(
        level=config.get('logging.level', 'INFO'),
        console=config.get('logging.console', True),
        log_file=config.get('logging.file.path') if config.get('logging.file.enabled') else None,
        max_size=config.get('logging.file.max_size', 10485760),
        backup_count=config.get('logging.file.backup_count', 5)
    )

    # 启动服务
    api_config = config.get('api', {})
    uvicorn.run(
        "api.app:app",
        host=api_config.get('host', '127.0.0.1'),
        port=api_config.get('port', 8000),
        reload=True
    )
