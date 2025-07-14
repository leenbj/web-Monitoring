# 宝塔面板部署指南

本指南提供在宝塔面板环境下部署网址监控系统的完整流程。

## 📋 部署架构

```
宝塔面板前后端分离环境：
┌─────────────────┐    ┌─────────────────┐
│   前端 (Nginx)   │    │   后端 (Nginx)   │
│   静态文件服务    │────→│   API代理服务    │
│   w4.799n.com   │    │   w3.799n.com   │
└─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  Docker容器群    │
                       │  Backend:5000   │
                       │  MySQL:3306     │
                       │  Redis:6379     │
                       └─────────────────┘
```

## 🚀 一、前端部署步骤

### 1.1 本地构建前端

```bash
# 在本地项目目录
cd frontend

# 安装依赖
npm install

# 构建生产版本
npm run build

# 验证构建结果
ls dist/
# 应该包含: index.html, assets/, favicon.ico
```

### 1.2 上传到宝塔面板

#### 方法A: 宝塔文件管理器上传
1. 登录宝塔面板
2. 文件 → 进入站点目录 `/www/wwwroot/w4.799n.com/`
3. 清空原有文件 (如果有)
4. 上传 `dist/` 目录中的所有文件
5. 确保文件权限为 644，目录权限为 755

#### 方法B: SCP命令上传
```bash
# 打包前端文件
cd frontend
tar -czf website-monitor-frontend.tar.gz dist/

# 上传到服务器
scp website-monitor-frontend.tar.gz root@your-server-ip:/tmp/

# 在服务器上解压
ssh root@your-server-ip
cd /www/wwwroot/w4.799n.com/
rm -rf * .*  # 清空目录
tar -xzf /tmp/website-monitor-frontend.tar.gz --strip-components=1
chown -R www:www *
chmod -R 644 *
find . -type d -exec chmod 755 {} \\;
rm /tmp/website-monitor-frontend.tar.gz
```

### 1.3 配置Nginx站点

#### 前端站点配置 (w4.799n.com)
1. 宝塔面板 → 网站 → 找到 `w4.799n.com` → 设置  
2. 配置文件 → 替换为以下内容：

```nginx
# 复制 deployment/nginx/bt-panel-site.conf 的内容
```

#### 后端站点配置 (w3.799n.com)  
1. 宝塔面板 → 网站 → 找到 `w3.799n.com` → 设置
2. 配置文件 → 替换为以下内容：

```nginx
# 复制 deployment/nginx/bt-panel-backend.conf 的内容
```

或者直接上传配置文件：
```bash
# 将前后端配置文件上传到服务器
scp deployment/nginx/bt-panel-site.conf root@your-server-ip:/tmp/frontend-nginx.conf
scp deployment/nginx/bt-panel-backend.conf root@your-server-ip:/tmp/backend-nginx.conf

# 在宝塔面板中应用配置
# 前端: 网站 → w4.799n.com → 设置 → 配置文件 → 粘贴 frontend-nginx.conf 内容
# 后端: 网站 → w3.799n.com → 设置 → 配置文件 → 粘贴 backend-nginx.conf 内容
```

### 1.4 验证前端部署

1. 访问 `https://w4.799n.com`
2. 检查页面是否正常显示
3. 浏览器F12检查是否有404错误
4. 测试前端路由是否正常 (刷新页面不报错)

### 1.5 验证后端代理

1. 访问 `https://w3.799n.com/api/health`
2. 检查API响应是否正常
3. 确认CORS头设置正确
4. 测试WebSocket连接 (如果使用)

## 🐳 二、后端部署步骤

### 2.1 安装Docker和Docker Compose

如果宝塔面板没有安装Docker：

```bash
# CentOS/RHEL
yum install -y docker docker-compose

# Ubuntu/Debian  
apt-get update
apt-get install -y docker.io docker-compose

# 启动Docker服务
systemctl enable docker
systemctl start docker

# 验证安装
docker --version
docker-compose --version
```

或使用宝塔面板的Docker管理器插件。

### 2.2 创建后端部署目录

```bash
# 创建部署目录
mkdir -p /opt/website-monitor
cd /opt/website-monitor

# 下载部署文件
wget https://raw.githubusercontent.com/yourusername/website-monitor/main/deployment/docker-compose.backend-only.yml
wget https://raw.githubusercontent.com/yourusername/website-monitor/main/deployment/.env.production

# 重命名环境配置文件
mv .env.production .env
```

### 2.3 配置环境变量

编辑 `.env` 文件：

```bash
vim .env
```

修改以下配置：

```env
# 数据库配置
DB_NAME=website_monitor
DB_USER=monitor_user
DB_PASSWORD=your_secure_password_here
DB_ROOT_PASSWORD=your_root_password_here

# Redis配置
REDIS_PASSWORD=your_redis_password_here

# 应用安全配置
SECRET_KEY=your-32-char-secret-key-change-this
JWT_SECRET_KEY=your-32-char-jwt-secret-key-change

# 邮件配置
MAIL_SERVER=smtp.qq.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your_email@qq.com
MAIL_PASSWORD=your_qq_app_password

# 端口配置
BACKEND_PORT=5000
MYSQL_PORT=3306
REDIS_PORT=6379
PHPMYADMIN_PORT=8080

# Docker Hub配置
DOCKERHUB_USERNAME=leenbj68719929

# 其他配置
TZ=Asia/Shanghai
LOG_LEVEL=INFO
```

