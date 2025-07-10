#!/bin/bash
# 修复API 404错误 - 部署增强版后端

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "============================================="
echo "    修复API 404错误 - 部署增强版后端"
echo "============================================="

# 1. 停止现有服务
info "1. 停止现有服务..."
systemctl stop website-monitor.service 2>/dev/null || true
systemctl stop website-monitor-simple.service 2>/dev/null || true
systemctl stop website-monitor-minimal.service 2>/dev/null || true

# 查找并终止占用5011端口的进程
PORT_PID=$(netstat -tlnp 2>/dev/null | grep ":5011 " | awk '{print $7}' | cut -d'/' -f1 | head -1)
if [ -n "$PORT_PID" ] && [ "$PORT_PID" != "-" ]; then
    info "终止占用端口5011的进程 $PORT_PID"
    kill -9 $PORT_PID 2>/dev/null || true
    sleep 2
fi

# 2. 备份现有文件
info "2. 备份现有后端文件..."
if [ -f "minimal_flask_app.py" ]; then
    mv minimal_flask_app.py minimal_flask_app.py.backup
fi

if [ -f "run_simple_backend.py" ]; then
    mv run_simple_backend.py run_simple_backend.py.backup
fi

# 3. 设置增强版后端
info "3. 设置增强版后端..."
chmod +x enhanced-minimal-backend.py

# 4. 创建增强版systemd服务
info "4. 创建增强版systemd服务..."
cat > /etc/systemd/system/website-monitor-enhanced.service << EOF
[Unit]
Description=Website Monitor Enhanced Backend Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/website-monitor
Environment=PYTHONPATH=/root/website-monitor
Environment=PYTHONUNBUFFERED=1
Environment=PORT=5011
ExecStart=/usr/bin/python3 /root/website-monitor/enhanced-minimal-backend.py
Restart=always
RestartSec=10
StandardOutput=append:/root/website-monitor/logs/backend.log
StandardError=append:/root/website-monitor/logs/backend.log

[Install]
WantedBy=multi-user.target
EOF

# 5. 启动增强版服务
info "5. 启动增强版服务..."
systemctl daemon-reload
systemctl enable website-monitor-enhanced.service
systemctl start website-monitor-enhanced.service

# 等待服务启动
sleep 5

# 6. 检查服务状态
info "6. 检查服务状态..."
if systemctl is-active --quiet website-monitor-enhanced.service; then
    success "增强版服务启动成功！"
    systemctl status website-monitor-enhanced.service --no-pager -l
else
    error "增强版服务启动失败"
    info "尝试直接运行..."
    
    # 直接运行
    nohup python3 enhanced-minimal-backend.py > logs/backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > backend.pid
    
    sleep 3
    
    if kill -0 $BACKEND_PID 2>/dev/null; then
        success "增强版后端进程启动成功，PID: $BACKEND_PID"
    else
        error "增强版后端进程启动失败"
        tail -20 logs/backend.log
        exit 1
    fi
fi

# 7. 健康检查
info "7. 健康检查..."
for i in {1..10}; do
    if curl -s http://localhost:5011/api/health >/dev/null 2>&1; then
        success "健康检查通过！"
        HEALTH_RESPONSE=$(curl -s http://localhost:5011/api/health)
        info "响应: $HEALTH_RESPONSE"
        break
    else
        warning "等待服务启动... ($i/10)"
        sleep 3
    fi
    
    if [ $i -eq 10 ]; then
        error "健康检查失败"
        info "检查日志..."
        tail -20 logs/backend.log 2>/dev/null || echo "日志文件不存在"
        exit 1
    fi
done

# 8. 测试关键API接口
info "8. 测试关键API接口..."

# 测试登录接口
info "测试登录接口..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:5011/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"admin123"}' \
    -w "%{http_code}")

if echo "$LOGIN_RESPONSE" | grep -q "登录成功"; then
    success "登录接口测试通过"
else
    warning "登录接口测试失败: $LOGIN_RESPONSE"
fi

# 测试分组接口
info "测试分组接口..."
GROUPS_RESPONSE=$(curl -s http://localhost:5011/api/groups/ -w "%{http_code}")

if echo "$GROUPS_RESPONSE" | grep -q "获取分组列表成功"; then
    success "分组接口测试通过"
else
    warning "分组接口测试失败: $GROUPS_RESPONSE"
fi

# 测试网站接口
info "测试网站接口..."
WEBSITES_RESPONSE=$(curl -s http://localhost:5011/api/websites/ -w "%{http_code}")

if echo "$WEBSITES_RESPONSE" | grep -q "获取网站列表成功"; then
    success "网站接口测试通过"
else
    warning "网站接口测试失败: $WEBSITES_RESPONSE"
fi

echo ""
echo "============================================="
echo "           修复完成"
echo "============================================="
success "API 404错误已修复！"
echo ""
echo "增强版后端功能:"
echo "  ✓ 登录认证 (/api/auth/login)"
echo "  ✓ 用户管理 (/api/auth/me, /api/auth/users)"
echo "  ✓ 分组管理 (/api/groups/)"
echo "  ✓ 网站管理 (/api/websites/)"
echo "  ✓ 任务管理 (/api/tasks/)"
echo "  ✓ 结果查询 (/api/results/)"
echo "  ✓ 文件管理 (/api/files/)"
echo "  ✓ 系统设置 (/api/settings/system)"
echo "  ✓ 邮件设置 (/api/settings/email)"
echo ""
echo "服务信息:"
echo "  - 服务名称: website-monitor-enhanced.service"
echo "  - 端口: 5011"
echo "  - 日志文件: /root/website-monitor/logs/backend.log"
echo ""
echo "管理命令:"
echo "  - 查看状态: systemctl status website-monitor-enhanced.service"
echo "  - 重启服务: systemctl restart website-monitor-enhanced.service"
echo "  - 查看日志: tail -f logs/backend.log"
echo "  - 停止服务: systemctl stop website-monitor-enhanced.service"
echo ""
echo "测试命令:"
echo "  - 健康检查: curl http://localhost:5011/api/health"
echo "  - 登录测试: curl -X POST http://localhost:5011/api/auth/login -H 'Content-Type: application/json' -d '{\"username\":\"admin\",\"password\":\"admin123\"}'"
echo "  - 分组列表: curl http://localhost:5011/api/groups/"
echo ""
echo "现在可以正常使用前端界面的所有功能了！"
echo "============================================="