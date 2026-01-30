# ClauQBot GitHub Release Notes

## v0.1.0 - Initial Release (2025-01-30)

### 🎉 首次发布

ClauQBot 是一个通过OneBot协议连接QQ和Claude的桥接服务，支持私聊、群聊、命令模式，提供WebUI管理界面。

### ✨ 核心功能

#### Bot功能
- ✅ 私聊自动回复 - 直接私聊Bot，自动回复
- ✅ 群聊@唤起 - 在群聊中@Bot触发回复
- ✅ 命令模式 - 支持 `/c`、`/claude`、`/问`、`/ask` 等命令
- ✅ 多轮对话 - 每个群/私聊独立会话
- ✅ 成本显示 - 显示每次对话的API成本
- ✅ 临时会话过滤 - 自动忽略非好友临时会话

#### 系统功能
- ✅ NapCat集成 - 自动下载、配置、启动NapCat
- ✅ WebUI管理 - Streamlit可视化配置界面
- ✅ REST API - 完整的API接口
- ✅ 后台运行 - 支持daemon模式
- ✅ 日志系统 - 完整的日志记录和轮转
- ✅ 配置管理 - YAML配置文件

### 🏗️ 技术架构

```
QQ客户端 (Windows)
  ↓ (DLL注入)
NapCat (OneBot v11协议) ⭐ 核心组件
  ↓ (反向WebSocket)
ClauQBot (我们的项目) 🤖 智能处理器
  ↓ (subprocess)
Claude Code CLI
  ↓ (API)
Claude AI
```

### 📦 技术栈

- **后端**: FastAPI (异步API服务)
- **前端**: Streamlit (WebUI)
- **Bot逻辑**: Python (消息处理、Claude调用)
- **配置**: YAML
- **日志**: Python logging
- **核心依赖**: NapCat (QQ注入 + OneBot v11)、Claude Code CLI

### 🚀 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/Levtain/ClauQBot.git
cd ClauQBot

# 2. 安装依赖
bash install.sh

# 3. 一键启动（包括NapCat）
python3 start.py all-with-napcat
```

### 📝 文件清单

```
ClauQBot/
├── src/                  # 核心代码
│   ├── config.py         # 配置管理
│   ├── logger.py         # 日志系统
│   ├── onebot_client.py  # OneBot客户端
│   ├── claude_handler.py # Claude调用处理
│   └── bot.py            # Bot核心逻辑
├── api/                  # FastAPI后端
│   └── app.py
├── webui/                # Streamlit前端
│   └── app.py
├── config.yaml           # 配置文件
├── start.py              # 一键启动脚本
├── install.sh            # 快速安装脚本
├── requirements.txt      # Python依赖
├── README.md             # 完整文档
├── QUICKSTART.md         # 快速入门
├── NAPCAT_SETUP.md      # NapCat集成指南
├── CONTRIBUTING.md      # 贡献指南
└── LICENSE              # MIT License
```

### 🌐 访问地址

启动成功后：
- **WebUI**: http://127.0.0.1:8501
- **API文档**: http://127.0.0.1:8000/docs

### 📊 项目统计

- **总文件数**: 18个
- **代码行数**: ~2900行
- **支持Python版本**: 3.8+
- **许可证**: MIT

### 🐛 已知问题

- NapCat QQ状态监控待实现
- Windows平台部分功能需要管理员权限
- WebUI日志查看功能待完善

### 🎯 下一步计划

#### 优先级P0（核心功能）
- [ ] 心跳检测（NapCat连接状态）
- [ ] 消息队列（并发处理）
- [ ] 会话持久化
- [ ] 错误重试机制

#### 优先级P1（体验优化）
- [ ] 日志查看界面
- [ ] 成本统计和预警
- [ ] 权限控制（白名单/黑名单）
- [ ] NapCat状态监控

#### 优先级P2（高级功能）
- [ ] 多项目支持
- [ ] 插件系统
- [ ] Docker部署
- [ ] 一键安装脚本（Windows/Mac）
- [ ] NapCat GUI集成到WebUI

### 👥 贡献者

- 蜡烛 - 项目发起人
- Claude (AI) - 技术实现

### 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

### 🔗 相关链接

- **项目仓库**: https://github.com/Levtain/ClauQBot
- **NapCat GitHub**: https://github.com/NapNeko/NapCatQQ
- **Claude Code CLI**: https://github.com/anthropics/claude-code
- **Issues**: https://github.com/Levtain/ClauQBot/issues
- **Discussions**: https://github.com/Levtain/ClauQBot/discussions

### 💬 联系方式

- GitHub Issues: [提交问题](https://github.com/Levtain/ClauQBot/issues)
- Pull Requests: 欢迎提交PR

---

**感谢使用 ClauQBot！🎉**
