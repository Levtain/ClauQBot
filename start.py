#!/usr/bin/env python3
"""
Claude QQ Bridge 一键启动脚本

NapCat是核心组件，用于注入QQ框架并提供OneBot v11协议接口。
我们的项目作为"胶水"，将NapCat和Claude连接起来。
"""
import sys
import os
import argparse
import subprocess
import signal
import requests
import zipfile
from pathlib import Path


# NapCat配置
NAPCAT_DIR = Path(__file__).parent / "napcat"
NAPCAT_DOWNLOAD_URL = "https://github.com/NapNeko/NapCatQQ/releases/latest/download/NapCatQQ.zip"
NAPCAT_EXE = NAPCAT_DIR / "NapCatWinBootMain.exe"


def install_napcat():
    """下载并安装NapCat"""
    print("=" * 50)
    print("  下载并安装NapCat")
    print("=" * 50)

    # 检查是否已安装
    if NAPCAT_EXE.exists():
        print(f"✅ NapCat已安装: {NAPCAT_DIR}")
        return

    # 创建目录
    NAPCAT_DIR.mkdir(parents=True, exist_ok=True)

    # 下载
    print(f"正在从 {NAPCAT_DOWNLOAD_URL} 下载NapCat...")
    try:
        response = requests.get(NAPCAT_DOWNLOAD_URL, stream=True)
        response.raise_for_status()

        # 保存到临时文件
        temp_zip = NAPCAT_DIR / "NapCatQQ.zip"
        with open(temp_zip, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print("✅ 下载完成")

        # 解压
        print("正在解压...")
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            zip_ref.extractall(NAPCAT_DIR.parent)

        print("✅ 解压完成")

        # 删除zip文件
        temp_zip.unlink()

        print(f"✅ NapCat安装成功: {NAPCAT_DIR}")

    except Exception as e:
        print(f"❌ 安装失败: {e}")
        print("请手动下载NapCat并解压到 napcat/ 目录")
        sys.exit(1)


def configure_napcat():
    """自动配置NapCat"""
    print("=" * 50)
    print("  配置NapCat")
    print("=" * 50)

    napcat_config_file = NAPCAT_DIR / "config" / "napcat.json"

    # 创建config目录
    napcat_config_file.parent.mkdir(parents=True, exist_ok=True)

    # 读取当前配置
    config = {}
    if napcat_config_file.exists():
        import json
        with open(napcat_config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

    # 更新配置
    config.update({
        "fileLog": False,
        "consoleLog": True,
        "fileLogLevel": "debug",
        "consoleLogLevel": "info",
        "packetBackend": "auto",
        "packetServer": "",
        "o3HookMode": 1
    })

    # 保存配置
    import json
    with open(napcat_config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"✅ NapCat配置已更新: {napcat_config_file}")
    print("\n请手动在NapCat GUI中配置反向WebSocket:")
    print("  - 连接地址: ws://127.0.0.1:8081")
    print("  - 启用反向WebSocket: 是")


def start_napcat():
    """启动NapCat"""
    if not NAPCAT_EXE.exists():
        print(f"❌ NapCat未找到: {NAPCAT_EXE}")
        print("请运行: python3 start.py install-napcat")
        return None

    print(f"正在启动NapCat: {NAPCAT_EXE}")
    try:
        process = subprocess.Popen(
            [str(NAPCAT_EXE)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print(f"✅ NapCat已启动 (PID: {process.pid})")
        print("请在NapCat GUI中:")
        print("  1. 登录QQ")
        print("  2. 配置反向WebSocket: ws://127.0.0.1:8081")
        return process
    except Exception as e:
        print(f"❌ 启动NapCat失败: {e}")
        return None


def daemonize():
    """将进程转为后台daemon"""
    try:
        pid = os.fork()
        if pid > 0:
            # 父进程退出
            sys.exit(0)
    except OSError as e:
        print(f"Fork失败: {e}", file=sys.stderr)
        sys.exit(1)

    # 子进程继续
    os.chdir("/")
    os.setsid()
    os.umask(0)

    try:
        pid = os.fork()
        if pid > 0:
            # 父进程退出
            sys.exit(0)
    except OSError as e:
        print(f"Second fork失败: {e}", file=sys.stderr)
        sys.exit(1)

    # 重定向标准输入输出
    sys.stdout.flush()
    sys.stderr.flush()
    sys.stdin.close()
    sys.stdout.close()
    sys.stderr.close()


def start_daemon():
    """启动daemon模式"""
    print("正在启动后台daemon...")

    # 读取配置
    import yaml
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)

    daemon_config = config_data.get('daemon', {})
    pid_file = Path(daemon_config.get('pid_file', '/tmp/claude-qq-bridge.pid'))
    log_file = Path(daemon_config.get('log_file', 'logs/daemon.log'))

    # 检查是否已在运行
    if pid_file.exists():
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        try:
            os.kill(pid, 0)
            print(f"Daemon已在运行中 (PID: {pid})", file=sys.stderr)
            sys.exit(1)
        except OSError:
            # 进程不存在，清理旧PID文件
            pid_file.unlink()

    # 转为daemon
    daemonize()

    # 写入PID文件
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))

    # 重定向输出到日志文件
    log_file.parent.mkdir(parents=True, exist_ok=True)
    sys.stdout = open(log_file, 'a')
    sys.stderr = open(log_file, 'a')

    print(f"Daemon启动成功 (PID: {os.getpid()})")

    # 启动服务
    start_services(daemon=True)


def stop_daemon():
    """停止daemon"""
    import yaml
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)

    daemon_config = config_data.get('daemon', {})
    pid_file = Path(daemon_config.get('pid_file', '/tmp/claude-qq-bridge.pid'))

    if not pid_file.exists():
        print("Daemon未运行", file=sys.stderr)
        sys.exit(1)

    with open(pid_file, 'r') as f:
        pid = int(f.read().strip())

    try:
        os.kill(pid, signal.SIGTERM)
        print(f"Daemon已停止 (PID: {pid})")
        pid_file.unlink()
    except OSError as e:
        print(f"停止daemon失败: {e}", file=sys.stderr)
        sys.exit(1)


