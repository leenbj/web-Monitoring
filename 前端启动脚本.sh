#!/bin/bash

echo "🔧 网址监控工具 - 前端启动脚本"
echo "=================================="

# 进入前端目录
cd /Users/wangbo/Desktop/代码项目/网址监控/frontend

echo "📋 检查环境..."

# 检查Node.js版本
echo "Node.js 版本: $(node --version)"
echo "npm 版本: $(npm --version)"

# 检查依赖
echo ""
echo "📦 检查依赖安装状态..."
if [ ! -d "node_modules" ]; then
    echo "⚠️  node_modules不存在，正在安装依赖..."
    npm install
else
    echo "✅ 依赖已安装"
fi

# 检查端口
echo ""
echo "🔍 检查端口3000..."
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  端口3000已被占用，正在释放..."
    pkill -f "vite.*3000" 2>/dev/null || true
    sleep 2
fi

echo ""
echo "🚀 启动前端开发服务器..."
echo "访问地址: http://localhost:3000"
echo "按 Ctrl+C 停止服务器"
echo ""

# 启动开发服务器
npm run dev

echo ""
echo "🛑 前端服务器已停止" 