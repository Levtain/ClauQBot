"""
Streamlit WebUI前端
"""
import streamlit as st
import requests
import time
from pathlib import Path
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# API地址
API_URL = "http://127.0.0.1:8000"

# 页面配置
st.set_page_config(
    page_title="ClauQBot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .status-running {
        color: #00c853;
        font-weight: bold;
    }
    .status-stopped {
        color: #d32f2f;
        font-weight: bold;
    }
    .status-warning {
        color: #ff9800;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


def get_status():
    """获取服务状态"""
    try:
        response = requests.get(f"{API_URL}/status")
        return response.json()
    except Exception as e:
        return {"bot_running": False, "bot_task_running": False, "error": str(e)}


def get_detailed_status():
    """获取详细的服务状态"""
    try:
        response = requests.get(f"{API_URL}/status/detailed")
        return response.json()
    except Exception as e:
        return {}


def get_config():
    """获取配置"""
    try:
        response = requests.get(f"{API_URL}/config")
        return response.json()
    except Exception as e:
        st.error(f"获取配置失败: {e}")
        return {}


def update_config(config_data):
    """更新配置"""
    try:
        response = requests.post(f"{API_URL}/config", json=config_data)
        return response.json()
    except Exception as e:
        st.error(f"更新配置失败: {e}")
        return {"status": "error"}


def start_bot():
    """启动Bot"""
    try:
        response = requests.post(f"{API_URL}/bot/start")
        return response.json()
    except Exception as e:
        st.error(f"启动Bot失败: {e}")
        return {"status": "error"}


def stop_bot():
    """停止Bot"""
    try:
        response = requests.post(f"{API_URL}/bot/stop")
        return response.json()
    except Exception as e:
        st.error(f"停止Bot失败: {e}")
        return {"status": "error"}


def restart_bot():
    """重启Bot"""
    try:
        response = requests.post(f"{API_URL}/bot/restart")
        return response.json()
    except Exception as e:
        st.error(f"重启Bot失败: {e}")
        return {"status": "error"}


def main():
    """主界面"""

    # 标题
    st.markdown('<div class="main-header">🤖 ClauQBot 管理面板</div>', unsafe_allow_html=True)

    # 侧边栏
    with st.sidebar:
        st.header("控制面板")

        # 状态
        status = get_status()
        bot_running = status.get('bot_running', False)

        if bot_running:
            st.markdown('<div class="status-running">● Bot 运行中</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-stopped">● Bot 已停止</div>', unsafe_allow_html=True)

        st.divider()

        # Bot控制按钮
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("▶️ 启动", use_container_width=True, disabled=bot_running):
                result = start_bot()
                if result.get('status') == 'success':
                    st.success("Bot启动成功！")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"启动失败: {result.get('message')}")

        with col2:
            if st.button("⏹️ 停止", use_container_width=True, disabled=not bot_running):
                result = stop_bot()
                if result.get('status') == 'success':
                    st.success("Bot已停止")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"停止失败: {result.get('message')}")

        with col3:
            if st.button("🔄 重启", use_container_width=True, disabled=not bot_running):
                result = restart_bot()
                if result.get('status') == 'success':
                    st.success("Bot已重启")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"重启失败: {result.get('message')}")

        st.divider()

        # 导航
        page = st.radio(
            "页面导航",
            ["🏠 首页", "⚙️ 配置管理", "📊 系统状态"],
            label_visibility="collapsed"
        )

    # 主内容区
    if page == "🏠 首页":
        st.header("欢迎使用 ClauQBot")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📖 快速开始")
            st.markdown("""
            1. 在左侧点击 **▶️ 启动** 按钮启动Bot
            2. 确保OneBot服务（如NapCat）正在运行
            3. 在QQ中私聊或@Bot与Claude对话
            4. 使用 **⚙️ 配置管理** 调整配置
            """)

        with col2:
            st.subheader("📝 功能特性")
            st.markdown("""
            - ✅ 私聊自动回复
            - ✅ 群聊@唤起
            - ✅ 命令模式（/c, /claude, /问, /ask）
            - ✅ 多轮对话
            - ✅ 成本显示
            - ✅ 后台运行
            - ✅ 日志系统
            - ✅ 心跳检测
            - ✅ 错误重试
            """)

        st.divider()
        st.subheader("🔧 技术栈")
        st.markdown("""
        - **后端**: FastAPI（异步API服务）
        - **前端**: Streamlit（快速开发WebUI）
        - **Bot框架**: OneBot v11协议
        - **AI调用**: Claude Code CLI
        - **日志**: Python logging
        - **心跳**: 每60秒检测连接状态
        - **重试**: 指数退避策略
        """)

    elif page == "⚙️ 配置管理":
        st.header("配置管理")

        # 获取当前配置
        config = get_config()

        # 分组显示配置
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🌐 网络配置",
            "🤖 Claude配置",
            "🎯 Bot配置",
            "📝 日志配置",
            "🔧 其他配置"
        ])

        with tab1:
            st.subheader("网络配置")
            network = config.get('network', {})

            onebot_ws_url = st.text_input(
                "OneBot WebSocket地址",
                value=network.get('onebot_ws_url', 'ws://127.0.0.1:8081'),
                help="OneBot服务器的WebSocket地址"
            )

            reconnect_interval = st.number_input(
                "重连间隔（秒）",
                value=network.get('reconnect_interval', 5),
                min_value=1,
                max_value=60
            )

            timeout = st.number_input(
                "超时时间（秒）",
                value=network.get('timeout', 30),
                min_value=5,
                max_value=300
            )

            st.divider()
            st.subheader("代理配置")
            proxy = config.get('proxy', {})

            proxy_enabled = st.checkbox("启用代理", value=proxy.get('enabled', False))
            http_proxy = st.text_input(
                "HTTP代理",
                value=proxy.get('http_proxy', ''),
                disabled=not proxy_enabled
            )
            https_proxy = st.text_input(
                "HTTPS代理",
                value=proxy.get('https_proxy', ''),
                disabled=not proxy_enabled
            )
            no_proxy = st.text_input(
                "不使用代理的地址",
                value=proxy.get('no_proxy', 'localhost,127.0.0.1'),
                disabled=not proxy_enabled
            )

        with tab2:
            st.subheader("Claude配置")
            claude = config.get('claude', {})

            cli_path = st.text_input(
                "Claude CLI路径",
                value=claude.get('cli_path', 'claude'),
                help="Claude Code CLI的完整路径或命令名"
            )

            work_dir = st.text_input(
                "工作目录",
                value=claude.get('work_dir', '.'),
                help="Claude的工作目录（项目根目录）"
            )

            timeout = st.number_input(
                "超时时间（秒）",
                value=claude.get('timeout', 300),
                min_value=10,
                max_value=3600
            )

            st.divider()
            st.subheader("错误重试配置")

            max_retries = st.number_input(
                "最大重试次数",
                value=claude.get('max_retries', 3),
                min_value=0,
                max_value=10,
                help="调用失败时的重试次数"
            )

            initial_backoff = st.number_input(
                "初始退避时间（秒）",
                value=claude.get('initial_backoff', 1.0),
                min_value=0.1,
                max_value=10.0,
                step=0.1,
                help="首次重试前的等待时间"
            )

            max_backoff = st.number_input(
                "最大退避时间（秒）",
                value=claude.get('max_backoff', 60.0),
                min_value=1.0,
                max_value=300.0,
                step=1.0,
                help="重试等待时间的最大值"
            )

        with tab3:
            st.subheader("Bot配置")
            bot = config.get('bot', {})

            qq_number = st.text_input(
                "Bot QQ号",
                value=bot.get('qq_number', ''),
                help="用于识别@消息"
            )

            auto_reply_private = st.checkbox(
                "私聊自动回复",
                value=bot.get('auto_reply_private', True)
            )

            ignore_temp_session = st.checkbox(
                "忽略临时会话",
                value=bot.get('ignore_temp_session', True)
            )

            command_prefix_str = st.text_input(
                "命令前缀（逗号分隔）",
                value=', '.join(bot.get('command_prefix', ['/c', '/claude', '/问', '/ask']))
            )

            st.divider()
            st.subheader("心跳检测配置")

            heartbeat_enabled = st.checkbox(
                "启用心跳检测",
                value=bot.get('heartbeat_enabled', True),
                help="定期检测NapCat连接状态"
            )

            heartbeat_interval = st.number_input(
                "心跳间隔（秒）",
                value=bot.get('heartbeat_interval', 60),
                min_value=10,
                max_value=600,
                disabled=not heartbeat_enabled,
                help="心跳检测的时间间隔"
            )

            max_connection_failures = st.number_input(
                "连续失败阈值",
                value=bot.get('max_connection_failures', 3),
                min_value=1,
                max_value=10,
                disabled=not heartbeat_enabled,
                help="连续失败多少次判定为掉线"
            )

        with tab4:
            st.subheader("日志配置")
            logging_config = config.get('logging', {})

            level = st.selectbox(
                "日志级别",
                ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                index=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"].index(
                    logging_config.get('level', 'INFO')
                )
            )

            console = st.checkbox("输出到控制台", value=logging_config.get('console', True))

            file_enabled = st.checkbox("输出到文件", value=logging_config.get('file', {}).get('enabled', True))

            if file_enabled:
                file_config = logging_config.get('file', {})
                file_path = st.text_input(
                    "日志文件路径",
                    value=file_config.get('path', 'logs/app.log')
                )
                max_size = st.number_input(
                    "单文件最大大小（MB）",
                    value=file_config.get('max_size', 10485760) // 1048576,
                    min_value=1,
                    max_value=100
                )
                backup_count = st.number_input(
                    "备份文件数量",
                    value=file_config.get('backup_count', 5),
                    min_value=1,
                    max_value=20
                )

        with tab5:
            st.subheader("API配置")
            api = config.get('api', {})

            api_enabled = st.checkbox("启用API", value=api.get('enabled', True))
            api_host = st.text_input(
                "API监听地址",
                value=api.get('host', '127.0.0.1'),
                disabled=not api_enabled
            )
            api_port = st.number_input(
                "API端口",
                value=api.get('port', 8000),
                min_value=1024,
                max_value=65535,
                disabled=not api_enabled
            )

            st.divider()
            st.subheader("WebUI配置")
            webui = config.get('webui', {})

            webui_enabled = st.checkbox("启用WebUI", value=webui.get('enabled', True))
            webui_host = st.text_input(
                "WebUI监听地址",
                value=webui.get('host', '127.0.0.1'),
                disabled=not webui_enabled
            )
            webui_port = st.number_input(
                "WebUI端口",
                value=webui.get('port', 8501),
                min_value=1024,
                max_value=65535,
                disabled=not webui_enabled
            )

        # 保存按钮
        st.divider()
        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("💾 保存配置", use_container_width=True, type="primary"):
                # 构建配置数据
                config_data = {
                    "network": {
                        "onebot_ws_url": onebot_ws_url,
                        "reconnect_interval": reconnect_interval,
                        "timeout": timeout
                    },
                    "proxy": {
                        "enabled": proxy_enabled,
                        "http_proxy": http_proxy,
                        "https_proxy": https_proxy,
                        "no_proxy": no_proxy
                    },
                    "claude": {
                        "cli_path": cli_path,
                        "work_dir": work_dir,
                        "timeout": timeout,
                        "max_retries": max_retries,
                        "initial_backoff": initial_backoff,
                        "max_backoff": max_backoff
                    },
                    "bot": {
                        "qq_number": qq_number,
                        "auto_reply_private": auto_reply_private,
                        "ignore_temp_session": ignore_temp_session,
                        "command_prefix": [p.strip() for p in command_prefix_str.split(',')],
                        "heartbeat_enabled": heartbeat_enabled,
                        "heartbeat_interval": heartbeat_interval,
                        "max_connection_failures": max_connection_failures
                    },
                    "logging": {
                        "level": level,
                        "console": console,
                        "file": {
                            "enabled": file_enabled,
                            "path": file_path if file_enabled else '',
                            "max_size": max_size * 1048576 if file_enabled else 0,
                            "backup_count": backup_count if file_enabled else 0
                        }
                    },
                    "api": {
                        "enabled": api_enabled,
                        "host": api_host,
                        "port": api_port
                    },
                    "webui": {
                        "enabled": webui_enabled,
                        "host": webui_host,
                        "port": webui_port
                    }
                }

                result = update_config(config_data)
                if result.get('status') == 'success':
                    st.success("配置已保存！重启Bot以应用新配置。")
                else:
                    st.error(f"保存失败: {result.get('message')}")

        with col2:
            if st.button("🔄 重置为默认", use_container_width=True):
                st.warning("重置功能暂未实现")

    elif page == "📊 系统状态":
        st.header("系统状态")

        # 详细状态
        detailed_status = get_detailed_status()

        # Bot状态
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🤖 Bot状态")

            if not detailed_status:
                st.error("❌ Bot未运行或无法获取状态")
            else:
                bot_status = detailed_status.get('bot_status', {})

                # 在线状态
                online = bot_status.get('online', False)
                if online:
                    st.success("✅ Bot 在线")
                else:
                    st.error("❌ Bot 离线")
                    st.warning("NapCat连接可能已断开")

                st.json(bot_status)

        with col2:
            st.subheader("🌐 OneBot连接状态")

            if not detailed_status:
                st.error("❌ 无法获取状态")
            else:
                onebot = detailed_status.get('onebot', {})
                connected = onebot.get('connected', False)

                if connected:
                    st.success("✅ OneBot 已连接")
                else:
                    st.error("❌ OneBot 未连接")

                last_heartbeat = onebot.get('last_heartbeat')
                if last_heartbeat:
                    import time as time_module
                    elapsed = time_module.time() - last_heartbeat
                    if elapsed < 60:
                        st.success(f"✅ 心跳正常（{elapsed:.1f}秒前）")
                    else:
                        st.warning(f"⚠️ 心跳异常（{elapsed:.1f}秒前）")

                st.json(onebot)

        st.divider()

        # Claude状态
        st.subheader("🤖 Claude调用状态")

        if not detailed_status:
            st.error("❌ 无法获取状态")
        else:
            claude_handler = detailed_status.get('claude_handler', {})
            st.json(claude_handler)

            # 显示重试配置
            st.write("**重试配置:**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("最大重试次数", claude_handler.get('max_retries', 0))
            with col2:
                st.metric("初始退避(秒)", f"{claude_handler.get('initial_backoff', 0):.1f}")
            with col3:
                st.metric("最大退避(秒)", f"{claude_handler.get('max_backoff', 0):.1f}")

        st.divider()

        # API状态
        st.subheader("🌐 API状态")
        try:
            response = requests.get(f"{API_URL}/")
            if response.status_code == 200:
                st.success("✅ API 服务正常")
                st.json(response.json())
            else:
                st.error(f"❌ API 服务异常: {response.status_code}")
        except Exception as e:
            st.error(f"❌ API 连接失败: {e}")

        st.divider()

        # 当前配置
        st.subheader("📝 当前配置")
        st.json(get_config())


if __name__ == "__main__":
    main()
