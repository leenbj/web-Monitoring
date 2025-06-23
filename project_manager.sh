#!/bin/bash

# 网址监控工具 - 项目管理脚本
# 用于启动、停止和检查项目服务状态

PROJECT_ROOT="/Users/wangbo/Desktop/代码项目/网址监控"
VENV_PATH="$PROJECT_ROOT/venv"
BACKEND_LOG="$PROJECT_ROOT/logs/backend.log"
FRONTEND_LOG="$PROJECT_ROOT/logs/frontend.log"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印带颜色的文本
print_color() {
    local color=$1
    local text=$2
    echo -e "${color}${text}${NC}"
}

# 检查服务状态
check_status() {
    print_color $BLUE "=== 网址监控项目状态检查 ==="
    echo
    
    # 检查后端服务
    print_color $YELLOW "🔴 后端服务状态 (Flask - Port 5001):"
    backend_pid=$(ps aux | grep "run_backend.py" | grep -v grep | awk '{print $2}')
    if [ -n "$backend_pid" ]; then
        print_color $GREEN "  ✅ 后端服务运行中 (PID: $backend_pid)"
        # 测试API连接
        api_response=$(curl -s -m 3 -o /dev/null -w "%{http_code}" http://localhost:5001 2>/dev/null)
        if [ "$api_response" = "200" ]; then
            print_color $GREEN "  ✅ API响应正常 (http://localhost:5001)"
        else
            print_color $RED "  ❌ API响应异常 (状态码: $api_response)"
        fi
    else
        print_color $RED "  ❌ 后端服务未运行"
    fi
    echo
    
    # 检查前端服务
    print_color $YELLOW "🟦 前端服务状态 (Vue.js - Port 3000):"
    frontend_pid=$(ps aux | grep "npm run dev" | grep -v grep | awk '{print $2}')
    if [ -n "$frontend_pid" ]; then
        print_color $GREEN "  ✅ 前端服务运行中 (PID: $frontend_pid)"
        # 测试前端连接
        frontend_response=$(curl -s -m 5 -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null)
        if [ "$frontend_response" = "200" ]; then
            print_color $GREEN "  ✅ 前端界面可访问 (http://localhost:3000)"
        else
            print_color $YELLOW "  ⏳ 前端正在启动中... (状态码: $frontend_response)"
        fi
    else
        print_color $RED "  ❌ 前端服务未运行"
    fi
    echo
    
    # 显示访问地址
    if [ -n "$backend_pid" ] || [ -n "$frontend_pid" ]; then
        print_color $BLUE "🌐 访问地址:"
        if [ -n "$backend_pid" ]; then
            echo "  📡 后端API: http://localhost:5001"
        fi
        if [ -n "$frontend_pid" ]; then
            echo "  🖥️  前端界面: http://localhost:3000"
        fi
        echo
    fi
}

# 启动后端服务
start_backend() {
    print_color $YELLOW "启动后端服务..."
    
    # 检查虚拟环境
    if [ ! -d "$VENV_PATH" ]; then
        print_color $RED "❌ 虚拟环境不存在: $VENV_PATH"
        return 1
    fi
    
    # 激活虚拟环境并启动
    cd "$PROJECT_ROOT"
    source "$VENV_PATH/bin/activate"
    
    # 检查是否已运行
    backend_pid=$(ps aux | grep "run_backend.py" | grep -v grep | awk '{print $2}')
    if [ -n "$backend_pid" ]; then
        print_color $YELLOW "⚠️  后端服务已在运行 (PID: $backend_pid)"
        return 0
    fi
    
    # 启动后端
    nohup python run_backend.py > "$BACKEND_LOG" 2>&1 &
    sleep 3
    
    # 验证启动
    backend_pid=$(ps aux | grep "run_backend.py" | grep -v grep | awk '{print $2}')
    if [ -n "$backend_pid" ]; then
        print_color $GREEN "✅ 后端服务启动成功 (PID: $backend_pid)"
    else
        print_color $RED "❌ 后端服务启动失败，请查看日志: $BACKEND_LOG"
        return 1
    fi
}

# 启动前端服务
start_frontend() {
    print_color $YELLOW "启动前端服务..."
    
    # 检查是否已运行
    frontend_pid=$(ps aux | grep "npm run dev" | grep -v grep | awk '{print $2}')
    if [ -n "$frontend_pid" ]; then
        print_color $YELLOW "⚠️  前端服务已在运行 (PID: $frontend_pid)"
        return 0
    fi
    
    # 进入前端目录
    cd "$PROJECT_ROOT/frontend"
    
    # 检查依赖
    if [ ! -d "node_modules" ]; then
        print_color $YELLOW "📦 安装前端依赖..."
        npm install
    fi
    
    # 启动前端
    nohup npm run dev > "$FRONTEND_LOG" 2>&1 &
    sleep 5
    
    # 验证启动
    frontend_pid=$(ps aux | grep "npm run dev" | grep -v grep | awk '{print $2}')
    if [ -n "$frontend_pid" ]; then
        print_color $GREEN "✅ 前端服务启动成功 (PID: $frontend_pid)"
    else
        print_color $RED "❌ 前端服务启动失败，请查看日志: $FRONTEND_LOG"
        return 1
    fi
}

# 停止服务
stop_services() {
    print_color $YELLOW "停止所有服务..."
    
    # 停止后端
    backend_pid=$(ps aux | grep "run_backend.py" | grep -v grep | awk '{print $2}')
    if [ -n "$backend_pid" ]; then
        kill $backend_pid
        print_color $GREEN "✅ 后端服务已停止"
    fi
    
    # 停止前端
    frontend_pid=$(ps aux | grep "npm run dev" | grep -v grep | awk '{print $2}')
    if [ -n "$frontend_pid" ]; then
        kill $frontend_pid
        print_color $GREEN "✅ 前端服务已停止"
    fi
    
    # 清理node进程
    pkill -f "vite.*3000" 2>/dev/null || true
    
    echo
    print_color $GREEN "🛑 所有服务已停止"
}

# 重启服务
restart_services() {
    print_color $YELLOW "重启所有服务..."
    stop_services
    sleep 2
    start_backend
    start_frontend
    echo
    check_status
}

# 查看日志
show_logs() {
    local service=$1
    case $service in
        "backend")
            print_color $BLUE "=== 后端服务日志 ==="
            tail -f "$BACKEND_LOG"
            ;;
        "frontend")
            print_color $BLUE "=== 前端服务日志 ==="
            tail -f "$FRONTEND_LOG"
            ;;
        *)
            print_color $YELLOW "选择要查看的日志:"
            echo "1) 后端日志"
            echo "2) 前端日志"
            read -p "请输入选项 (1-2): " choice
            case $choice in
                1) show_logs "backend" ;;
                2) show_logs "frontend" ;;
                *) print_color $RED "无效选项" ;;
            esac
            ;;
    esac
}

