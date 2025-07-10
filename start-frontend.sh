#!/bin/bash

# 网址监控工具 - 前端启动脚本
# 用于快速启动和测试前端应用

echo "🚀 网址监控工具 - 前端启动脚本"
echo "=================================="

# 检查是否在正确的目录
if [ ! -d "frontend" ]; then
    echo "❌ 错误：请在项目根目录运行此脚本"
    exit 1
fi

# 进入前端目录
cd frontend

echo "📦 检查前端依赖..."
if [ ! -d "node_modules" ]; then
    echo "📥 正在安装前端依赖..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ 依赖安装失败"
        exit 1
    fi
else
    echo "✅ 前端依赖已存在"
fi

echo "🔨 检查构建文件..."
if [ ! -d "dist" ]; then
    echo "🏗️  正在构建前端应用..."
    npm run build
    if [ $? -ne 0 ]; then
        echo "❌ 构建失败"
        exit 1
    fi
else
    echo "✅ 构建文件已存在"
fi

echo "🌐 启动前端服务..."
echo "访问地址: http://localhost:4173"
echo "按 Ctrl+C 停止服务"
echo "--------------------------------"

# 启动预览服务
npm run preview 