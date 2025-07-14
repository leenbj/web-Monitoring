# 网址监控系统 - Docker完整部署指南

## 🎯 部署概述

本项目现已支持前后端完整Docker化部署，包含：
- **前端**: Vue.js 3 + Element Plus + Nginx
- **后端**: Python Flask + MySQL + Redis
- **一键部署**: Docker Compose自动化部署

## 📦 Docker镜像

### 镜像列表
- **后端镜像**: `leenbj68719929/website-monitor-backend:fixed`
- **前端镜像**: `leenbj68719929/website-monitor-frontend:fullstack`
- **数据库**: `mysql:8.0`
- **缓存**: `redis:7-alpine`

### 镜像特点
- ✅ **多架构支持**: linux/amd64, linux/arm64
- ✅ **健康检查**: 所有服务包含健康检查
- ✅ **安全优化**: 非root用户运行，最小权限原则
- ✅ **性能优化**: 使用Alpine Linux，镜像体积小
- ✅ **国内优化**: 使用阿里云镜像源加速构建

## 🚀 快速部署

### 1. 一键启动
```bash
# 克隆仓库
git clone https://github.com/yourusername/website-monitor.git
cd website-monitor

# 启动所有服务
docker-compose -f docker-compose.fullstack.yml up -d
```

### 2. 验证部署
```bash
# 检查服务状态
docker-compose -f docker-compose.fullstack.yml ps

# 测试前端
curl http://localhost/health

# 测试后端API
curl http://localhost:5013/api/health

# 测试前端代理API
curl http://localhost/api/health
```

## 🔧 配置说明

### 端口映射
- **80**: 前端Web服务
- **5013**: 后端API服务
- **3306**: MySQL数据库
- **6379**: Redis缓存

### 环境变量
```yaml
# 数据库配置
DATABASE_URL: mysql://monitor_user:Monitor123%21%40%23@mysql:3306/website_monitor
REDIS_URL: redis://:Redis123%21%40%23@redis:6379/0

# 安全密钥
SECRET_KEY: website-monitor-secret-key-12345678901234567890abcdef
JWT_SECRET_KEY: website-monitor-jwt-secret-12345678901234567890abcdef

# 运行环境
FLASK_ENV: production
TZ: Asia/Shanghai
```

### 数据持久化
- **MySQL数据**: `mysql_data` 数据卷
- **Redis数据**: `redis_data` 数据卷
- **自动备份**: 支持数据库自动备份

## 🌐 网络架构

### 服务通信
```
用户 → Nginx(Frontend) → Flask(Backend) → MySQL/Redis
     ↓
     前端静态文件
```

### 网络配置
- **frontend_network**: 前端网络
- **backend_network**: 后端网络
- **跨网络通信**: 前端可访问后端API

## 📋 部署选项

### 1. 完整部署 (推荐)
```bash
docker-compose -f docker-compose.fullstack.yml up -d
```
包含前端、后端、数据库、缓存的完整服务

### 2. 后端部署
```bash
docker-compose -f docker-compose.simple.yml up -d
```
仅部署后端API服务，适合前端分离部署

### 3. 开发环境
```bash
# 后端
docker-compose -f docker-compose.simple.yml up -d

# 前端
cd frontend
npm install
npm run dev
```

## 🛠️ 高级配置

### 自定义域名
编辑 `docker-compose.fullstack.yml`:
```yaml
services:
  frontend:
    environment:
      - VIRTUAL_HOST=your-domain.com
      - LETSENCRYPT_HOST=your-domain.com
```

### 扩展服务
```yaml
services:
  # 添加监控
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
      
  # 添加日志
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.15.0
    ports:
      - "9200:9200"
```

### 负载均衡
```yaml
services:
  backend:
    deploy:
      replicas: 3
      
  nginx:
    image: nginx:alpine
    depends_on:
      - backend
```

## 🔒 安全配置

### 生产环境建议
1. **更改默认密码**
```bash
# 修改 docker-compose.fullstack.yml 中的密码
- MYSQL_PASSWORD=your-secure-password
- REDIS_PASSWORD=your-redis-password
```

