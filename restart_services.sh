#!/bin/bash

echo "🔄 重启网址监控工具服务"
echo "========================"

# 杀死现有进程
echo "🛑 停止现有服务..."
pkill -f "python.*run_backend" 2>/dev/null || true
pkill -f "vite.*3000" 2>/dev/null || true
pkill -f "node.*dev" 2>/dev/null || true
sleep 2

# 进入项目根目录
cd "/Users/wangbo/Desktop/代码项目/网址监控"

echo "🚀 启动后端服务..."
# 启动后端服务（后台运行）
source venv/bin/activate && python run_backend.py > backend_server.log 2>&1 &
BACKEND_PID=$!
echo "后端服务 PID: $BACKEND_PID"

echo "⏳ 等待后端服务启动..."
sleep 3

echo "🚀 启动前端服务..."
# 启动前端服务（后台运行）
cd frontend
npm run dev > ../frontend_server.log 2>&1 &
FRONTEND_PID=$!
echo "前端服务 PID: $FRONTEND_PID"

echo "⏳ 等待前端服务启动..."
sleep 5

echo ""
echo "✅ 服务启动完成！"
echo "📡 后端服务: http://localhost:5001"
echo "🌐 前端界面: http://localhost:3000"
echo ""
echo "📋 进程信息:"
echo "后端 PID: $BACKEND_PID"
echo "前端 PID: $FRONTEND_PID"
echo ""
echo "📝 日志文件:"
echo "后端日志: backend_server.log"
echo "前端日志: frontend_server.log"
echo ""
echo "🔍 检查服务状态:"
sleep 2

# 检查端口
if lsof -Pi :5001 -sTCP:LISTEN -t >/dev/null ; then
    echo "✅ 后端服务 (端口5001) 运行正常"
else
    echo "❌ 后端服务 (端口5001) 启动失败"
fi

if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null ; then
    echo "✅ 前端服务 (端口3000) 运行正常"
else
    echo "❌ 前端服务 (端口3000) 启动失败"
fi

echo ""
echo "🎯 请在浏览器中访问: http://localhost:3000"