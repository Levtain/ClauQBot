# Claude QQ Bridge

一个通过OneBot协议连接QQ和Claude的桥接服务，支持私聊、群聊、命令模式，提供WebUI管理界面。

## 🏗️ 核心架构

```
QQ客户端 (Windows)
  ↓ (DLL注入)
NapCat (OneBot v11协议) ⭐ 核心组件
  ↓ (反向WebSocket)
Claude QQ Bridge (我们的项目) 🤖 智能处理器
  ↓ (subprocess)
Claude Code CLI
  ↓ (API)
Claude AI
```

**重要说明**:
- **NapCat**: 负责注入QQ框架，获取和发送QQ消息（必须组件）
- **Claude QQ Bridge**: 我们的项目，作为"胶水"连接NapCat和Claude（智能处理）
- **分工明确**: NapCat负责"通信"，我们负责"智能"

## 📦 为什么选择NapCat？

| 特性 | NapCat | Lagrange.OneBot | 其他方案 |
|------|--------|----------------|----------|
| **稳定性** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **维护活跃度** | 活跃 | 较活跃 | 停滞 |
| **QQ版本支持** | 最新版 | 部分版本 | 旧版本 |
| **注入方式** | Windows Hook | 逆向协议 | WebQQ |
| **功能完整性** | 完整 | 基本 | 有限 |

**结论**: NapCat是目前最稳定、最可靠的OneBot实现，是生产环境的首选方案。

## ✨ 功能特性

- ✅ **私聊自动回复** - 直接私聊Bot，自动回复
- ✅ **群聊@唤起** - 在群聊中@Bot触发回复
- ✅ **命令模式** - 支持 `/c`、`/claude`、`/问`、`/ask` 等命令
- ✅ **多轮对话** - 每个群/私聊独立会话
- ✅ **成本显示** - 显示每次对话的API成本
- ✅ **后台运行** - 支持daemon模式
- ✅ **日志系统** - 完整的日志记录和轮转
- ✅ **WebUI管理** - 可视化配置和管理界面
- ✅ **REST API** - 完整的API接口
- ✅ **NapCat集成** - 自动下载、配置、启动NapCat

## 🏗️ 技术栈

### 我们的项目
- **后端**: FastAPI（异步API服务）
- **前端**: Streamlit（WebUI）
- **Bot逻辑**: Python（消息处理、Claude调用）
- **配置**: YAML
- **日志**: Python logging

### 核心依赖
- **NapCat**: QQ注入 + OneBot v11协议（必须）
- **Claude Code CLI**: Claude API调用（必须）
- **Python 3.8+**: 运行环境
- **Node.js**: NapCat依赖

## 📦 安装

### 方法1: 自动安装（推荐）

```bash
# 1. 进入项目目录
cd /root/claude-qq-bridge

# 2. 运行快速安装脚本
bash install.sh

# 3. 一键启动（包括NapCat）
python3 start.py all-with-napcat
```

### 方法2: 手动安装

#### 1. 安装Python依赖

```bash
pip install -r requirements.txt
```

#### 2. 安装Claude Code CLI

```bash
npm install -g @anthropic-ai/claude-code
claude auth login
```

#### 3. 安装NapCat

**自动安装**:
```bash
python3 start.py install-napcat
```

**手动安装**:
1. 访问 https://github.com/NapNeko/NapCatQQ
2. 下载最新Windows版本（Zip包）
3. 解压到 `napcat/` 目录

#### 4. 配置NapCat

```bash
python3 start.py configure-napcat
```

然后手动在NapCat GUI中配置：
- 反向WebSocket地址: `ws://127.0.0.1:8081`
- 启用反向WebSocket: 是

## 🚀 使用

### 方式1: 一键启动（包括NapCat）⭐ 推荐

```bash
python3 start.py all-with-napcat
```

这个命令会：
1. 检查并安装NapCat（如果需要）
2. 配置NapCat
3. 启动NapCat
4. 等待你手动登录QQ并配置NapCat
5. 启动FastAPI + Streamlit + Bot

### 方式2: 分步启动

```bash
# 终端1: 启动NapCat
python3 start.py install-napcat  # 首次安装
./napcat/NapCatWinBootMain.exe   # 启动NapCat
# 然后在NapCat GUI中登录QQ并配置反向WebSocket

# 终端2: 启动所有服务
python3 start.py all
```

### 方式3: 只启动Bot（需先启动NapCat）

```bash
python3 start.py start
```

### 方式4: 后台daemon模式

```bash
# 启动daemon
python3 start.py daemon

# 停止daemon
python3 start.py stop
```

### 方式5: 分别启动各服务

```bash
# 启动API
python3 start.py api

# 启动WebUI
python3 start.py webui
```

## 🌐 访问界面

启动成功后：
- **WebUI管理界面**: http://127.0.0.1:8501
- **API文档**: http://127.0.0.1:8000/docs
- **NapCat GUI**: 自动打开

## ⚙️ 配置

编辑 `config.yaml` 文件进行配置：

### 网络配置
```yaml
network:
  onebot_ws_url: "ws://127.0.0.1:8081"  # OneBot WebSocket地址
  reconnect_interval: 5  # 重连间隔（秒）
  timeout: 30  # 超时时间（秒）
```

### Claude配置
```yaml
claude:
  cli_path: "claude"  # Claude CLI路径
  work_dir: "."  # 工作目录
  timeout: 300  # 超时时间（秒）
```

