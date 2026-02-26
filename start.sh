#!/bin/bash
# 编年 (BianNian) - AI 日记助手启动脚本
# 支持 macOS / Linux / Windows (Git Bash / WSL)

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "  编年 - AI 日记助手"
echo "  一个人就是一本"
echo "=========================================="
echo ""

# 检测操作系统
OS="$(uname -s)"
IS_WINDOWS=false

if [[ "$OS" == *"MINGW"* ]] || [[ "$OS" == *"CYGWIN"* ]] || [[ "$OS" == *"MSYS"* ]]; then
    IS_WINDOWS=true
fi

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 python3，请先安装 Python 3.10+"
    exit 1
fi

# 检查 Node.js
if ! command -v npm &> /dev/null; then
    echo "❌ 未找到 npm，请先安装 Node.js 18+"
    exit 1
fi

# 检查并安装后端依赖
echo "📦 检查后端依赖..."
PYTHON_DEPS=("fastapi" "uvicorn" "pydantic" "openai" "httpx")
MISSING_DEPS=()

for dep in "${PYTHON_DEPS[@]}"; do
    if ! python3 -c "import $dep" 2>/dev/null; then
        MISSING_DEPS+=("$dep")
    fi
done

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo "📥 安装后端依赖: ${MISSING_DEPS[*]}"
    pip install "${MISSING_DEPS[@]}" || pip3 install "${MISSING_DEPS[@]}"
fi

# 检查并安装前端依赖
echo ""
echo "📦 检查前端依赖..."
if [ ! -d "web/node_modules" ]; then
    echo "📥 安装前端依赖..."
    cd web
    npm install
    cd ..
fi

echo ""
echo "=========================================="
echo "🚀 启动服务..."
echo "=========================================="
echo ""
echo "📍 后端 API:    http://localhost:8080"
echo "🌐 前端页面:    http://localhost:5173"
echo ""
echo "按 Ctrl+C 停止服务"
echo "=========================================="
echo ""

# 启动后端
echo "🔄 启动后端服务..."
if [ "$IS_WINDOWS" = true ]; then
    # Windows 下使用 start 命令新开窗口
    start "" python3 src/llm.py
else
    # macOS / Linux 后台启动
    python3 src/llm.py &
fi

# 等待后端启动
sleep 2

# 启动前端
echo "🔄 启动前端服务..."
cd web
npm run dev
