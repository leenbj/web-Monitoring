# Docker镜像依赖缺失修复方案

## 🚨 问题确认

诊断结果显示Docker镜像缺少关键Python依赖：
- ❌ `ModuleNotFoundError: No module named 'flask'`
- ❌ `No module named 'pymysql'`
- ❌ `No module named 'redis'`

## 🛠️ 解决方案

### 方案1: 修复容器内依赖 (临时解决)

```bash
# 进入容器安装依赖
docker exec -it website-monitor-backend bash

# 在容器内执行
cd /app
python -m pip install --upgrade pip
pip install flask pymysql redis flask-sqlalchemy flask-jwt-extended flask-cors APScheduler requests beautifulsoup4 python-dotenv

# 手动启动测试
python run_backend.py

# 如果成功，退出容器重启
exit
docker restart website-monitor-backend
```

### 方案2: 重新构建镜像 (推荐)

#### 2.1 检查requirements.txt文件
```bash
# 查看项目根目录的requirements.txt
cat requirements.txt

# 如果不存在，创建requirements.txt
cat > requirements.txt << 'EOF'
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-JWT-Extended==4.5.3
Flask-CORS==4.0.0
PyMySQL==1.1.0
redis==4.6.0
APScheduler==3.10.4
requests==2.31.0
beautifulsoup4==4.12.2
python-dotenv==1.0.0
gunicorn==21.2.0
cryptography==41.0.7
Werkzeug==2.3.7
EOF
```

#### 2.2 检查Dockerfile
```bash
# 查看Dockerfile内容
cat Dockerfile

# 确保包含依赖安装步骤
```

#### 2.3 本地重新构建
```bash
# 停止现有容器
docker-compose -f docker-compose.backend-only.yml down

# 重新构建镜像
docker build -t leenbj68719929/website-monitor-backend:latest .

# 启动服务
docker-compose -f docker-compose.backend-only.yml up -d
```

### 方案3: 使用GitHub Actions重新构建镜像

#### 3.1 触发新的构建
```bash
# 如果requirements.txt有更新，推送到GitHub
git add requirements.txt
git commit -m "fix: 添加缺失的Python依赖库"
git push origin main

# GitHub Actions会自动构建新镜像
```

#### 3.2 等待构建完成后拉取新镜像
```bash
# 拉取最新镜像
docker pull leenbj68719929/website-monitor-backend:latest

# 重启服务
docker-compose -f docker-compose.backend-only.yml down
docker-compose -f docker-compose.backend-only.yml up -d
```

## ⚡ 立即执行的快速修复

### 步骤1: 临时修复容器
```bash
# 进入容器
docker exec -it website-monitor-backend bash

# 安装依赖
pip install flask pymysql redis flask-sqlalchemy flask-jwt-extended flask-cors APScheduler requests beautifulsoup4 python-dotenv gunicorn

# 测试启动
cd /app
python run_backend.py
```

### 步骤2: 验证修复
```bash
# 在另一个终端测试API
curl http://localhost:5013/api/health

# 如果成功，按Ctrl+C停止手动启动，然后重启容器
docker restart website-monitor-backend

# 再次测试
curl http://localhost:5013/api/health
```

### 步骤3: 验证完整服务
```bash
# 运行完整测试
./backend-service-test.sh
```

## 🔍 验证Dockerfile配置

检查项目中的Dockerfile是否正确：

```dockerfile
# Dockerfile应该包含以下内容
FROM python:3.9-slim

WORKDIR /app

# 复制requirements.txt
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["python", "run_backend.py"]
```

## 🎯 预防措施

### 1. 完善requirements.txt
确保requirements.txt包含所有必要依赖：
```txt
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-JWT-Extended==4.5.3
Flask-CORS==4.0.0
PyMySQL==1.1.0
redis==4.6.0
APScheduler==3.10.4
requests==2.31.0
beautifulsoup4==4.12.2
python-dotenv==1.0.0
gunicorn==21.2.0
cryptography==41.0.7
Werkzeug==2.3.7
```

### 2. 改进Dockerfile
```dockerfile
FROM python:3.9-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    pkg-config \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 复制并安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 设置环境变量
ENV FLASK_APP=run_backend.py
ENV FLASK_ENV=production

EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s \
  CMD curl -f http://localhost:5000/api/health || exit 1

CMD ["python", "run_backend.py"]
```

### 3. 测试镜像构建
```bash
# 本地测试构建
docker build -t test-backend .

# 测试运行
docker run --rm -p 5000:5000 test-backend

# 测试API
curl http://localhost:5000/api/health
```

## 🆘 如果问题持续

1. **检查GitHub Actions构建日志**
2. **确认requirements.txt在正确位置**
3. **验证Dockerfile语法**
4. **手动构建镜像测试**

执行临时修复后，应该能立即解决API访问问题！