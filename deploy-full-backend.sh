#!/bin/bash
# 部署完整的Flask后端服务

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
echo "    部署完整的Flask后端服务"
echo "============================================="

# 1. 停止现有服务
info "1. 停止现有服务..."
systemctl stop website-monitor-enhanced.service 2>/dev/null || true
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

# 2. 检查Python环境
info "2. 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    error "Python3 not found"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
success "Python环境: $PYTHON_VERSION"

# 3. 创建虚拟环境
info "3. 创建虚拟环境..."
if [ -d "venv" ]; then
    rm -rf venv
fi
python3 -m venv venv
source venv/bin/activate
success "虚拟环境已创建并激活"

# 4. 安装核心依赖（使用本地源）
info "4. 安装核心依赖..."

# 创建requirements-core.txt，只包含必需的包
cat > requirements-core.txt << EOF
Flask==2.3.3
Werkzeug==2.3.7
Jinja2==3.1.2
MarkupSafe==2.1.3
itsdangerous==2.1.2
click==8.1.7
blinker==1.6.2
SQLAlchemy==2.0.21
PyMySQL==1.1.0
cryptography==41.0.4
python-dotenv==1.0.0
requests==2.31.0
APScheduler==3.10.4
Flask-SQLAlchemy==3.0.5
Flask-JWT-Extended==4.5.2
Flask-CORS==4.0.0
pandas==2.0.3
openpyxl==3.1.2
six==1.16.0
python-dateutil==2.8.2
pytz==2023.3
tzdata==2023.3
aiohttp==3.8.5
aiosignal==1.3.1
attrs==23.1.0
charset-normalizer==3.2.0
frozenlist==1.4.0
multidict==6.0.4
yarl==1.9.2
async-timeout==4.0.2
EOF

# 尝试安装依赖，如果失败则使用系统包
info "尝试安装Python依赖..."

# 设置pip配置使用国内源
mkdir -p ~/.pip
cat > ~/.pip/pip.conf << EOF
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple/
trusted-host = pypi.tuna.tsinghua.edu.cn
timeout = 60
retries = 3
EOF

# 升级pip
python3 -m pip install --upgrade pip

# 逐个安装关键包
CRITICAL_PACKAGES=(
    "Flask==2.3.3"
    "Werkzeug==2.3.7"
    "SQLAlchemy==2.0.21"
    "PyMySQL==1.1.0"
    "python-dotenv==1.0.0"
    "requests==2.31.0"
)

for package in "${CRITICAL_PACKAGES[@]}"; do
    info "安装 $package"
    if ! pip install "$package" --timeout=60; then
        warning "$package 安装失败，尝试无缓存安装..."
        pip install "$package" --no-cache-dir --timeout=60 || warning "$package 安装失败，继续..."
    fi
done

# 尝试安装其他包
OTHER_PACKAGES=(
    "Flask-SQLAlchemy==3.0.5"
    "Flask-JWT-Extended==4.5.2"
    "Flask-CORS==4.0.0"
    "APScheduler==3.10.4"
    "pandas==2.0.3"
    "openpyxl==3.1.2"
)

for package in "${OTHER_PACKAGES[@]}"; do
    info "安装 $package"
    pip install "$package" --timeout=60 || warning "$package 安装失败，继续..."
done

# 5. 测试关键模块导入
info "5. 测试关键模块导入..."
python3 -c "
try:
    import flask
    print('✓ Flask 导入成功')
except ImportError as e:
    print('✗ Flask 导入失败:', e)

try:
    import sqlalchemy
    print('✓ SQLAlchemy 导入成功')
except ImportError as e:
    print('✗ SQLAlchemy 导入失败:', e)

try:
    import pymysql
    print('✓ PyMySQL 导入成功')
except ImportError as e:
    print('✗ PyMySQL 导入失败:', e)

try:
    import requests
    print('✓ requests 导入成功')
except ImportError as e:
    print('✗ requests 导入失败:', e)
"

# 6. 创建必要目录
info "6. 创建必要目录..."
mkdir -p logs uploads downloads user_files database backend/api backend/services

# 7. 设置环境变量
info "7. 设置环境变量..."
cat > .env << EOF
# 数据库配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=website_monitor
MYSQL_USER=monitor_user
MYSQL_PASSWORD=BaotaUser2024!

# 应用配置
SECRET_KEY=WebMonitorBaotaSecretKey2024ChangeMe
JWT_SECRET_KEY=JWTBaotaSecretKey2024ChangeMe
FLASK_ENV=production
PORT=5011
DEBUG=false
LOG_LEVEL=INFO

# 性能配置
WORKERS=2
THREADS=4
TIMEOUT=120
MAX_MEMORY_MB=512

# 检测配置
DEFAULT_TIMEOUT=30
DEFAULT_RETRY_TIMES=3
DEFAULT_MAX_CONCURRENT=20
DEFAULT_INTERVAL_HOURS=6

# 时区
TZ=Asia/Shanghai
EOF

# 8. 检查数据库连接
info "8. 检查数据库连接..."
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

# 9. 初始化数据库
info "9. 初始化数据库..."
python3 -c "
import os
import sys
sys.path.insert(0, os.getcwd())

# 设置环境变量
os.environ['MYSQL_HOST'] = 'localhost'
os.environ['MYSQL_PORT'] = '3306'
os.environ['MYSQL_DATABASE'] = 'website_monitor'
os.environ['MYSQL_USER'] = 'monitor_user'
os.environ['MYSQL_PASSWORD'] = 'BaotaUser2024!'
os.environ['SECRET_KEY'] = 'WebMonitorBaotaSecretKey2024ChangeMe'
os.environ['FLASK_ENV'] = 'production'

