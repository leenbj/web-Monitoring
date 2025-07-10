#!/bin/bash
"""
前端开发服务器启动脚本
用于在本地启动前端开发环境
"""

cd "$(dirname "$0")/frontend"

echo "=================================================="
echo "🚀 启动网址监控前端开发服务器"
echo "=================================================="
echo "📅 启动时间: $(date)"
echo "📁 前端目录: $(pwd)"
echo ""

# 检查Node.js版本
echo "🔍 检查Node.js环境..."
node --version
npm --version
echo ""

# 检查后端API是否可用
echo "🔍 检查后端API连接..."
if curl -s http://localhost:15000/api/health > /dev/null; then
    echo "✅ 后端API运行正常 (http://localhost:15000)"
else
    echo "❌ 后端API无法连接，请先启动后端服务"
    echo "   运行命令: sudo ./deploy-backend-only.sh"
    exit 1
fi
echo ""

# 检查依赖
if [ ! -d "node_modules" ]; then
    echo "📦 安装前端依赖..."
    npm install
fi

# 启动开发服务器
echo "🚀 启动前端开发服务器..."
echo "   访问地址: http://localhost:3000"
echo "   API代理:  http://localhost:3000/api -> http://localhost:15000/api"
echo ""
echo "按 Ctrl+C 停止服务器"
echo "=================================================="

npm run dev 