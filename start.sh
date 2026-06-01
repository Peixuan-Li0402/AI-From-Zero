#!/bin/bash
# AI From Zero — 启动脚本
# KIMI_API_KEY 可选；未设置时会启用本地术语匹配降级模式。

cd "$(dirname "$0")/backend"

if [ -f "../.env" ]; then
    set -a
    . "../.env"
    set +a
fi

LLM_PROVIDER="${LLM_PROVIDER:-kimi}"
if [ -z "${LLM_API_KEY:-}" ] && [ -z "${KIMI_API_KEY:-}" ] && [ "$LLM_PROVIDER" != "ollama" ]; then
    echo "⚠️  未设置 LLM_API_KEY，将使用本地术语匹配模式"
    echo "   如需完整 LLM 分析，请打开网页点「配置模型」，或运行: export LLM_API_KEY=your_key_here"
else
    echo "✅ 已配置 LLM provider: $LLM_PROVIDER，将启用完整 LLM 分析"
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
echo "📖 访问: http://localhost:${APP_PORT:-8080}"
echo ""
python3 server.py
