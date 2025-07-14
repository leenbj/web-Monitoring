# 网址监控系统 - 前后端分离部署方案

## 📋 部署概述

本项目采用前后端分离的部署架构：
- **前端**: Vue.js静态文件部署，通过Nginx代理
- **后端**: Docker容器化部署，通过GitHub Actions自动构建镜像
- **数据库**: MySQL容器化部署
- **缓存**: Redis容器化部署

## 🏗️ 架构图

```
[用户] → [Nginx] → [前端静态文件]
                ↓
              [后端API] → [MySQL] + [Redis]
```

## 🚀 快速部署

### 1. 环境准备

```bash
# 服务器要求
# - Ubuntu 20.04+ / CentOS 8+
# - Docker 20.10+
# - Docker Compose 2.0+
# - Nginx 1.18+
# - 2GB+ RAM, 20GB+ 磁盘空间

# 安装Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.17.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 安装Nginx
sudo apt update
sudo apt install nginx -y
```

### 2. 代码部署

```bash
# 克隆项目
git clone https://github.com/yourusername/website-monitor.git
cd website-monitor

# 创建环境配置文件
cp deployment/.env.example deployment/.env
vim deployment/.env  # 配置环境变量
```

### 3. 环境变量配置

创建 `deployment/.env` 文件：

```bash
# 数据库配置
DB_ROOT_PASSWORD=your_root_password_here
DB_PASSWORD=your_db_password_here

# Redis配置
REDIS_PASSWORD=your_redis_password_here

# 应用配置
SECRET_KEY=your_secret_key_here_min_32_chars
JWT_SECRET_KEY=your_jwt_secret_here_min_32_chars

# 邮件配置
MAIL_SERVER=smtp.qq.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your_email@qq.com
MAIL_PASSWORD=your_email_app_password

# 部署配置
DEPLOY_HOST=your_server_ip
DEPLOY_USERNAME=root
DEPLOY_PORT=22
```

### 4. 前端部署

```bash
# 构建前端
cd frontend
npm install
npm run build

# 部署到Nginx目录
sudo mkdir -p /var/www/website-monitor
sudo cp -r dist/* /var/www/website-monitor/
sudo chown -R www-data:www-data /var/www/website-monitor
```

### 5. 后端部署

```bash
# 使用Docker Compose部署
cd deployment
docker-compose -f docker-compose.prod.yml up -d

# 查看服务状态
docker-compose -f docker-compose.prod.yml ps
```

### 6. Nginx配置

```bash
# 复制Nginx配置
sudo cp deployment/nginx/website-monitor.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/website-monitor.conf /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重载Nginx
sudo systemctl reload nginx
```

## 🔧 GitHub Actions配置

### 1. 设置GitHub Secrets

在GitHub仓库设置中添加以下Secrets：

```bash
# 服务器部署
DEPLOY_HOST          # 服务器IP地址
DEPLOY_USERNAME      # 服务器用户名
DEPLOY_SSH_KEY       # SSH私钥
DEPLOY_PORT          # SSH端口(默认22)

# Docker Hub (可选)
DOCKERHUB_USERNAME   # Docker Hub用户名
DOCKERHUB_TOKEN      # Docker Hub访问令牌
```

### 2. 自动化流程

- **前端构建**: 推送到`main`分支时自动构建前端静态文件
- **后端构建**: 推送到`main`分支时自动构建Docker镜像
- **自动部署**: 构建完成后自动部署到服务器

### 3. 工作流文件

- `.github/workflows/frontend-deploy.yml`: 前端构建和部署
- `.github/workflows/backend-docker.yml`: 后端Docker镜像构建

## 📊 监控和维护

### 1. 服务监控

```bash
# 查看服务状态
docker-compose -f deployment/docker-compose.prod.yml ps

# 查看日志
docker-compose -f deployment/docker-compose.prod.yml logs -f backend

# 查看资源使用
docker stats
```

### 2. 健康检查

```bash
# 检查前端
curl -I http://your-domain.com

# 检查后端API
curl -I http://your-domain.com/api/health

# 检查数据库
docker exec -it website-monitor-mysql mysql -u monitor_user -p -e "SELECT 1"
```

### 3. 备份和恢复

```bash
# 数据库备份
docker exec website-monitor-mysql mysqldump -u monitor_user -p website_monitor > backup.sql

# 数据库恢复
docker exec -i website-monitor-mysql mysql -u monitor_user -p website_monitor < backup.sql

# 数据卷备份
docker run --rm -v website-monitor_mysql_data:/data -v $(pwd):/backup alpine tar czf /backup/mysql_backup.tar.gz /data
```

## 🔒 安全配置

### 1. SSL证书配置

```bash
# 使用Let's Encrypt
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com

# 或者使用自签名证书
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/your-domain.com.key \
    -out /etc/ssl/certs/your-domain.com.crt
```

### 2. 防火墙配置

```bash
# 配置UFW防火墙
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 3. 安全加固

```bash
# 禁用root登录
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config

# 更改SSH端口
sudo sed -i 's/#Port 22/Port 2222/' /etc/ssh/sshd_config

# 重启SSH服务
sudo systemctl restart sshd
```

## 📈 性能优化

### 1. Nginx优化

```nginx
# 增加worker连接数
worker_connections 1024;

# 启用gzip压缩
gzip on;
gzip_comp_level 6;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

# 设置缓存
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### 2. Docker优化

```bash
# 限制容器资源
docker-compose -f deployment/docker-compose.prod.yml up -d --scale backend=2

# 使用多阶段构建减少镜像大小
# 已在Dockerfile中配置
```

## 🐛 故障排查

### 1. 常见问题

| 问题 | 解决方案 |
|------|----------|
| 前端404错误 | 检查Nginx配置和静态文件路径 |
| 后端连接失败 | 检查Docker容器状态和端口映射 |
| 数据库连接失败 | 检查MySQL容器状态和环境变量 |
| SSL证书错误 | 检查证书路径和有效期 |

### 2. 日志查看

```bash
# Nginx日志
sudo tail -f /var/log/nginx/website-monitor.access.log
sudo tail -f /var/log/nginx/website-monitor.error.log

# 应用日志
docker-compose -f deployment/docker-compose.prod.yml logs -f backend

# 系统日志
journalctl -u nginx -f
```

## 📝 更新和升级

### 1. 应用更新

```bash
# 拉取最新代码
git pull origin main

# 更新前端
cd frontend
npm install
npm run build
sudo cp -r dist/* /var/www/website-monitor/

# 更新后端
cd deployment
docker-compose -f docker-compose.prod.yml pull backend
docker-compose -f docker-compose.prod.yml up -d backend
```

### 2. 系统维护

```bash
# 清理Docker资源
docker system prune -a

# 清理日志
sudo journalctl --vacuum-time=30d

# 更新系统
sudo apt update && sudo apt upgrade -y
```

## 📞 技术支持

如需技术支持或遇到问题，请通过以下方式联系：

- 📧 邮箱: support@example.com
- 💬 Issues: https://github.com/yourusername/website-monitor/issues
- 📖 文档: https://docs.example.com

---

*© 2024 网址监控系统 | 版本 1.0.0*