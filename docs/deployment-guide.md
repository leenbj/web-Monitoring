# 宝塔面板部署指南

## 项目概述

本项目采用前后端分离架构：
- **前端**：Vue 3 + Element Plus + Vite
- **后端**：Flask + SQLAlchemy + SQLite
- **部署方式**：宝塔面板 + Nginx + Python

## 部署架构

```
用户请求 → Nginx → 前端静态文件 (Vue)
                 → 后端API (Flask)
```

## 服务器要求

### 系统要求
- 操作系统：CentOS 7+ / Ubuntu 18+ / Debian 9+
- 内存：至少 2GB RAM
- 硬盘：至少 10GB 可用空间
- Python：3.8+
- Node.js：16+

### 宝塔面板要求
- 宝塔面板版本：7.0+
- 已安装：Nginx、Python项目管理器、Node.js

## 部署步骤

### 第一步：准备服务器环境

1. **安装宝塔面板**
```bash
# CentOS安装命令
yum install -y wget && wget -O install.sh http://download.bt.cn/install/install_6.0.sh && sh install.sh

# Ubuntu/Debian安装命令
wget -O install.sh http://download.bt.cn/install/install-ubuntu_6.0.sh && sudo bash install.sh
```

2. **安装必要软件**
   - 登录宝塔面板
   - 软件商店 → 安装以下软件：
     - Nginx 1.20+
     - Python项目管理器
     - Node.js版本管理器
     - PM2管理器

### 第二步：上传项目文件

1. **创建项目目录**
```bash
# 在服务器上创建项目目录
mkdir -p /www/wwwroot/website-monitor
cd /www/wwwroot/website-monitor
```

2. **上传项目文件**
   - 方式一：使用宝塔面板文件管理器上传
   - 方式二：使用Git克隆（推荐）
```bash
git clone <your-repository-url> /www/wwwroot/website-monitor
```

3. **设置目录权限**
```bash
chown -R www:www /www/wwwroot/website-monitor
chmod -R 755 /www/wwwroot/website-monitor
```

### 第三步：部署后端服务

1. **创建Python虚拟环境**
```bash
cd /www/wwwroot/website-monitor
python3 -m venv venv
source venv/bin/activate
```

2. **安装Python依赖**
```bash
pip install -r requirements.txt
```

3. **配置数据库**
```bash
# 创建数据库目录
mkdir -p database
chmod 755 database

# 初始化数据库（如果需要）
python backend/database_migration_v5.py
```

4. **创建后端启动脚本**
```bash
# 创建启动脚本
cat > start_backend.sh << 'EOF'
#!/bin/bash
cd /www/wwwroot/website-monitor
source venv/bin/activate
export FLASK_ENV=production
export FLASK_RUN_PORT=5002
python backend/app.py
EOF

chmod +x start_backend.sh
```

5. **使用PM2管理后端服务**
   - 在宝塔面板 → PM2管理器
   - 添加项目：
     - 项目名称：website-monitor-backend
     - 启动文件：/www/wwwroot/website-monitor/start_backend.sh
     - 项目目录：/www/wwwroot/website-monitor
     - 启动方式：bash

### 第四步：部署前端服务

1. **安装Node.js依赖**
```bash
cd /www/wwwroot/website-monitor/frontend
npm install
```

2. **配置生产环境API地址**
```bash
# 创建生产环境配置
cat > .env.production << 'EOF'
VITE_API_BASE_URL=http://your-domain.com:5002
VITE_APP_TITLE=网址监控系统
EOF
```

3. **构建前端项目**
```bash
npm run build
```

4. **配置Nginx站点**
   - 宝塔面板 → 网站 → 添加站点
   - 域名：your-domain.com
   - 根目录：/www/wwwroot/website-monitor/frontend/dist

### 第五步：配置Nginx