### Bot配置
```yaml
bot:
  qq_number: ""  # Bot QQ号
  auto_reply_private: true  # 私聊自动回复
  ignore_temp_session: true  # 忽略临时会话
  command_prefix: ["/c", "/claude", "/问", "/ask"]  # 命令前缀
```

### 日志配置
```yaml
logging:
  level: "INFO"  # 日志级别
  console: true  # 输出到控制台
  file:
    enabled: true  # 输出到文件
    path: "logs/app.log"  # 日志文件路径
    max_size: 10485760  # 单文件最大大小（10MB）
    backup_count: 5  # 备份文件数量
```

详细配置请查看配置文件注释。

## 🎯 使用方式

### 私聊模式

直接私聊Bot，无需命令：
```
你好
```

### 群聊模式

在群聊中@Bot：
```
@Claude 解释一下这段代码
```

### 命令模式

使用命令前缀：
```
/c 解释一下这段代码
/claude 什么是量子计算
/问 今天天气怎么样
```

## 🌐 WebUI

访问 http://127.0.0.1:8501 打开WebUI，可以：
- 启动/停止/重启Bot
- 查看服务状态
- 修改配置（无需手动编辑YAML）
- 查看系统信息

## 🔌 API接口

### GET /
获取服务信息

### GET /status
获取Bot状态

### GET /config
获取配置

### POST /config
更新配置

### POST /bot/start
启动Bot

### POST /bot/stop
停止Bot

### POST /bot/restart
重启Bot

示例：
```bash
# 启动Bot
curl -X POST http://127.0.0.1:8000/bot/start

# 获取状态
curl http://127.0.0.1:8000/status

# 停止Bot
curl -X POST http://127.0.0.1:8000/bot/stop
```

## 📝 项目结构

```
claude-qq-bridge/
├── napcat/                    # NapCat（核心组件）
│   ├── NapCatWinBootMain.exe  # 启动器
│   ├── NapCatWinBootHook.dll  # Hook DLL
│   ├── napcat.mjs             # Node.js主程序
│   ├── node_modules/          # Node.js依赖
│   └── config/
│       └── napcat.json        # NapCat配置
├── src/                       # 核心代码
│   ├── config.py              # 配置管理
│   ├── logger.py              # 日志系统
│   ├── onebot_client.py       # OneBot客户端
│   ├── claude_handler.py      # Claude调用处理
│   └── bot.py                 # Bot核心逻辑
├── api/                       # FastAPI后端
│   └── app.py
├── webui/                     # Streamlit前端
│   └── app.py
├── config.yaml                # 配置文件
├── start.py                   # 一键启动脚本
├── install.sh                  # 快速安装脚本
├── requirements.txt           # Python依赖
├── README.md                  # 本文档
├── QUICKSTART.md              # 快速入门
└── NAPCAT_SETUP.md            # NapCat集成指南
```

## 🐛 常见问题

### Q1: Bot无法连接到OneBot

**原因**: NapCat未运行或配置错误

**解决**:
1. 确认NapCat正在运行
2. 在NapCat GUI中配置反向WebSocket到 `ws://127.0.0.1:8081`
3. 确认QQ已登录
4. 查看NapCat日志

### Q2: Claude调用失败

**原因**: Claude CLI未安装或路径错误

**解决**:
1. 安装Claude CLI: `npm install -g @anthropic-ai/claude-code`
2. 配置API密钥: `claude auth login`
3. 检查 `config.yaml` 中的 `claude.cli_path` 是否正确

### Q3: WebUI无法访问

**原因**: WebUI服务未启动或端口冲突

**解决**:
1. 确认已执行 `python3 start.py all`
2. 检查端口8501是否被占用
3. 检查防火墙设置

### Q4: NapCat无法注入QQ

**原因**: QQ版本不兼容或杀毒软件拦截

**解决**:
1. 更新NapCat到最新版
2. 将NapCat添加到杀毒软件白名单
3. 以管理员权限运行NapCat

## 🔄 与原方案对比

| 特性 | 原方案 (QQBot) | 新方案 (Claude QQ Bridge) |
|------|----------------|---------------------------|
| 架构 | NoneBot2 + 自定义插件 | 独立FastAPI服务 ✅ |
| 配置 | 硬编码代码 | YAML + WebUI ✅ |
| 管理界面 | 无 | Streamlit WebUI ✅ |
| API | 无 | REST API ✅ |
| 后台运行 | 手动 | 原生daemon ✅ |
| 日志 | print | 完整日志系统 ✅ |
| NapCat集成 | 手动 | 自动下载/配置/启动 ✅ |
| 可维护性 | 中等 | 高 ✅ |
| 可扩展性 | 低 | 高 ✅ |

## 🎯 下一步计划

- [ ] 消息队列（并发处理）
- [ ] 会话持久化
- [ ] 权限控制（白名单/黑名单）
- [ ] 成本统计和预警
- [ ] 日志查看界面
- [ ] 多项目支持
- [ ] 插件系统
- [ ] Docker部署
- [ ] 一键安装脚本（Windows/Mac）
- [ ] NapCat GUI集成到WebUI

## 📄 许可证

MIT License

## 👥 贡献

欢迎提交Issue和Pull Request！

## 📞 联系方式

- 作者: 蜡烛 + Claude (AI参谋)
- 项目位置: `/root/claude-qq-bridge`
- NapCat GitHub: https://github.com/NapNeko/NapCatQQ

## 📚 相关文档

- [快速入门指南](QUICKSTART.md)
- [NapCat集成指南](NAPCAT_SETUP.md)

---

**最后更新**: 2025-01-30
**版本**: v0.1.0
