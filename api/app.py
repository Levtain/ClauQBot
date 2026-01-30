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
    title="Claude QQ Bridge API",
    description="Claude QQ Bridge 后端API",
    version="0.1.0"
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
        "service": "Claude QQ Bridge",
        "version": "0.1.0"
    }


@app.get("/status")
async def get_status():
    """获取服务状态"""
    return {
        "bot_running": bot_client is not None,
        "bot_task_running": bot_task is not None and not bot_task.done()
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

        # 创建Claude处理器
        claude_handler = ClaudeHandler(
            cli_path=config.get('claude.cli_path', 'claude'),
            work_dir=config.get('claude.work_dir', '.'),
            timeout=config.get('claude.timeout', 300),
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
