#!/bin/bash

# 杏仁 AI-Center 启动脚本

set -e

echo "🌰 启动杏仁 AI-Center..."

# 检查环境变量
if [ ! -f .env ]; then
    echo "⚠️  未找到 .env 文件"
    echo "📝 正在创建 .env 文件..."
    cp .env.example .env
    echo "✅ 已创建 .env 文件，请编辑它并填入你的 API Key"
    exit 1
fi

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "📦 创建虚拟环境..."
    uv venv
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source .venv/bin/activate

# 安装依赖
echo "📥 安装依赖..."
uv pip install -e ".[dev]"

# 设置日志目录
mkdir -p logs

# 启动服务
echo "🚀 启动服务..."
echo ""
echo "访问以下地址："
echo "  - API 文档: http://localhost:8000/docs"
echo "  - 健康检查: http://localhost:8000/v1/health"
echo ""

# 根据参数选择启动模式
if [ "$1" == "prod" ]; then
    echo "🏭 生产模式启动（4 workers）..."
    uvicorn ai_center.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --workers 4 \
        --log-level info
else
    echo "🔧 开发模式启动（支持热重载）..."
    uvicorn ai_center.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --reload \
        --log-level debug
fi