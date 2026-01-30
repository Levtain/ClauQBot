"""
日志系统模块
"""
import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "claude-qq-bridge",
    level: str = "INFO",
    console: bool = True,
    log_file: Optional[str] = None,
    max_size: int = 10485760,
    backup_count: int = 5
) -> logging.Logger:
    """
    配置日志系统

    Args:
        name: 日志器名称
        level: 日志级别
        console: 是否输出到控制台
        log_file: 日志文件路径
        max_size: 单文件最大大小（字节）
        backup_count: 备份文件数量

    Returns:
        配置好的Logger实例
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    logger.handlers.clear()  # 清除已有的handler

    # 日志格式
    formatter = logging.Formatter(
        fmt='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 控制台输出
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # 文件输出
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "claude-qq-bridge") -> logging.Logger:
    """获取Logger实例"""
    return logging.getLogger(name)