# 打开浏览器
open_browser() {
    print_color $YELLOW "正在打开浏览器..."
    if command -v open >/dev/null; then
        open http://localhost:3000
    elif command -v xdg-open >/dev/null; then
        xdg-open http://localhost:3000
    else
        print_color $YELLOW "请手动打开浏览器访问: http://localhost:3000"
    fi
}

# 显示帮助
show_help() {
    print_color $BLUE "=== 网址监控工具管理脚本 ==="
    echo
    echo "用法: $0 [命令]"
    echo
    echo "命令:"
    echo "  status     检查服务状态"
    echo "  start      启动所有服务"
    echo "  stop       停止所有服务"
    echo "  restart    重启所有服务"
    echo "  backend    仅启动后端服务"
    echo "  frontend   仅启动前端服务"
    echo "  logs       查看服务日志"
    echo "  open       打开浏览器"
    echo "  help       显示此帮助信息"
    echo
    echo "示例:"
    echo "  $0 start    # 启动完整项目"
    echo "  $0 status   # 查看运行状态"
    echo "  $0 logs     # 查看日志"
    echo
}

# 主函数
main() {
    case ${1:-status} in
        "status")
            check_status
            ;;
        "start")
            start_backend
            start_frontend
            echo
            check_status
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            restart_services
            ;;
        "backend")
            start_backend
            ;;
        "frontend")
            start_frontend
            ;;
        "logs")
            show_logs $2
            ;;
        "open")
            open_browser
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_color $RED "未知命令: $1"
            echo
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@" 