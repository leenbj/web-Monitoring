#!/bin/bash

# 构建前后端镜像的简化脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}🔨 开始构建前后端镜像...${NC}"

# 检查 Docker 是否可用
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker 未安装或未在PATH中${NC}"
    exit 1
fi

# 构建后端镜像
echo -e "${YELLOW}📦 构建后端镜像...${NC}"
docker build -t web-monitoring-backend:latest -f Dockerfile .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 后端镜像构建成功${NC}"
else
    echo -e "${RED}❌ 后端镜像构建失败${NC}"
    exit 1
fi

# 构建前端镜像
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

# 显示构建的镜像
echo -e "${YELLOW}📋 构建的镜像列表:${NC}"
docker images | grep "web-monitoring"

echo -e "${GREEN}🎉 所有镜像构建完成！${NC}"
echo ""
echo "下一步:"
echo "1. 使用 docker-compose up -d 启动服务"
echo "2. 或者运行 ./build_and_deploy.sh 进行完整部署"