"""
Claude调用处理模块
"""
import subprocess
import asyncio
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging


class ClaudeHandler:
    """Claude CLI调用处理器"""

    def __init__(
        self,
        cli_path: str = "claude",
        work_dir: str = ".",
        timeout: int = 300,
        logger: Optional[logging.Logger] = None
    ):
        """
        初始化Claude处理器

        Args:
            cli_path: Claude CLI路径
            work_dir: 工作目录
            timeout: 超时时间（秒）
            logger: 日志器
        """
        self.cli_path = cli_path
        self.work_dir = Path(work_dir).resolve()
        self.timeout = timeout
        self.logger = logger or logging.getLogger(__name__)

        # 确保工作目录存在
        self.work_dir.mkdir(parents=True, exist_ok=True)

    def _find_claude_cli(self) -> Optional[str]:
        """查找Claude CLI路径"""
        # 优先使用配置的路径
        if self.cli_path != "claude":
            if Path(self.cli_path).exists():
                return self.cli_path

        # 尝试在PATH中查找
        import shutil
        claude_path = shutil.which("claude")
        if claude_path:
            return claude_path

        # 尝试常见位置
        common_paths = [
            os.path.expanduser("~/AppData/Roaming/npm/claude.cmd"),  # Windows
            os.path.expanduser("~/.npm-global/bin/claude"),  # Linux/Mac
            "/usr/local/bin/claude",  # Linux/Mac
        ]

        for path in common_paths:
            if Path(path).exists():
                return path

        return None

    async def call(self, message: str) -> Dict[str, Any]:
        """
        调用Claude CLI（异步）

        Args:
            message: 用户消息

        Returns:
            {
                "success": bool,
                "result": str,  # Claude的回复
                "cost_usd": float,  # API成本（美元）
                "error": str  # 错误信息
            }
        """
        claude_path = self._find_claude_cli()
        if not claude_path:
            return {
                "success": False,
                "error": "找不到Claude CLI，请确认已安装：npm install -g @anthropic-ai/claude-code"
            }

        self.logger.info(f"调用Claude: {message[:50]}...")

        # 在线程池中执行同步调用
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self._call_sync,
            claude_path,
            message
        )

        return result

    def _call_sync(self, claude_path: str, message: str) -> Dict[str, Any]:
        """
        同步调用Claude CLI

        Args:
            claude_path: Claude CLI路径
            message: 用户消息

        Returns:
            结果字典
        """
        cmd = [
            claude_path,
            "-p",  # 项目模式
            "--output-format",
            "json",
            message
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                encoding='utf-8',
                errors='replace',
                timeout=self.timeout,
                cwd=str(self.work_dir),
                check=False
            )

            # 解析输出
            output = result.stdout.strip()
            if not output:
                return {
                    "success": False,
                    "error": "Claude无响应"
                }

            # 尝试解析JSON
            try:
                data = json.loads(output)
            except json.JSONDecodeError:
                # 如果不是JSON格式，直接返回原始输出
                return {
                    "success": True,
                    "result": output,
                    "cost_usd": 0
                }

            # 提取结果
            if isinstance(data, dict):
                success = data.get("success", True)
                result_text = data.get("result", data.get("response", ""))
                cost = data.get("cost_usd", 0)
                error = data.get("error", "")

                return {
                    "success": success,
                    "result": result_text,
                    "cost_usd": cost,
                    "error": error
                }
            else:
                return {
                    "success": True,
                    "result": str(data),
                    "cost_usd": 0
                }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Claude响应超时（超过{self.timeout}秒）"
            }
        except FileNotFoundError:
            return {
                "success": False,
                "error": f"Claude CLI不存在：{claude_path}"
            }
        except Exception as e:
            self.logger.error(f"调用Claude失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"调用失败: {str(e)}"
            }

    def get_work_dir(self) -> Path:
        """获取工作目录"""
        return self.work_dir
