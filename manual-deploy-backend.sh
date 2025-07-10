#!/bin/bash
# 手动部署后端服务（绕过Docker构建问题）

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
echo "    手动部署后端服务"
echo "============================================="

# 1. 停止Docker服务
info "1. 停止Docker服务..."
docker-compose -f docker-compose.baota.yml down 2>/dev/null || true
docker stop website-monitor-backend 2>/dev/null || true
docker rm website-monitor-backend 2>/dev/null || true

# 2. 检查Python环境
info "2. 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    error "Python3 not found"
    info "安装Python3..."
    # CentOS/RHEL
    if command -v yum &> /dev/null; then
        yum install -y python3 python3-pip
    # Ubuntu/Debian
    elif command -v apt-get &> /dev/null; then
        apt-get update && apt-get install -y python3 python3-pip
    else
        error "无法识别的系统，请手动安装Python3"
        exit 1
    fi
fi

PYTHON_VERSION=$(python3 --version)
success "Python环境: $PYTHON_VERSION"

# 3. 创建虚拟环境
info "3. 创建虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
success "虚拟环境已激活"

# 4. 安装依赖
info "4. 安装Python依赖..."
pip3 install --upgrade pip
pip3 install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

# 5. 创建必要目录
info "5. 创建必要目录..."
mkdir -p logs uploads downloads user_files database

# 6. 设置环境变量
info "6. 设置环境变量..."
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_DATABASE=website_monitor
export MYSQL_USER=monitor_user
export MYSQL_PASSWORD=BaotaUser2024!
export SECRET_KEY=WebMonitorBaotaSecretKey2024ChangeMe
export JWT_SECRET_KEY=JWTBaotaSecretKey2024ChangeMe
export FLASK_ENV=production
export PORT=5011
export DEBUG=false
export LOG_LEVEL=INFO
export PYTHONPATH=/root/website-monitor
export PYTHONUNBUFFERED=1

# 7. 测试数据库连接
info "7. 测试数据库连接..."
if command -v mysql &> /dev/null; then
    if mysql -hlocalhost -umonitor_user -pBaotaUser2024! -e "USE website_monitor;" 2>/dev/null; then
        success "数据库连接成功"
    else
        error "数据库连接失败"
        warning "请确保在宝塔面板中："
        echo "1. 创建数据库: website_monitor"
        echo "2. 创建用户: monitor_user"
        echo "3. 设置密码: BaotaUser2024!"
        echo "4. 授予所有权限"
        exit 1
    fi
else
    warning "mysql客户端不可用，跳过数据库连接测试"
fi

# 8. 检查端口占用
info "8. 检查端口占用..."
if netstat -tlnp | grep -q ":5011 "; then
    warning "端口5011已被占用"
    PORT_PID=$(netstat -tlnp | grep ":5011 " | awk '{print $7}' | cut -d'/' -f1)
    if [ "$PORT_PID" != "-" ]; then
        info "终止占用进程 $PORT_PID"
        kill -9 $PORT_PID 2>/dev/null || true
        sleep 2
    fi
fi

# 9. 创建systemd服务文件
info "9. 创建systemd服务..."
cat > /etc/systemd/system/website-monitor.service << EOF
[Unit]
Description=Website Monitor Backend Service
After=network.target mysql.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/website-monitor
Environment=MYSQL_HOST=localhost
Environment=MYSQL_PORT=3306
Environment=MYSQL_DATABASE=website_monitor
Environment=MYSQL_USER=monitor_user
Environment=MYSQL_PASSWORD=BaotaUser2024!
Environment=SECRET_KEY=WebMonitorBaotaSecretKey2024ChangeMe
Environment=JWT_SECRET_KEY=JWTBaotaSecretKey2024ChangeMe
Environment=FLASK_ENV=production
Environment=PORT=5011
Environment=DEBUG=false
Environment=LOG_LEVEL=INFO
Environment=PYTHONPATH=/root/website-monitor
Environment=PYTHONUNBUFFERED=1
ExecStart=/root/website-monitor/venv/bin/python /root/website-monitor/run_backend.py
Restart=always
RestartSec=10
StandardOutput=append:/root/website-monitor/logs/backend.log
StandardError=append:/root/website-monitor/logs/backend.log

[Install]
WantedBy=multi-user.target
EOF

# 10. 启动服务
info "10. 启动服务..."
systemctl daemon-reload
systemctl enable website-monitor.service
systemctl start website-monitor.service

# 等待服务启动
sleep 5

# 11. 检查服务状态
info "11. 检查服务状态..."
if systemctl is-active --quiet website-monitor.service; then
    success "服务启动成功！"
    systemctl status website-monitor.service --no-pager
else
    error "服务启动失败"
    info "检查日志..."
    journalctl -u website-monitor.service --no-pager -l
    exit 1
fi

# 12. 健康检查
info "12. 健康检查..."
for i in {1..12}; do
    if curl -s http://localhost:5011/api/health >/dev/null 2>&1; then
        success "健康检查通过！"
        HEALTH_RESPONSE=$(curl -s http://localhost:5011/api/health)
        info "响应: $HEALTH_RESPONSE"
        break
    else
        warning "等待服务启动... ($i/12)"
        sleep 5
    fi
    
    if [ $i -eq 12 ]; then
        error "健康检查失败"
        info "检查服务日志..."
        tail -20 logs/backend.log
        exit 1
    fi
done

echo ""
echo "============================================="
echo "           手动部署完成"
echo "============================================="
success "后端服务已成功部署并运行！"
echo ""
echo "服务信息:"
echo "  - 服务状态: $(systemctl is-active website-monitor.service)"
echo "  - 端口: 5011"
echo "  - 日志文件: /root/website-monitor/logs/backend.log"
echo ""
echo "管理命令:"
echo "  - 启动服务: systemctl start website-monitor.service"
echo "  - 停止服务: systemctl stop website-monitor.service"
echo "  - 重启服务: systemctl restart website-monitor.service"
echo "  - 查看状态: systemctl status website-monitor.service"
echo "  - 查看日志: journalctl -u website-monitor.service -f"
echo ""
echo "API测试:"
curl -s http://localhost:5011/api/health || echo "API暂时不可用"
echo ""
echo "============================================="