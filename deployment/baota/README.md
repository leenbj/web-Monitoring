# 网址监控系统 - 宝塔面板部署方案

## 📋 部署概述

本文档详细介绍如何在宝塔面板环境下部署网址监控系统：
- **前端**: 本地构建后上传到宝塔面板，通过Nginx提供静态文件服务
- **后端**: 使用Docker Hub自动构建的镜像，通过Docker Compose部署
- **数据库**: MySQL和Redis容器化部署
- **管理**: 集成宝塔面板的管理功能

## 🏗️ 架构图

```
[用户] → [宝塔面板Nginx] → [前端静态文件]
                         ↓
                      [Docker后端] → [MySQL容器] + [Redis容器]
                         ↓
                   [PhpMyAdmin管理] + [Redis Commander管理]
```

## 🚀 快速部署指南

### 步骤1: 准备宝塔面板环境

#### 1.1 安装宝塔面板
```bash
# CentOS/RHEL
yum install -y wget && wget -O install.sh http://download.bt.cn/install/install_6.0.sh && sh install.sh

# Ubuntu/Debian  
wget -O install.sh http://download.bt.cn/install/install-ubuntu_6.0.sh && sudo bash install.sh

# 安装完成后记录访问地址、用户名和密码
```

#### 1.2 安装必要组件
在宝塔面板中安装以下组件：
- **Nginx** (1.20+)
- **Docker** (20.10+)
- **Docker Compose** (2.0+)
- **PM2管理器** (可选)

#### 1.3 配置防火墙
在宝塔面板 → 安全 → 防火墙中开放端口：
- `80` (HTTP)
- `443` (HTTPS) 
- `5000` (后端API)
- `8080` (PhpMyAdmin，可选)
- `8081` (Redis Commander，可选)

### 步骤2: 配置GitHub Actions自动构建

#### 2.1 配置GitHub Secrets
在GitHub仓库 → Settings → Secrets and variables → Actions 中添加：

```bash
# Docker Hub配置
DOCKERHUB_USERNAME=your_dockerhub_username
DOCKERHUB_TOKEN=your_dockerhub_access_token

# 可选：部署Webhook
DEPLOY_WEBHOOK=https://your-domain.com/api/deploy/webhook
```

