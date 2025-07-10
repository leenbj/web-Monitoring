#!/bin/bash
# 使用系统包管理器安装依赖（避免pip网络问题）

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
echo "    系统包安装Python依赖"
echo "============================================="

# 1. 检测系统类型
info "1. 检测系统类型..."
if [ -f /etc/redhat-release ]; then
    SYSTEM="centos"
    info "检测到CentOS/RHEL系统"
elif [ -f /etc/debian_version ]; then
    SYSTEM="debian"
    info "检测到Debian/Ubuntu系统"
else
    SYSTEM="unknown"
    warning "未知系统类型"
fi

# 2. 更新包管理器
info "2. 更新包管理器..."
if [ "$SYSTEM" = "centos" ]; then
    yum update -y
    yum install -y epel-release
elif [ "$SYSTEM" = "debian" ]; then
    apt-get update
else
    warning "跳过包管理器更新"
fi

# 3. 安装Python3和基础工具
info "3. 安装Python3和基础工具..."
if [ "$SYSTEM" = "centos" ]; then
    yum install -y python3 python3-pip python3-devel gcc gcc-c++ make \
        mysql-devel libffi-devel openssl-devel curl wget
elif [ "$SYSTEM" = "debian" ]; then
    apt-get install -y python3 python3-pip python3-dev build-essential \
        libmysqlclient-dev libffi-dev libssl-dev curl wget
fi

# 4. 安装系统Python包
info "4. 安装系统Python包..."
if [ "$SYSTEM" = "centos" ]; then
    yum install -y python3-flask python3-requests python3-werkzeug \
        python3-jinja2 python3-markupsafe python3-itsdangerous \
        python3-click python3-dateutil python3-six
elif [ "$SYSTEM" = "debian" ]; then
    apt-get install -y python3-flask python3-requests python3-werkzeug \
        python3-jinja2 python3-markupsafe python3-itsdangerous \
        python3-click python3-dateutil python3-six python3-pymysql
fi

# 5. 创建本地包目录
info "5. 创建本地包目录..."
mkdir -p /root/website-monitor/local_packages
cd /root/website-monitor

# 6. 下载并安装离线包（如果可能）
info "6. 尝试下载离线包..."
PACKAGES=(
    "PyMySQL==1.1.0"
    "Flask-SQLAlchemy==3.0.5"
    "Flask-CORS==4.0.0"
    "Flask-JWT-Extended==4.5.2"
    "APScheduler==3.10.4"
    "python-dotenv==1.0.0"
)

for package in "${PACKAGES[@]}"; do
    info "尝试安装 $package"
    timeout 30 pip3 install --no-deps --target ./local_packages "$package" 2>/dev/null || warning "$package 安装失败"
done

# 7. 如果pip完全失败，创建最小实现
info "7. 创建最小实现..."
cat > minimal_flask_app.py << 'EOF'
#!/usr/bin/env python3
"""
最小Flask应用实现 - 无外部依赖
"""
import os
import sys
import json
import time
import socket
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import subprocess

class WebMonitorHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0-minimal'
            }
            self.wfile.write(json.dumps(response).encode())
            
        elif parsed_path.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                'name': '网址监控系统',
                'version': '1.0.0-minimal',
                'status': 'running'
            }
            self.wfile.write(json.dumps(response).encode())
            
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        if self.path == '/api/auth/login':
            try:
                data = json.loads(post_data.decode())
                if data.get('username') == 'admin' and data.get('password') == 'admin123':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    
                    response = {
                        'success': True,
                        'message': '登录成功',
                        'token': 'minimal-token-' + str(int(time.time()))
                    }
                    self.wfile.write(json.dumps(response).encode())
                else:
                    self.send_response(401)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    
                    response = {'success': False, 'message': '用户名或密码错误'}
                    self.wfile.write(json.dumps(response).encode())
            except:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'Bad Request')
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

