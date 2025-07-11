# 网址监控系统 - Docker Hub 自动构建版本
# 支持多架构构建 (linux/amd64, linux/arm64)

FROM python:3.11-slim-bullseye

# 设置构建参数
ARG BUILDPLATFORM
ARG TARGETPLATFORM
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

# 设置标签
LABEL maintainer="网址监控系统 <support@example.com>" \
      org.opencontainers.image.title="网址监控系统后端" \
      org.opencontainers.image.description="一个功能完整的网址监控系统后端服务" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.source="https://github.com/yourusername/web-monitor" \
      org.opencontainers.image.url="https://github.com/yourusername/web-monitor" \
      org.opencontainers.image.documentation="https://github.com/yourusername/web-monitor/blob/main/README.md" \
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

# 更新系统并安装必要的系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    # 编译工具
    gcc \
    g++ \
    make \
    pkg-config \
    # 网络工具
    curl \
    wget \
    netcat \
    # MySQL客户端和开发库
    default-mysql-client \
    default-libmysqlclient-dev \
    # 其他必要库
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev \
    # 系统工具
    tzdata \
    ca-certificates \
    procps \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# 升级pip和安装基础Python包
RUN pip install --upgrade pip setuptools wheel

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖 - 优化的分步安装
RUN pip install --no-cache-dir --timeout=300 \
    # 先安装基础依赖
    wheel setuptools \
    # 数据库相关
    && pip install --no-cache-dir --timeout=300 \
    PyMySQL==1.1.0 \
    SQLAlchemy>=2.0.30 \
    # Flask相关
    && pip install --no-cache-dir --timeout=300 \
    Flask==2.3.3 \
    Flask-SQLAlchemy==3.0.5 \
    Flask-CORS==4.0.0 \
    Flask-Mail==0.9.1 \
    flask-jwt-extended==4.5.3 \
    flask-limiter==3.5.0 \
    # 其他核心依赖
    && pip install --no-cache-dir --timeout=300 \
    requests==2.31.0 \
    redis==5.0.1 \
    APScheduler==3.10.4 \
    python-dotenv==1.0.0 \
    # 剩余依赖
    && pip install --no-cache-dir --timeout=300 -r requirements.txt \
    && pip cache purge

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
COPY database/ ./database/
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