1. **编辑Nginx配置**
   - 宝塔面板 → 网站 → 设置 → 配置文件

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # 前端静态文件
    location / {
        root /www/wwwroot/website-monitor/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
    
    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:5002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # 支持WebSocket（如果需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        root /www/wwwroot/website-monitor/frontend/dist;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # 安全设置
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    
    # 日志配置
    access_log /www/wwwlogs/website-monitor.access.log;
    error_log /www/wwwlogs/website-monitor.error.log;
}
```

2. **重载Nginx配置**
```bash
nginx -t && nginx -s reload
```

### 第六步：配置SSL证书（可选但推荐）

1. **申请SSL证书**
   - 宝塔面板 → 网站 → 设置 → SSL
   - 选择Let's Encrypt免费证书或上传自有证书

2. **强制HTTPS**
   - 开启"强制HTTPS"选项

### 第七步：配置防火墙和安全

1. **开放必要端口**
   - 宝塔面板 → 安全 → 防火墙
   - 开放端口：80, 443, 5002

2. **配置安全规则**
   - 限制后端端口5002仅本地访问
   - 配置IP白名单（如果需要）

## 部署验证

### 检查后端服务
```bash
# 检查后端是否运行
curl http://localhost:5002/api/websites/

# 检查PM2状态
pm2 status
```

### 检查前端服务
```bash
# 访问网站
curl http://your-domain.com

# 检查API代理
curl http://your-domain.com/api/websites/
```

### 检查日志
```bash
# 查看后端日志
tail -f /www/wwwroot/website-monitor/logs/app.log

# 查看Nginx日志
tail -f /www/wwwlogs/website-monitor.access.log
tail -f /www/wwwlogs/website-monitor.error.log
```

## 常见问题解决

### 1. 后端服务启动失败
```bash
# 检查Python环境
source /www/wwwroot/website-monitor/venv/bin/activate
python --version

# 检查依赖安装
pip list

# 手动启动测试
cd /www/wwwroot/website-monitor
python backend/app.py
```

### 2. 前端构建失败
```bash
# 清理缓存重新安装
cd /www/wwwroot/website-monitor/frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

### 3. API请求失败
- 检查Nginx配置中的proxy_pass地址
- 确认后端服务运行在正确端口
- 检查防火墙设置

### 4. 数据库权限问题
```bash
# 设置数据库文件权限
chown www:www /www/wwwroot/website-monitor/database/
chmod 755 /www/wwwroot/website-monitor/database/
chmod 644 /www/wwwroot/website-monitor/database/*.db
```

## 维护和监控

### 自动备份
```bash
# 创建备份脚本
cat > /www/wwwroot/website-monitor/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/www/backup/website-monitor"
mkdir -p $BACKUP_DIR

# 备份数据库
cp -r /www/wwwroot/website-monitor/database $BACKUP_DIR/database_$DATE

# 备份配置文件
tar -czf $BACKUP_DIR/config_$DATE.tar.gz \
    /www/wwwroot/website-monitor/backend/config.py \
    /www/wwwroot/website-monitor/frontend/.env.production

# 清理7天前的备份
find $BACKUP_DIR -name "*" -mtime +7 -delete
EOF

chmod +x /www/wwwroot/website-monitor/backup.sh

# 添加到定时任务
echo "0 2 * * * /www/wwwroot/website-monitor/backup.sh" | crontab -
```

### 监控脚本
```bash
# 创建监控脚本
cat > /www/wwwroot/website-monitor/monitor.sh << 'EOF'
#!/bin/bash
# 检查后端服务
if ! curl -s http://localhost:5002/api/websites/ > /dev/null; then
    echo "Backend service is down, restarting..."
    pm2 restart website-monitor-backend
fi

# 检查磁盘空间
DISK_USAGE=$(df /www | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "Disk usage is high: ${DISK_USAGE}%"
fi
EOF

chmod +x /www/wwwroot/website-monitor/monitor.sh

# 添加到定时任务
echo "*/5 * * * * /www/wwwroot/website-monitor/monitor.sh" | crontab -
```

## 性能优化建议

1. **启用Gzip压缩**
2. **配置静态资源缓存**
3. **使用CDN加速**
4. **数据库定期优化**
5. **日志轮转配置**

部署完成后，您的网址监控系统将通过 `http://your-domain.com` 访问！
