#!/bin/bash
# AI From Zero — 启动脚本
# 使用前请设置环境变量 KIMI_API_KEY，或直接修改下方 KEY

cd "$(dirname "$0")/backend"

# API Key 配置（二选一）
# 1. 设置环境变量: export KIMI_API_KEY=your_key
# 2. 直接修改下面这行:
KEY="${KIMI_API_KEY:-REPLACE_WITH_YOUR_KEY}"

if [ "$KEY" = "REPLACE_WITH_YOUR_KEY" ]; then
    echo "⚠️  请先设置 KIMI_API_KEY 环境变量"
    echo "   export KIMI_API_KEY=your_key_here"
    echo "   或者编辑 start.sh 直接填入 Key"
    exit 1
fi

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
echo "📖 访问: http://YOUR_IP:8080（将 YOUR_IP 替换为你的实际IP）"
echo ""
KIMI_API_KEY="$KEY" python3 server.py