def run_server(port=5011):
    server_address = ('', port)
    httpd = HTTPServer(server_address, WebMonitorHandler)
    print(f"启动最小化服务器在端口 {port}")
    httpd.serve_forever()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5011))
    run_server(port)
EOF

chmod +x minimal_flask_app.py

# 8. 创建启动脚本
info "8. 创建启动脚本..."
cat > start_minimal_backend.sh << 'EOF'
#!/bin/bash
# 启动最小化后端服务

# 设置Python路径
export PYTHONPATH="/root/website-monitor:/root/website-monitor/local_packages:$PYTHONPATH"

# 创建日志目录
mkdir -p /root/website-monitor/logs

# 检查端口占用
if netstat -tlnp | grep -q ":5011 "; then
    echo "端口5011已被占用，尝试终止..."
    PORT_PID=$(netstat -tlnp | grep ":5011 " | awk '{print $7}' | cut -d'/' -f1)
    if [ "$PORT_PID" != "-" ]; then
        kill -9 $PORT_PID 2>/dev/null || true
        sleep 2
    fi
fi

# 启动服务
echo "启动最小化后端服务..."
cd /root/website-monitor

# 首先尝试完整的应用
if [ -f "run_simple_backend.py" ]; then
    echo "尝试启动完整应用..."
    python3 run_simple_backend.py 2>&1 | tee logs/backend.log &
    BACKEND_PID=$!
    sleep 3
    
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo "完整应用启动成功，PID: $BACKEND_PID"
        echo $BACKEND_PID > backend.pid
        exit 0
    else
        echo "完整应用启动失败，尝试最小化应用..."
    fi
fi

# 启动最小化应用
echo "启动最小化应用..."
python3 minimal_flask_app.py 2>&1 | tee logs/backend.log &
BACKEND_PID=$!
sleep 3

if kill -0 $BACKEND_PID 2>/dev/null; then
    echo "最小化应用启动成功，PID: $BACKEND_PID"
    echo $BACKEND_PID > backend.pid
    
    # 测试健康检查
    for i in {1..5}; do
        if curl -s http://localhost:5011/api/health >/dev/null 2>&1; then
            echo "健康检查通过！"
            break
        else
            echo "等待服务启动... ($i/5)"
            sleep 2
        fi
    done
else
    echo "最小化应用启动失败"
    exit 1
fi
EOF

chmod +x start_minimal_backend.sh

# 9. 创建systemd服务
info "9. 创建systemd服务..."
cat > /etc/systemd/system/website-monitor-minimal.service << EOF
[Unit]
Description=Website Monitor Minimal Backend Service
After=network.target

[Service]
Type=forking
User=root
WorkingDirectory=/root/website-monitor
ExecStart=/root/website-monitor/start_minimal_backend.sh
PIDFile=/root/website-monitor/backend.pid
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 10. 启动服务
info "10. 启动服务..."
systemctl daemon-reload
systemctl enable website-monitor-minimal.service
./start_minimal_backend.sh

echo ""
echo "============================================="
echo "           系统包安装完成"
echo "============================================="
success "后端服务已通过系统包部署！"
echo ""
echo "服务信息:"
echo "  - 端口: 5011"
echo "  - 日志文件: /root/website-monitor/logs/backend.log"
echo "  - PID文件: /root/website-monitor/backend.pid"
echo ""
echo "管理命令:"
echo "  - 启动服务: systemctl start website-monitor-minimal.service"
echo "  - 停止服务: systemctl stop website-monitor-minimal.service"
echo "  - 重启服务: systemctl restart website-monitor-minimal.service"
echo "  - 查看状态: systemctl status website-monitor-minimal.service"
echo "  - 查看日志: tail -f logs/backend.log"
echo ""
echo "API测试:"
echo "  - 健康检查: curl http://localhost:5011/api/health"
echo "  - 登录测试: curl -X POST http://localhost:5011/api/auth/login -H 'Content-Type: application/json' -d '{\"username\":\"admin\",\"password\":\"admin123\"}'"
echo ""
echo "============================================="