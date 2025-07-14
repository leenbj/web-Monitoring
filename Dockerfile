# 网址监控系统 - 后端服务
# 多阶段构建，优化镜像大小

FROM python:3.11-slim AS builder

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    pkg-config \
    default-libmysqlclient-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制并安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# 生产镜像
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
    FLASK_APP=run_backend.py

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    default-mysql-client \
    tzdata \
    ca-certificates \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 复制Python依赖
COPY --from=builder /root/.local /root/.local

# 确保python包在PATH中
ENV PATH=/root/.local/bin:$PATH

# 创建应用用户（安全最佳实践）
RUN groupadd -r appuser && useradd -r -g appuser appuser

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
COPY run_backend.py .

# 复制启动脚本
COPY start.sh /app/start.sh

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