#### 2.2 获取Docker Hub Access Token
1. 登录 [Docker Hub](https://hub.docker.com/)
2. 点击头像 → Account Settings
3. 选择 Security → New Access Token
4. 创建Token并保存到GitHub Secrets

### 步骤3: 本地构建前端

#### 3.1 本地构建
```bash
# 克隆项目
git clone https://github.com/yourusername/website-monitor.git
cd website-monitor

# 安装依赖并构建前端
cd frontend
npm install
npm run build

# 构建完成后 dist/ 目录包含所有静态文件
```

#### 3.2 上传前端文件
**方法1: 宝塔面板文件管理器**
1. 登录宝塔面板
2. 文件 → 进入网站根目录 `/www/wwwroot/`
3. 创建站点目录 `monitor.yourdomain.com`
4. 上传 `frontend/dist/` 中的所有文件

**方法2: SCP命令上传**
```bash
# 打包前端文件
cd frontend
tar -czf dist.tar.gz dist/

# 上传到服务器
scp dist.tar.gz root@your-server-ip:/www/wwwroot/monitor.yourdomain.com/

# 服务器上解压
ssh root@your-server-ip
cd /www/wwwroot/monitor.yourdomain.com/
tar -xzf dist.tar.gz --strip-components=1
rm dist.tar.gz
```

### 步骤4: 配置宝塔面板站点

#### 4.1 创建网站
1. 宝塔面板 → 网站 → 添加站点
2. 域名: `monitor.yourdomain.com`
3. 根目录: `/www/wwwroot/monitor.yourdomain.com`
4. PHP版本: 纯静态 (或选择任意版本，不影响)

#### 4.2 配置SSL证书
1. 网站设置 → SSL → Let's Encrypt
2. 或上传自有证书
3. 强制HTTPS开启

#### 4.3 配置Nginx
1. 网站设置 → 配置文件
2. 复制 `deployment/baota/nginx.conf` 内容
3. 修改域名为你的实际域名
4. 保存并重载Nginx

### 步骤5: 部署后端Docker服务

#### 5.1 上传Docker配置文件
```bash
# 服务器上创建项目目录
mkdir -p /www/website-monitor
cd /www/website-monitor

# 上传配置文件 (可使用宝塔文件管理器或scp)
# - docker-compose.yml
# - .env.baota (重命名为 .env)
```

#### 5.2 配置环境变量
```bash
# 编辑环境变量文件
vim .env

# 必须修改的配置:
DOCKERHUB_USERNAME=your_dockerhub_username
DB_PASSWORD=your_secure_password
DB_ROOT_PASSWORD=your_root_password
REDIS_PASSWORD=your_redis_password
SECRET_KEY=your-32-char-secret-key
JWT_SECRET_KEY=your-32-char-jwt-secret

# 邮件配置 (以QQ邮箱为例)
MAIL_SERVER=smtp.qq.com
MAIL_USERNAME=your_email@qq.com
MAIL_PASSWORD=your_qq_app_password
```

#### 5.3 启动Docker服务
```bash
# 拉取最新镜像
docker-compose pull

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend
```

#### 5.4 初始化数据库
```bash
# 等待数据库启动 (约30秒)
sleep 30

# 初始化数据库
docker-compose exec backend python init_database.py

# 或者手动连接到容器执行
docker exec -it website-monitor-backend bash
python init_database.py
```

### 步骤6: 验证部署

#### 6.1 健康检查
```bash
# 检查前端
curl -I https://monitor.yourdomain.com

# 检查后端API
curl -I https://monitor.yourdomain.com/api/health

# 检查数据库连接
docker-compose exec mysql mysql -u monitor_user -p -e "SELECT 1"
```

#### 6.2 访问测试
- **前端**: https://monitor.yourdomain.com
- **后端API**: https://monitor.yourdomain.com/api/health
- **PhpMyAdmin**: https://monitor.yourdomain.com/phpmyadmin (可选)
- **Redis Commander**: https://monitor.yourdomain.com/redis (可选)

#### 6.3 默认登录信息
- 用户名: `admin`
- 密码: `admin123`

## 🔧 宝塔面板集成功能

### 数据库管理
- 使用宝塔面板的数据库管理功能
- 或访问集成的PhpMyAdmin: `/phpmyadmin`

### 文件管理
- 宝塔面板文件管理器可直接管理前端文件
- 支持在线编辑和更新

### 日志监控
- Nginx访问日志: `/www/wwwlogs/monitor.yourdomain.com.log`
- Nginx错误日志: `/www/wwwlogs/monitor.yourdomain.com.error.log`
- 应用日志: `docker-compose logs -f backend`

### 定时任务
在宝塔面板 → 计划任务中设置：

#### 数据库备份
```bash
# 每日2点备份数据库
0 2 * * * cd /www/website-monitor && docker-compose exec mysql mysqldump -u monitor_user -p监控密码 website_monitor > /www/backup/db_$(date +\%Y\%m\%d).sql
```

#### 日志清理
```bash
# 每周清理7天前的日志
0 0 * * 0 find /www/wwwlogs/ -name "*.log" -mtime +7 -delete
```

#### Docker镜像更新
```bash
# 每天4点检查并更新Docker镜像
0 4 * * * cd /www/website-monitor && docker-compose pull && docker-compose up -d
```

## 📊 监控和维护

### 性能监控
使用宝塔面板的系统监控功能：
- CPU使用率
- 内存使用率  
- 磁盘使用率
- 网络流量

### 备份策略

#### 1. 数据库备份
```bash
# 手动备份
cd /www/website-monitor
docker-compose exec mysql mysqldump -u monitor_user -p website_monitor > backup_$(date +%Y%m%d).sql

# 自动备份脚本
#!/bin/bash
BACKUP_DIR="/www/backup/website-monitor"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# 备份数据库
docker-compose exec mysql mysqldump -u monitor_user -p监控密码 website_monitor > $BACKUP_DIR/db_$DATE.sql

# 备份应用数据
tar -czf $BACKUP_DIR/data_$DATE.tar.gz data/

# 删除7天前的备份
find $BACKUP_DIR -name "*.sql" -o -name "*.tar.gz" -mtime +7 -delete
```

#### 2. 网站文件备份
```bash
# 备份前端文件
tar -czf /www/backup/frontend_$(date +%Y%m%d).tar.gz /www/wwwroot/monitor.yourdomain.com/

# 备份Docker配置
tar -czf /www/backup/docker_config_$(date +%Y%m%d).tar.gz /www/website-monitor/
```

### 更新部署

#### 1. 前端更新
```bash
# 本地重新构建
cd frontend
npm run build

# 上传新的静态文件到宝塔面板
# 或使用自动化脚本同步
```

#### 2. 后端更新
```bash
# GitHub推送代码后自动构建新镜像
git push origin main

# 服务器拉取新镜像并重启
cd /www/website-monitor
docker-compose pull backend
docker-compose up -d backend
```

## 🔒 安全配置

### 宝塔面板安全
1. 修改默认端口 (不使用8888)
2. 启用面板SSL
3. 设置授权IP
4. 定期更新面板版本

### 应用安全
1. 修改默认密码
2. 启用HTTPS
3. 配置防火墙规则
4. 定期更新镜像

### 数据库安全
1. 修改默认密码
2. 限制远程连接
3. 定期备份数据
4. 监控异常登录

## 🐛 故障排查

### 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 前端404错误 | Nginx配置错误 | 检查网站根目录和Nginx配置 |
| API无法访问 | Docker服务未启动 | `docker-compose up -d` |
| 数据库连接失败 | 环境变量配置错误 | 检查`.env`文件中的数据库配置 |
| SSL证书错误 | 证书配置问题 | 重新申请或配置SSL证书 |
| 邮件发送失败 | SMTP配置错误 | 检查邮箱SMTP设置和应用密码 |

### 日志查看
```bash
# 宝塔面板日志
tail -f /www/wwwlogs/monitor.yourdomain.com.log
tail -f /www/wwwlogs/monitor.yourdomain.com.error.log

# Docker应用日志
cd /www/website-monitor
docker-compose logs -f backend
docker-compose logs -f mysql
docker-compose logs -f redis

# 系统日志
journalctl -u docker -f
```

### 服务重启
```bash
# 重启Nginx
sudo systemctl restart nginx

# 重启Docker服务
cd /www/website-monitor
docker-compose restart

# 重启特定容器
docker-compose restart backend
```

## 📱 移动端适配

前端已经过移动端优化，支持响应式设计：
- 手机浏览器访问
- 平板设备访问
- 宝塔面板移动APP管理

## 🔄 CI/CD集成

### GitHub Actions自动化
- 代码推送自动构建Docker镜像
- 支持多架构构建 (amd64/arm64)
- 自动更新Docker Hub描述
- 可选择Webhook通知部署

### 部署流程
1. 开发者推送代码到GitHub
2. GitHub Actions自动构建Docker镜像
3. 推送镜像到Docker Hub
4. 服务器定时拉取最新镜像
5. 自动重启更新服务

## 📞 技术支持

### 联系方式
- 📧 邮箱: support@example.com
- 💬 Issues: https://github.com/yourusername/website-monitor/issues
- 📖 文档: 详见本README

### 社区支持
- 宝塔面板官方论坛
- Docker Hub镜像页面
- GitHub项目主页

---

*© 2024 网址监控系统 | 宝塔面板部署版本 v1.0.0*