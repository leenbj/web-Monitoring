#!/bin/bash
# 快速修复Docker构建问题

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
echo "    快速修复Docker构建问题"
echo "============================================="

# 1. 停止当前构建
info "1. 停止当前构建进程..."
docker-compose -f docker-compose.baota.yml down 2>/dev/null || true
docker stop website-monitor-backend 2>/dev/null || true
docker rm website-monitor-backend 2>/dev/null || true

# 2. 检查是否有预构建的镜像
info "2. 检查现有镜像..."
if docker images | grep -q "website-monitor-baota-backend"; then
    info "发现现有镜像，尝试直接使用..."
    docker-compose -f docker-compose.baota.yml up -d --no-build
    sleep 10
    
    # 检查容器状态
    if docker ps | grep -q "website-monitor-backend"; then
        success "使用现有镜像启动成功！"
        docker ps | grep website-monitor-backend
        exit 0
    else
        warning "现有镜像启动失败，需要重新构建"
    fi
fi

# 3. 创建轻量级Dockerfile
info "3. 创建轻量级Dockerfile..."
cat > Dockerfile.baota.fast << 'EOF'
# 使用阿里云镜像源加速
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 使用阿里云镜像源
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources

# 安装必要的系统依赖（最小化）
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements.txt
COPY requirements.txt .

# 使用阿里云pip源安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt \
    -i https://mirrors.aliyun.com/pypi/simple/ \
    --trusted-host mirrors.aliyun.com

# 复制应用代码
COPY backend/ ./backend/
COPY run_backend.py .
COPY start-baota.sh .

# 创建必要的目录
RUN mkdir -p /app/logs /app/uploads /app/downloads /app/user_files /app/database

# 设置权限
RUN chmod +x start-baota.sh

# 暴露端口
EXPOSE 5011

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5011/api/health || exit 1

# 启动应用
CMD ["./start-baota.sh"]
EOF

success "轻量级Dockerfile创建完成"

# 4. 修改docker-compose使用新的Dockerfile
info "4. 修改docker-compose配置..."
sed -i 's/dockerfile: Dockerfile.baota/dockerfile: Dockerfile.baota.fast/g' docker-compose.baota.yml

# 5. 构建镜像（使用缓存）
info "5. 开始构建镜像..."
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# 设置构建超时
timeout 300 docker-compose -f docker-compose.baota.yml build --build-arg BUILDKIT_INLINE_CACHE=1

if [ $? -eq 0 ]; then
    success "镜像构建成功"
else
    error "镜像构建失败"
    
    # 尝试使用预构建镜像
    info "尝试使用Python基础镜像直接运行..."
    
    # 创建临时运行脚本
    cat > run-temp-backend.sh << 'EOF'
#!/bin/bash
# 临时运行后端服务
cd /root/website-monitor

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "Python3 not found, installing..."
    yum install -y python3 python3-pip || apt-get update && apt-get install -y python3 python3-pip
fi

# 安装依赖
pip3 install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 设置环境变量
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_DATABASE=website_monitor
export MYSQL_USER=monitor_user
export MYSQL_PASSWORD=BaotaUser2024!
export SECRET_KEY=WebMonitorBaotaSecretKey2024ChangeMe
export JWT_SECRET_KEY=JWTBaotaSecretKey2024ChangeMe
export FLASK_ENV=production
export PORT=5011

# 创建目录
mkdir -p logs uploads downloads user_files database

# 启动服务
nohup python3 run_backend.py > logs/backend.log 2>&1 &
echo "后端服务已启动，PID: $!"
EOF

    chmod +x run-temp-backend.sh
    warning "Docker构建失败，可以尝试使用 ./run-temp-backend.sh 临时启动"
    exit 1
fi

# 6. 启动容器
info "6. 启动容器..."
docker-compose -f docker-compose.baota.yml up -d

# 等待启动
sleep 10

# 7. 检查状态
info "7. 检查容器状态..."
CONTAINER_STATUS=$(docker ps --format "table {{.Names}}\t{{.Status}}" | grep website-monitor-backend)
if [ -n "$CONTAINER_STATUS" ]; then
    success "容器启动成功！"
    echo "$CONTAINER_STATUS"
else
    error "容器启动失败"
    info "检查日志..."
    docker logs website-monitor-backend --tail 20
    exit 1
fi

# 8. 健康检查
info "8. 健康检查..."
for i in {1..6}; do
    if curl -s http://localhost:5011/api/health >/dev/null 2>&1; then
        success "健康检查通过！"
        break
    else
        warning "等待服务启动... ($i/6)"
        sleep 10
    fi
done

echo ""
echo "============================================="
echo "           快速修复完成"
echo "============================================="
success "后端服务已启动"
echo ""
echo "服务状态:"
docker ps | grep website-monitor-backend
echo ""
echo "端口监听:"
netstat -tlnp | grep :5011
echo ""
echo "API测试:"
curl -s http://localhost:5011/api/health || echo "API暂时不可用"
echo ""
echo "============================================="