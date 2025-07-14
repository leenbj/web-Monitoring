# 前端静态文件部署指南

## 📋 前后端分离部署方案

### 🏗️ 架构说明

```
前端部署方式：
┌─────────────────┐
│   本地构建       │
│   npm run build │
│        ↓        │
│   dist/ 文件夹   │
│        ↓        │
│  上传到服务器    │
│   /www/wwwroot/  │
└─────────────────┘

后端部署方式：
┌─────────────────┐
│  Docker 容器     │
│  仅API服务       │
│  端口: 5000      │
└─────────────────┘

Nginx配置：
┌─────────────────┐
│  静态文件服务    │
│  /               │
│        +         │
│  反向代理        │
│  /api/* → 5000   │
└─────────────────┘
```

## 🚀 前端部署步骤

### 1. 本地构建前端

```bash
# 在项目根目录
cd frontend

# 安装依赖
npm install

# 构建生产版本
npm run build

# 构建完成后，dist/ 目录包含所有静态文件
ls dist/
# 输出: index.html  assets/  favicon.ico
```

### 2. 上传静态文件到服务器

#### 方法A: 使用SCP上传
```bash
# 打包前端文件
cd frontend
tar -czf frontend-dist.tar.gz dist/

# 上传到服务器
scp frontend-dist.tar.gz root@your-server-ip:/tmp/

# 在服务器上解压
ssh root@your-server-ip
cd /www/wwwroot/monitor.yourdomain.com/
tar -xzf /tmp/frontend-dist.tar.gz --strip-components=1
rm /tmp/frontend-dist.tar.gz
```

#### 方法B: 使用宝塔面板文件管理
```bash
1. 登录宝塔面板
2. 文件 → 进入网站根目录
3. 上传 dist/ 目录中的所有文件
4. 或者上传压缩包后在线解压
```

#### 方法C: 使用Git部署
```bash
# 服务器上
cd /www/wwwroot/monitor.yourdomain.com/
git clone https://github.com/yourusername/website-monitor.git temp
cp -r temp/frontend/dist/* ./
rm -rf temp
```

### 3. 配置服务器Nginx

#### 创建站点配置文件
```nginx
# /etc/nginx/sites-available/monitor.yourdomain.com
# 或宝塔面板站点配置

server {
    listen 80;
    listen 443 ssl http2;
    server_name monitor.yourdomain.com;
    
    # SSL配置 (如果启用HTTPS)
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    
    # 网站根目录
    root /www/wwwroot/monitor.yourdomain.com;
    index index.html;
    
    # 前端路由配置 (Vue Router)
    location / {
        try_files $uri $uri/ /index.html;
        
        # 静态文件缓存
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
        
        # HTML文件不缓存
        location ~* \.html$ {
            expires -1;
            add_header Cache-Control "no-cache, no-store, must-revalidate";
        }
    }
    
    # 后端API反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS配置 (如果需要)
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods 'GET, POST, PUT, DELETE, OPTIONS';
        add_header Access-Control-Allow-Headers 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization';
        
        if ($request_method = 'OPTIONS') {
            return 204;
        }
    }
    
    # 安全配置
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-Content-Type-Options "nosniff";
    add_header X-XSS-Protection "1; mode=block";
}
```

## 🔧 后端部署步骤

### 1. 部署纯后端服务

```bash
# 在服务器上
cd /opt/website-monitor  # 或其他目录

# 创建环境配置
cat > .env << 'EOF'
# 数据库配置
DB_NAME=website_monitor
DB_USER=monitor_user
DB_PASSWORD=your_secure_password
DB_ROOT_PASSWORD=your_root_password

# Redis配置
REDIS_PASSWORD=your_redis_password

# 应用配置
SECRET_KEY=your-32-char-secret-key
JWT_SECRET_KEY=your-32-char-jwt-secret

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
EOF

# 下载纯后端配置文件
wget https://raw.githubusercontent.com/yourusername/website-monitor/main/deployment/docker-compose.backend-only.yml

# 启动后端服务
docker-compose -f docker-compose.backend-only.yml up -d
```

### 2. 验证后端服务

```bash
# 检查容器状态
docker ps

# 检查API健康状态
curl http://localhost:5000/api/health

# 查看日志
docker logs website-monitor-backend
```

## 📊 部署验证清单

### ✅ 前端验证
- [ ] 静态文件上传到服务器网站目录
- [ ] Nginx配置正确，包含Vue Router支持
- [ ] 可以访问 https://yourdomain.com
- [ ] 前端页面正常显示
- [ ] 浏览器F12无404错误

### ✅ 后端验证
- [ ] Docker容器正常运行
- [ ] API健康检查通过: `curl http://localhost:5000/api/health`
- [ ] 数据库连接正常
- [ ] Redis连接正常
- [ ] PhpMyAdmin可访问 (可选)

### ✅ 前后端连接验证
- [ ] 前端可以调用后端API
- [ ] 登录功能正常
- [ ] API请求无CORS错误
- [ ] 数据正常加载和保存

## 🔄 更新部署流程

### 前端更新
```bash
# 本地重新构建
cd frontend
npm run build

# 上传新文件到服务器
# (重复上面的上传步骤)
```

### 后端更新
```bash
# 拉取新镜像
docker-compose -f docker-compose.backend-only.yml pull

# 重启服务
docker-compose -f docker-compose.backend-only.yml up -d
```

## 🎯 关键要点

1. **前端**: 纯静态文件，通过服务器Nginx提供
2. **后端**: Docker容器，只暴露API端口5000
3. **Nginx**: 既提供静态文件服务，又做API反向代理
4. **无需**: 在Docker中配置Nginx或前端文件
5. **分离**: 前后端完全独立部署和更新

这样的架构更清晰、更易维护，也更符合前后端分离的最佳实践！