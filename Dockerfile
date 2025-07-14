# 网址监控系统 - 修复版Dockerfile
# 解决Python依赖安装和路径问题

FROM python:3.11-slim

# 设置构建参数
ARG BUILD_DATE
ARG VCS_REF  
ARG VERSION

# 设置标签
LABEL maintainer="网址监控系统 <support@example.com>" \
      org.opencontainers.image.title="网址监控系统后端" \
      org.opencontainers.image.description="一个功能完整的网址监控系统后端服务" \
      org.opencontainers.image.version="${VERSION:-latest}" \
      org.opencontainers.image.created="${BUILD_DATE:-unknown}" \
      org.opencontainers.image.revision="${VCS_REF:-unknown}" \
      org.opencontainers.image.source="https://github.com/yourusername/web-monitor" \
      org.opencontainers.image.licenses="MIT"

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=Asia/Shanghai \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    FLASK_ENV=production \
    FLASK_APP=run_backend.py \
    PYTHONPATH=/app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    # 构建工具
    gcc \
    g++ \
    make \
    pkg-config \
    # MySQL客户端和开发库
    default-mysql-client \
    default-libmysqlclient-dev \
    # SSL和加密库
    libffi-dev \
    libssl-dev \
    # 网络工具
    curl \
    netcat-traditional \
    # 系统工具
    tzdata \
    ca-certificates \
    # 清理
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 升级pip到最新版本
RUN pip install --upgrade pip

# 复制requirements.txt
COPY requirements.txt .

# 安装Python依赖到系统路径
RUN pip install --no-cache-dir -r requirements.txt

# 安装额外的MySQL驱动（确保兼容性）
RUN pip install --no-cache-dir mysqlclient

# 创建应用用户（安全最佳实践）
RUN groupadd -r appuser && useradd -r -g appuser -d /home/appuser -m appuser

# 创建应用目录结构
RUN mkdir -p /app/backend/logs \
    /app/backend/uploads \
    /app/backend/downloads \
    /app/backend/user_files \
    /app/database \
    /app/tmp

# 复制应用代码
COPY backend/ ./backend/
COPY init_database.py .
COPY database_init.py .
COPY run_backend.py .

# 创建启动脚本（修复版）
COPY <<EOF /app/start.sh
#!/bin/bash
set -e

# 导入PyMySQL作为MySQLdb的替代
export PYTHONPATH=/app

# 输出启动信息
echo "===========================================" 
echo "🚀 网址监控系统后端服务启动中..."
echo "==========================================="
echo "Python版本: \$(python --version)"
echo "工作目录: \$(pwd)"
echo "时间: \$(date)"
echo "用户: \$(whoami)"
echo "==========================================="

# 测试Python模块导入
echo "🔍 测试关键模块导入..."
python -c "
import sys
print('Python路径:', sys.path[:3])
try:
    import flask, pymysql, redis, requests, chardet
    print('✅ 核心模块导入成功')
except ImportError as e:
    print(f'❌ 模块导入失败: {e}')
    exit(1)
"

# 等待MySQL和Redis服务
echo "⏳ 等待数据库服务..."
max_attempts=30
attempt=0

while [ \$attempt -lt \$max_attempts ]; do
    if nc -z mysql 3306 2>/dev/null; then
        echo "✅ MySQL连接成功"
        break
    fi
    attempt=\$((attempt + 1))
    echo "等待MySQL连接... (\$attempt/\$max_attempts)"
    sleep 2
done

if [ \$attempt -eq \$max_attempts ]; then
    echo "❌ MySQL连接超时，但继续启动应用"
fi

# 等待Redis
if nc -z redis 6379 2>/dev/null; then
    echo "✅ Redis连接成功"
else
    echo "⚠️ Redis连接失败，但继续启动应用"
fi

# 初始化数据库结构
echo "🔍 初始化数据库结构..."
python database_init.py || echo "⚠️ 数据库初始化失败，继续启动应用"

echo "🚀 启动Flask应用..."
exec python run_backend.py
EOF

# 设置启动脚本权限
RUN chmod +x /app/start.sh

# 设置文件权限
RUN chmod +x run_backend.py && \
    chmod -R 755 /app && \
    chmod -R 777 /app/backend/logs && \
    chmod -R 777 /app/backend/uploads && \
    chmod -R 777 /app/backend/downloads && \
    chmod -R 777 /app/backend/user_files && \
    chmod -R 777 /app/database && \
    chmod -R 777 /app/tmp && \
    chown -R appuser:appuser /app

# 切换到应用用户
USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["/app/start.sh"]