### 2.4 启动后端服务

```bash
# 创建数据目录
mkdir -p data/{mysql,redis,backend} logs/backend uploads downloads user_files

# 拉取最新镜像
docker-compose -f docker-compose.backend-only.yml pull

# 启动服务
docker-compose -f docker-compose.backend-only.yml up -d

# 查看服务状态
docker-compose -f docker-compose.backend-only.yml ps

# 查看日志
docker-compose -f docker-compose.backend-only.yml logs -f backend
```

### 2.5 验证后端部署

```bash
# 检查容器状态
docker ps

# 测试API健康检查
curl http://localhost:5000/api/health

# 测试数据库连接
docker exec website-monitor-mysql mysql -u monitor_user -p website_monitor -e "SHOW TABLES;"

# 测试Redis连接
docker exec website-monitor-redis redis-cli auth your_redis_password ping
```

## 🔧 三、宝塔面板特定配置

### 3.1 防火墙配置

在宝塔面板 → 安全 → 防火墙中添加端口：

```
5000   # 后端API端口
3306   # MySQL端口 (可选，仅需要外部访问时)
6379   # Redis端口 (可选，仅需要外部访问时)
8080   # PhpMyAdmin端口 (可选)
```

### 3.2 宝塔监控配置

1. 安装系统监控插件
2. 监控项目添加：
   - Docker容器状态监控
   - 端口5000连通性监控
   - 磁盘空间监控 (Docker数据目录)

### 3.3 自动备份配置

在宝塔面板 → 计划任务中添加：

```bash
# 每日数据库备份 (凌晨2点)
#!/bin/bash
cd /opt/website-monitor
docker exec website-monitor-mysql mysqldump -u root -p${DB_ROOT_PASSWORD} website_monitor > backups/mysql_$(date +%Y%m%d_%H%M%S).sql
find backups/ -name "mysql_*.sql" -mtime +7 -delete

# 每周代码备份 (周日凌晨3点)  
#!/bin/bash
cd /www/wwwroot/w4.799n.com/
tar -czf /www/backup/frontend_$(date +%Y%m%d).tar.gz *
find /www/backup/ -name "frontend_*.tar.gz" -mtime +30 -delete
```

## 📊 四、部署验证清单

### ✅ 前端验证
- [ ] 访问 https://w3.799n.com 正常显示
- [ ] 前端路由工作正常 (页面刷新不报错)
- [ ] 静态资源加载正常 (无404错误)
- [ ] SSL证书有效
- [ ] 页面响应速度正常

### ✅ 后端验证
- [ ] Docker容器运行正常: `docker ps`
- [ ] API健康检查通过: `curl http://localhost:5000/api/health`
- [ ] 数据库连接正常
- [ ] Redis连接正常
- [ ] 日志输出正常

### ✅ 前后端连接验证
- [ ] 登录功能正常
- [ ] API请求无CORS错误
- [ ] 数据正常加载和保存
- [ ] 网站监控功能正常

## 🔄 五、更新部署流程

### 5.1 前端更新
```bash
# 本地构建新版本
cd frontend
npm run build

# 上传到宝塔面板
# 重复 1.2 节的上传步骤

# 清除浏览器缓存测试
```

### 5.2 后端更新
```bash
cd /opt/website-monitor

# 拉取新镜像
docker-compose -f docker-compose.backend-only.yml pull

# 重启服务
docker-compose -f docker-compose.backend-only.yml up -d

# 检查更新后状态
docker-compose -f docker-compose.backend-only.yml logs -f backend
```

## 🚨 六、故障排除

### 6.1 常见问题

**前端404错误**
```bash
# 检查文件权限
ls -la /www/wwwroot/w3.799n.com/
chown -R www:www /www/wwwroot/w3.799n.com/

# 检查Nginx配置
nginx -t
systemctl reload nginx
```

**后端连接失败**
```bash
# 检查容器状态
docker ps -a

# 查看详细日志
docker logs website-monitor-backend

# 检查端口占用
netstat -tulpn | grep 5000
```

**数据库连接失败**
```bash
# 检查MySQL容器
docker exec -it website-monitor-mysql mysql -u root -p

# 检查环境变量
cat .env | grep DB_
```

### 6.2 性能监控

```bash
# 监控容器资源使用
docker stats

# 监控磁盘空间
df -h
du -sh /opt/website-monitor/data/*

# 监控网络连接
ss -tulpn | grep -E "(5000|3306|6379)"
```

## 🎯 七、生产环境优化建议

1. **安全加固**
   - 修改默认端口
   - 设置复杂密码
   - 开启防火墙白名单
   - 定期更新系统

2. **性能优化**
   - 配置Redis缓存
   - 开启Nginx gzip压缩
   - 设置合理的缓存策略
   - 监控资源使用情况

3. **备份策略**
   - 自动化数据库备份
   - 代码版本控制
   - 配置文件备份
   - 制定恢复流程

这样的配置确保了在宝塔面板环境下的稳定部署和运行！