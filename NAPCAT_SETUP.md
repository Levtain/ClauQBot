# NapCat 集成指南

## 为什么选择NapCat？

NapCat是目前最稳定、最可靠的OneBot实现：

| 特性 | NapCat | Lagrange.OneBot | 其他方案 |
|------|--------|----------------|----------|
| **稳定性** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **维护活跃度** | 活跃 | 较活跃 | 停滞 |
| **QQ版本支持** | 最新版 | 部分版本 | 旧版本 |
| **注入方式** | Windows Hook | 逆向协议 | WebQQ |
| **性能** | 优秀 | 良好 | 一般 |
| **功能完整性** | 完整 | 基本 | 有限 |

**结论**: NapCat是生产环境的首选方案。

---

## NapCat工作原理

```
QQ客户端
  ↓ (DLL注入)
NapCat (Node.js)
  ↓ (OneBot v11协议)
我们的ClauQBot
  ↓
Claude CLI
```

NapCat通过DLL注入QQ进程，拦截QQ消息并通过OneBot v11协议（WebSocket）转发给我们的服务。

---

## 快速集成NapCat

### 方法1: 自动下载（推荐）

我们的项目会自动下载最新版NapCat：

```bash
python3 start.py install-napcat
```

### 方法2: 手动下载

1. 访问NapCat GitHub: https://github.com/NapNeko/NapCatQQ
2. 下载最新Windows版本（Zip包）
3. 解压到项目目录的 `napcat/` 文件夹

---

## NapCat配置

### 1. 基本配置

编辑 `napcat/config/napcat.json`:

```json
{
  "fileLog": false,
  "consoleLog": true,
  "fileLogLevel": "debug",
  "consoleLogLevel": "info",
  "packetBackend": "auto",
  "packetServer": "",
  "o3HookMode": 1
}
```

### 2. 反向WebSocket配置

在NapCat GUI中配置：

- **启用反向WebSocket**: ✅ 是
- **连接地址**: `ws://127.0.0.1:8081`
- **重连间隔**: 5000ms
- **心跳间隔**: 30000ms

### 3. 自动配置脚本

我们的项目会自动生成NapCat配置：

```bash
python3 start.py configure-napcat
```

---

## 启动顺序

```
1. 启动QQ客户端
   ↓
2. 启动NapCat (NapCatWinBootMain.exe)
   ↓
3. NapCat连接到我们的WebSocket服务器 (ws://127.0.0.1:8081)
   ↓
4. 启动我们的Bot服务 (python3 start.py start)
   ↓
5. 开始收发消息
```

### 一键启动

```bash
python3 start.py all-with-napcat
```

这个命令会：
1. 启动QQ客户端（如果已配置路径）
2. 启动NapCat
3. 等待NapCat连接
4. 启动我们的Bot服务

---

## NapCat目录结构

```
napcat/
├── NapCatWinBootMain.exe      # 启动器（双击启动）
├── NapCatWinBootHook.dll      # Hook DLL（注入QQ的核心）
├── napcat.mjs                 # Node.js主程序
├── node_modules/              # Node.js依赖
├── config/
│   └── napcat.json            # NapCat配置文件
└── data/                      # 数据目录（会话缓存等）
```

---

## WebUI集成NapCat控制

我们会在WebUI中添加NapCat控制面板：

- ✅ NapCat状态监控
- ✅ 一键启动/停止NapCat
- ✅ 反向WebSocket配置
- ✅ 日志查看
- ✅ QQ账号管理

---

## NapCat与我们的关系

**重要概念**: NapCat是**消息来源**，我们的项目是**消息处理器**。

```
NapCat (消息源)
  ↓ (OneBot协议)
ClauQBot (消息处理器)
  ↓ (调用Claude)
Claude AI (回复生成)
  ↓ (返回结果)
ClauQBot (格式化回复)
  ↓ (OneBot协议)
NapCat (发送到QQ)
  ↓
用户收到消息
```

**NapCat提供的能力**:
- 接收QQ消息（私聊、群聊）
- 发送QQ消息
- 获取好友列表、群列表
- 获取群成员信息
- 其他QQ操作（撤回消息、@提醒等）

**我们的项目提供的能力**:
- 处理收到的消息（过滤、路由）
- 调用Claude CLI生成回复
- 格式化消息（分段、成本显示）
- 配置管理、日志记录、WebUI管理

**分工明确**: NapCat负责"通信"，我们负责"智能"。

---

## 为什么不能用纯Python实现？

常见的误解：

**Q: 为什么不直接用Python逆向QQ协议？**

A:
1. **技术难度极高** - QQ协议加密复杂，逆向成本巨大
2. **容易被封号** - 逆向协议容易被腾讯检测和封禁
3. **维护成本高** - QQ版本更新需要重新逆向
4. **功能不完整** - 逆向无法支持所有QQ功能

**NapCat的优势**:
1. **官方思路** - 通过DLL注入，不破坏协议
2. **稳定性强** - 不易被检测
3. **功能完整** - 支持所有QQ功能
4. **持续维护** - 活跃的开源社区

**结论**: 重复造轮子不值得，NapCat是最优解。

---

## 故障排查

### Q1: NapCat无法注入QQ

**原因**: QQ版本不兼容或杀毒软件拦截

**解决**:
1. 更新NapCat到最新版
2. 将NapCat添加到杀毒软件白名单
3. 以管理员权限运行NapCat

### Q2: NapCat无法连接到我们的服务

**原因**: 反向WebSocket配置错误或我们的服务未启动

**解决**:
1. 确认我们的服务已启动: `python3 start.py start`
2. 检查NapCat配置中的WebSocket地址: `ws://127.0.0.1:8081`
3. 查看NapCat日志

### Q3: QQ版本更新后NapCat失效

**原因**: QQ版本更新导致Hook失效

**解决**:
1. 更新NapCat到最新版
2. 等待NapCat适配新版本
3. 暂时降级QQ版本

---

## NapCat资源

- **GitHub**: https://github.com/NapNeko/NapCatQQ
- **文档**: https://napneko.github.io/
- **社区**: Discord / QQ群

---

**总结**: NapCat是必须的核心组件，我们的项目是它的智能扩展。二者结合才能构成完整的解决方案。
