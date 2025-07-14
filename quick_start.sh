#!/bin/bash

# 快速启动脚本 - 自动构建镜像并启动服务

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 网址监控系统 - 快速启动${NC}"
echo "======================================"

# 检查 Docker 是否可用
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker 未安装或未在PATH中${NC}"
    exit 1
fi

# 停止现有服务
echo -e "${YELLOW}🛑 停止现有服务...${NC}"
docker-compose down 2>/dev/null || true

# 检查是否存在本地镜像
backend_image_exists=$(docker images -q web-monitoring-backend:latest)
frontend_image_exists=$(docker images -q web-monitoring-frontend:latest)

if [ -z "$backend_image_exists" ] || [ -z "$frontend_image_exists" ]; then
    echo -e "${YELLOW}📦 检测到缺少镜像，开始构建...${NC}"
    
    # 构建后端镜像
    if [ -z "$backend_image_exists" ]; then
        echo -e "${YELLOW}🔨 构建后端镜像...${NC}"
        docker build -t web-monitoring-backend:latest -f Dockerfile .
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ 后端镜像构建成功${NC}"
        else
            echo -e "${RED}❌ 后端镜像构建失败${NC}"
            exit 1
        fi
    fi
    
    # 构建前端镜像
    if [ -z "$frontend_image_exists" ]; then
        echo -e "${YELLOW}🎨 构建前端镜像...${NC}"
        cd frontend
        docker build -t web-monitoring-frontend:latest -f Dockerfile .
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ 前端镜像构建成功${NC}"
        else
            echo -e "${RED}❌ 前端镜像构建失败${NC}"
            exit 1
        fi
        cd ..
    fi
else
    echo -e "${GREEN}✅ 发现本地镜像，跳过构建${NC}"
fi

# 启动服务
echo -e "${YELLOW}🚀 启动服务...${NC}"
docker-compose up -d

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 服务启动成功${NC}"
else
    echo -e "${RED}❌ 服务启动失败${NC}"
    exit 1
fi

# 等待服务启动
echo -e "${YELLOW}⏳ 等待服务启动...${NC}"
sleep 20

# 检查服务状态
echo -e "${YELLOW}🔍 检查服务状态...${NC}"
docker-compose ps

# 修复管理员用户
echo -e "${YELLOW}🔧 修复管理员用户...${NC}"
docker-compose exec -T backend python3 -c "
import sys
import os
sys.path.insert(0, '/app')
os.environ['DATABASE_URL'] = 'mysql://webmonitor:webmonitor123@mysql:3306/website_monitor'

from backend.app import create_app
from backend.models import User
from backend.database import get_db

app = create_app()
with app.app_context():
    with get_db() as db:
        # 删除现有admin用户
        existing = db.query(User).filter(User.username == 'admin').first()
        if existing:
            db.delete(existing)
            db.commit()
        
        # 创建新的管理员用户
        admin = User(username='admin', email='admin@example.com', role='admin', status='active')
        admin.set_password('admin123')
        db.add(admin)
        db.commit()
        print('✅ 管理员用户创建成功!')
" 2>/dev/null || echo -e "${YELLOW}⚠️ 管理员用户修复可能需要等待数据库完全启动${NC}"

# 显示部署信息
echo ""
echo -e "${GREEN}🎉 部署完成！${NC}"
echo "======================================"
echo "📋 服务信息:"
echo "  - 前端地址: http://localhost:8080"
echo "  - 后端地址: http://localhost:5012"
echo "  - MySQL端口: 33061"
echo "  - Redis端口: 63791"
echo ""
echo "🔑 登录信息:"
echo "  - 用户名: admin"
echo "  - 密码: admin123"
echo ""
echo "🔧 管理命令:"
echo "  - 查看日志: docker-compose logs -f"
echo "  - 重启服务: docker-compose restart"
echo "  - 停止服务: docker-compose down"
echo "  - 查看状态: docker-compose ps"
echo ""
echo "如果无法登录，请运行: bash quick_fix_admin.sh"