def start_services(daemon=False):
    """启动服务"""
    import asyncio
    from src.config import config
    from src.logger import setup_logger, get_logger
    from src.onebot_client import OneBotClient
    from src.claude_handler import ClaudeHandler
    from src.bot import Bot

    # 加载配置
    config_path = Path(__file__).parent / "config.yaml"
    config.load(str(config_path))

    # 配置日志
    log_level = config.get('logging.level', 'INFO')
    log_console = config.get('logging.console', True) if not daemon else False
    log_file = config.get('logging.file.path') if config.get('logging.file.enabled') else None

    setup_logger(
        level=log_level,
        console=log_console,
        log_file=log_file,
        max_size=config.get('logging.file.max_size', 10485760),
        backup_count=config.get('logging.file.backup_count', 5)
    )

    logger = get_logger(__name__)
    logger.info("=" * 50)
    logger.info("Claude QQ Bridge 启动中...")
    logger.info("=" * 50)
    logger.info("NapCat是核心组件，负责注入QQ框架并提供OneBot协议接口")
    logger.info("我们的项目作为'胶水'，连接NapCat和Claude")

    async def run_bot():
        """运行Bot"""
        # 创建OneBot客户端
        onebot_client = OneBotClient(
            ws_url=config.get('network.onebot_ws_url'),
            on_message=None,  # 稍后设置
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

        # 设置消息回调
        onebot_client.on_message = lambda data: asyncio.create_task(bot_client.on_message(data))

        # 连接OneBot
        logger.info("正在连接到NapCat (OneBot)...")
        await onebot_client.connect()

        # 监听消息
        logger.info("开始监听消息...")
        await onebot_client.listen()

    # 运行Bot
    asyncio.run(run_bot())


def start_api():
    """启动FastAPI服务"""
    print("启动FastAPI服务...")
    subprocess.run([
        sys.executable,
        "-m",
        "uvicorn",
        "api.app:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
        "--reload"
    ])


def start_webui():
    """启动Streamlit服务"""
    print("启动Streamlit服务...")
    subprocess.run([
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "webui/app.py",
        "--server.port",
        "8501",
        "--server.address",
        "127.0.0.1"
    ])


def start_all():
    """启动所有服务"""
    print("启动所有服务...")
    print("FastAPI API: http://127.0.0.1:8000")
    print("Streamlit WebUI: http://127.0.0.1:8501")
    print("按 Ctrl+C 停止服务\n")

    # 启动API和WebUI（子进程）
    api_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.app:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    webui_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "webui/app.py", "--server.port", "8501", "--server.address", "127.0.0.1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    try:
        # 等待进程
        api_process.wait()
        webui_process.wait()
    except KeyboardInterrupt:
        print("\n正在停止服务...")
        api_process.terminate()
        webui_process.terminate()
        api_process.wait()
        webui_process.wait()
        print("服务已停止")


def start_all_with_napcat():
    """启动所有服务（包括NapCat）"""
    print("=" * 60)
    print("  Claude QQ Bridge - 完整启动（含NapCat）")
    print("=" * 60)
    print()

    # 1. 检查NapCat
    print("[1/4] 检查NapCat...")
    if not NAPCAT_EXE.exists():
        print("❌ NapCat未安装，正在下载...")
        install_napcat()
        configure_napcat()
    else:
        print("✅ NapCat已安装")

    print()

    # 2. 启动NapCat
    print("[2/4] 启动NapCat...")
    napcat_process = start_napcat()
    if not napcat_process:
        print("❌ NapCat启动失败")
        return

    print()

    # 3. 等待NapCat启动
    print("[3/4] 等待NapCat启动（请手动登录QQ并配置反向WebSocket）...")
    print("   NapCat GUI中配置:")
    print("   - 反向WebSocket地址: ws://127.0.0.1:8081")
    print("   - 启用反向WebSocket: 是")
    print()
    input("配置完成后按回车继续...")

    print()

    # 4. 启动我们的服务
    print("[4/4] 启动Claude QQ Bridge服务...")
    print()

    # 启动API和WebUI（子进程）
    api_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.app:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    webui_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "webui/app.py", "--server.port", "8501", "--server.address", "127.0.0.1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # 启动Bot（在当前线程）
    try:
        start_services()
    except KeyboardInterrupt:
        print("\n正在停止所有服务...")
    finally:
        api_process.terminate()
        webui_process.terminate()
        napcat_process.terminate()
        api_process.wait()
        webui_process.wait()
        napcat_process.wait()
        print("所有服务已停止")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Claude QQ Bridge - 一键启动脚本",
        epilog="NapCat是核心组件，负责注入QQ框架并提供OneBot协议接口"
    )
    parser.add_argument(
        "command",
        choices=[
            'start', 'stop', 'daemon',
            'api', 'webui', 'all',
            'install-napcat', 'configure-napcat',
            'all-with-napcat'
        ],
        help="""
            start           - 启动Bot（需要先手动启动NapCat）
            stop            - 停止daemon
            daemon          - 后台daemon模式
            api             - 启动FastAPI服务
            webui           - 启动Streamlit WebUI
            all             - 启动API + WebUI
            install-napcat  - 下载并安装NapCat
            configure-napcat - 自动配置NapCat
            all-with-napcat - 启动所有服务（包括NapCat）
        """
    )

    args = parser.parse_args()

    # 切换到脚本目录
    os.chdir(Path(__file__).parent)

    if args.command == 'daemon':
        start_daemon()
    elif args.command == 'stop':
        stop_daemon()
    elif args.command == 'api':
        start_api()
    elif args.command == 'webui':
        start_webui()
    elif args.command == 'all':
        start_all()
    elif args.command == 'install-napcat':
        install_napcat()
    elif args.command == 'configure-napcat':
        configure_napcat()
    elif args.command == 'all-with-napcat':
        start_all_with_napcat()
    else:  # start
        start_services()


if __name__ == "__main__":
    main()