2. **使用环境变量文件**
```bash
# 创建 .env 文件
cat > .env << EOF
MYSQL_PASSWORD=your-secure-password
REDIS_PASSWORD=your-redis-password
SECRET_KEY=your-secret-key
EOF
```

3. **启用SSL**
```bash
# 使用Let's Encrypt
docker run --rm -v $(pwd)/ssl:/etc/letsencrypt certbot/certbot \
  certonly --webroot -w /var/www/html -d your-domain.com
```

## 📊 监控和日志

### 查看日志
```bash
# 查看所有服务日志
docker-compose -f docker-compose.fullstack.yml logs -f

# 查看特定服务日志
docker-compose -f docker-compose.fullstack.yml logs -f backend
```

### 监控指标
```bash
# 查看资源使用
docker stats

# 查看服务状态
docker-compose -f docker-compose.fullstack.yml ps
```

### 健康检查
```bash
# 检查所有服务健康状态
docker-compose -f docker-compose.fullstack.yml exec backend curl -f http://localhost:5000/api/health
docker-compose -f docker-compose.fullstack.yml exec frontend curl -f http://localhost/health
```

## 🔄 CI/CD 集成

### GitHub Actions
项目包含三个GitHub Actions工作流：

1. **backend-docker.yml**: 后端镜像构建
2. **frontend-docker.yml**: 前端镜像构建  
3. **fullstack-docker.yml**: 完整部署工作流

### 自动部署
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production
on:
  push:
    branches: [main]
    
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - name: Deploy to server
      run: |
        ssh user@server "cd /path/to/project && docker-compose -f docker-compose.fullstack.yml pull && docker-compose -f docker-compose.fullstack.yml up -d"
```

## 🛡️ 故障排除

### 常见问题

1. **端口冲突**
```bash
# 查看端口占用
lsof -i :80
lsof -i :5013

# 修改端口映射
ports:
  - "8080:80"  # 前端改为8080
  - "5014:5000"  # 后端改为5014
```

2. **内存不足**
```bash
# 限制资源使用
deploy:
  resources:
    limits:
      memory: 512M
      cpus: '0.5'
```

3. **数据库连接失败**
```bash
# 检查MySQL状态
docker-compose -f docker-compose.fullstack.yml exec mysql mysqladmin ping -h localhost -u monitor_user -p

# 重置数据库
docker-compose -f docker-compose.fullstack.yml down -v
docker-compose -f docker-compose.fullstack.yml up -d
```

4. **前端页面空白**
```bash
# 检查Nginx配置
docker-compose -f docker-compose.fullstack.yml exec frontend nginx -t

# 重新构建前端
cd frontend
npm run build
docker build -f Dockerfile.fullstack -t leenbj68719929/website-monitor-frontend:fullstack .
```

### 调试命令
```bash
# 进入容器调试
docker-compose -f docker-compose.fullstack.yml exec backend /bin/bash
docker-compose -f docker-compose.fullstack.yml exec frontend /bin/sh

# 查看配置
docker-compose -f docker-compose.fullstack.yml config

# 验证服务
docker-compose -f docker-compose.fullstack.yml exec backend python -c "import flask; print('Flask OK')"
```

## 📚 更多资源

### 相关文档
- [项目README](README.md)
- [Docker部署指南](DOCKER.md)
- [GitHub Actions配置](deployment/DOCKER_HUB_SETUP.md)

### 技术支持
- 项目地址: https://github.com/yourusername/website-monitor
- 问题反馈: https://github.com/yourusername/website-monitor/issues
- 文档更新: 请查看项目Wiki

---

## 🎉 部署完成

恭喜！您已成功部署网址监控系统的完整Docker化方案。

### 访问地址
- **前端界面**: http://localhost
- **后端API**: http://localhost:5013
- **API文档**: http://localhost:5013/api/docs

### 默认账户
- **用户名**: admin
- **密码**: admin123

### 下一步
1. 修改默认密码
2. 配置邮件通知
3. 添加监控网站
4. 设置SSL证书
5. 配置定时备份

祝您使用愉快！ 🚀