# 快速入门指南

## 5分钟快速启动

### 前置条件

1. **Python 3.8+**
   ```bash
   python3 --version
   ```

2. **Node.js & npm**（可选，用于安装Claude CLI）
   ```bash
   node --version
   npm --version
   ```

3. **OneBot服务**（如NapCat）
   - 下载并安装NapCat
   - 配置反向WebSocket到 `ws://127.0.0.1:8081`
   - 启动NapCat并登录QQ

### 快速安装

```bash
# 1. 进入项目目录
cd /root/claude-qq-bridge

# 2. 运行安装脚本
bash install.sh
```

### 启动服务

```bash
# 方式1: 一键启动所有服务（推荐）
python3 start.py all

# 方式2: 分别启动
# 终端1: 启动API
python3 start.py api

# 终端2: 启动WebUI
python3 start.py webui

# 终端3: 启动Bot
python3 start.py start
```

### 访问界面

- **WebUI管理界面**: http://127.0.0.1:8501
- **API文档**: http://127.0.0.1:8000/docs

### 使用Bot

在QQ中：
1. **私聊**: 直接发送消息
2. **群聊**: @Bot发送消息
3. **命令**: `/c`、`/claude`、`/问`、`/ask`

## 配置OneBot（NapCat示例）

1. 启动NapCat
2. 登录QQ
3. 在NapCat配置中添加反向WebSocket：
   - 地址: `ws://127.0.0.1:8081`
   - 启用: 是
4. 保存并重启NapCat

## 配置Claude

```bash
# 安装Claude CLI
npm install -g @anthropic-ai/claude-code

# 登录
claude auth login
```

## 后台运行

```bash
# 启动daemon
python3 start.py daemon

# 停止daemon
python3 start.py stop
```

## 常见问题

### 1. 端口被占用

修改 `config.yaml` 中的端口号：
```yaml
api:
  port: 8001  # 改为其他端口

webui:
  port: 8502  # 改为其他端口
```

### 2. Claude CLI找不到

编辑 `config.yaml`：
```yaml
claude:
  cli_path: "/path/to/claude"  # 填写完整路径
```

### 3. OneBot连接失败

检查：
- NapCat是否正在运行
- 反向WebSocket地址是否正确
- 防火墙是否阻止连接

## 下一步

- 阅读 [README.md](README.md) 了解更多功能
- 访问 WebUI 进行配置
- 查看 API 文档了解接口使用
- 根据需要修改 `config.yaml`

## 获取帮助

- 查看日志: `tail -f logs/app.log`
- 检查状态: 访问 WebUI "系统状态" 页面
- 提交Issue: GitHub仓库
