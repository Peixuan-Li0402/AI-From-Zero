#!/bin/bash
# AI From Zero — OpenClaw Skill 启动脚本
# 用法: bash start.sh

cd "$(dirname "$0")/backend"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 需要 Python 3.10+"
    exit 1
fi

# 检查依赖
pip list 2>/dev/null | grep -q fastapi || {
    echo "📦 正在安装依赖..."
    pip install -r requirements.txt -q
}

echo "🐾 启动 AI From Zero 服务..."
echo "📖 访问: http://YOUR_IP:8080"
echo ""
python3 server.py