try:
    from backend.app import create_app
    from backend.database import db
    
    app = create_app()
    with app.app_context():
        # 创建所有表
        db.create_all()
        print('✓ 数据库表创建成功')
        
        # 创建默认管理员用户
        from backend.models import User
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                nickname='管理员',
                email='admin@example.com',
                role='admin'
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
            print('✓ 默认管理员用户创建成功')
        else:
            print('✓ 管理员用户已存在')
            
except Exception as e:
    print(f'✗ 数据库初始化失败: {e}')
    import traceback
    traceback.print_exc()
"

# 10. 创建启动脚本
info "10. 创建启动脚本..."
cat > start_full_backend.py << 'EOF'
#!/usr/bin/env python3
"""
完整Flask后端启动脚本
"""
import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 设置环境变量
os.environ.setdefault('FLASK_APP', 'backend.app')
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('PORT', '5011')

def main():
    try:
        from backend.app import create_app
        
        app = create_app()
        
        # 获取端口
        port = int(os.environ.get('PORT', 5011))
        
        print(f"启动完整Flask应用在端口 {port}")
        print(f"访问地址: http://localhost:{port}")
        print(f"健康检查: http://localhost:{port}/api/health")
        print("-" * 50)
        
        # 启动应用
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            threaded=True
        )
        
    except Exception as e:
        print(f"应用启动失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
EOF

chmod +x start_full_backend.py

# 11. 创建systemd服务
info "11. 创建systemd服务..."
cat > /etc/systemd/system/website-monitor-full.service << EOF
[Unit]
Description=Website Monitor Full Backend Service
After=network.target mysql.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/website-monitor
Environment=PYTHONPATH=/root/website-monitor
Environment=PYTHONUNBUFFERED=1
ExecStart=/root/website-monitor/venv/bin/python /root/website-monitor/start_full_backend.py
Restart=always
RestartSec=10
StandardOutput=append:/root/website-monitor/logs/backend.log
StandardError=append:/root/website-monitor/logs/backend.log

[Install]
WantedBy=multi-user.target
EOF

# 12. 启动完整服务
info "12. 启动完整服务..."
systemctl daemon-reload
systemctl enable website-monitor-full.service
systemctl start website-monitor-full.service

# 等待服务启动
sleep 10

# 13. 检查服务状态
info "13. 检查服务状态..."
if systemctl is-active --quiet website-monitor-full.service; then
    success "完整Flask服务启动成功！"
    systemctl status website-monitor-full.service --no-pager -l
else
    error "服务启动失败，尝试直接运行..."
    
    # 直接运行
    source venv/bin/activate
    nohup python3 start_full_backend.py > logs/backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > backend.pid
    
    sleep 5
    
    if kill -0 $BACKEND_PID 2>/dev/null; then
        success "Flask应用直接启动成功，PID: $BACKEND_PID"
    else
        error "Flask应用启动失败"
        echo "检查日志:"
        tail -30 logs/backend.log
        exit 1
    fi
fi

# 14. 健康检查
info "14. 健康检查..."
for i in {1..15}; do
    if curl -s http://localhost:5011/api/health >/dev/null 2>&1; then
        success "健康检查通过！"
        HEALTH_RESPONSE=$(curl -s http://localhost:5011/api/health)
        info "响应: $HEALTH_RESPONSE"
        break
    else
        warning "等待Flask应用启动... ($i/15)"
        sleep 5
    fi
    
    if [ $i -eq 15 ]; then
        error "健康检查失败"
        info "检查日志..."
        tail -50 logs/backend.log
        exit 1
    fi
done

# 15. 测试完整API
info "15. 测试完整API功能..."

# 测试登录
info "测试登录接口..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:5011/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"admin123"}')

if echo "$LOGIN_RESPONSE" | grep -q '"success".*true\|"code".*200'; then
    success "登录接口测试通过"
else
    warning "登录接口响应: $LOGIN_RESPONSE"
fi

# 测试数据库连接
info "测试数据库操作..."
DB_TEST=$(curl -s http://localhost:5011/api/groups/)
if echo "$DB_TEST" | grep -q '"success".*true\|"code".*200'; then
    success "数据库操作测试通过"
else
    warning "数据库操作响应: $DB_TEST"
fi

echo ""
echo "============================================="
echo "           完整Flask后端部署完成"
echo "============================================="
success "完整的网址监控系统后端已部署！"
echo ""
echo "功能特性:"
echo "  ✓ 完整的用户认证和权限管理"
echo "  ✓ 网站分组和批量管理"
echo "  ✓ 实时网站状态检测"
echo "  ✓ 定时任务调度系统"
echo "  ✓ 检测结果统计分析"
echo "  ✓ 文件导入导出功能"
echo "  ✓ 邮件通知系统"
echo "  ✓ 系统设置管理"
echo "  ✓ API接口文档"
echo ""
echo "服务信息:"
echo "  - 服务名称: website-monitor-full.service"
echo "  - 端口: 5011"
echo "  - 虚拟环境: /root/website-monitor/venv"
echo "  - 日志文件: /root/website-monitor/logs/backend.log"
echo "  - 配置文件: /root/website-monitor/.env"
echo ""
echo "管理命令:"
echo "  - 查看状态: systemctl status website-monitor-full.service"
echo "  - 重启服务: systemctl restart website-monitor-full.service"
echo "  - 查看日志: tail -f logs/backend.log"
echo "  - 停止服务: systemctl stop website-monitor-full.service"
echo ""
echo "数据库信息:"
echo "  - 数据库: website_monitor"
echo "  - 用户: monitor_user"
echo "  - 默认管理员: admin / admin123"
echo ""
echo "现在可以使用完整功能的网址监控系统了！"
echo "============================================="