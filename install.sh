#!/bin/bash
# 快速安装脚本

set -e

echo "========================================"
echo "  ClauQBot 快速安装"
echo "========================================"
echo ""

# 检查Python
echo "[1/4] 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "Python版本: $PYTHON_VERSION"

if [ $(echo "$PYTHON_VERSION 3.8" | awk '{print ($1 < $2)}') -eq 1 ]; then
    echo "错误: Python版本过低，需要3.8+"
    exit 1
fi

# 安装Python依赖
echo ""
echo "[2/4] 安装Python依赖..."
pip3 install -r requirements.txt

# 检查Node.js和npm
echo ""
echo "[3/4] 检查Node.js环境..."
if ! command -v node &> /dev/null; then
    echo "警告: 未找到Node.js，Claude CLI安装将跳过"
    echo "请手动安装: npm install -g @anthropic-ai/claude-code"
else
    echo "Node.js版本: $(node -v)"

    # 安装Claude CLI
    echo ""
    echo "[4/4] 安装Claude CLI..."
    if command -v claude &> /dev/null; then
        echo "Claude CLI已安装"
    else
        echo "正在安装Claude CLI..."
        npm install -g @anthropic-ai/claude-code
        echo "Claude CLI安装完成"
    fi
fi

echo ""
echo "========================================"
echo "  安装完成！"
echo "========================================"
echo ""
echo "使用方法:"
echo "  1. 启动所有服务: python3 start.py all"
echo "  2. 只启动Bot:   python3 start.py start"
echo "  3. 后台daemon:   python3 start.py daemon"
echo ""
echo "WebUI: http://127.0.0.1:8501"
echo "API:   http://127.0.0.1:8000"
echo ""
echo "请先配置OneBot服务（如NapCat）并启动，然后再启动Bot"
echo ""
