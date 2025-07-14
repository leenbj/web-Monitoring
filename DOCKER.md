# 网址监控系统后端服务

## 项目简介

这是一个功能完整的网址监控系统后端服务，用于监控网站可用性、状态变化跟踪和邮件通知。

## 特性

- 🌐 **网站监控**: 支持HTTP/HTTPS网站状态检测
- 📊 **状态跟踪**: 记录网站状态变化历史
- 📧 **邮件通知**: 状态变化时自动发送邮件提醒
- 👥 **用户管理**: 多用户支持，权限控制
- 📈 **数据分析**: 提供详细的监控报告和统计
- 🔄 **定时任务**: 自动化监控任务调度
- 💾 **数据存储**: 支持MySQL数据库
- 🚀 **高性能**: 异步监控，支持大量网站并发检测

## 快速开始

### 使用Docker运行

```bash
# 拉取镜像
docker pull your-username/website-monitor-backend:latest

# 运行容器
docker run -d \
  --name website-monitor \
  -p 5000:5000 \
  -e DATABASE_URL=mysql://user:password@host:3306/database \
  -e SECRET_KEY=your-secret-key \
  -e JWT_SECRET_KEY=your-jwt-secret \
  your-username/website-monitor-backend:latest
```

### 使用Docker Compose

```yaml
version: '3.8'
services:
  backend:
    image: your-username/website-monitor-backend:latest
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=mysql://monitor_user:password@mysql:3306/website_monitor
      - SECRET_KEY=your-secret-key
      - JWT_SECRET_KEY=your-jwt-secret
      - MAIL_SERVER=smtp.example.com
      - MAIL_USERNAME=your-email@example.com
      - MAIL_PASSWORD=your-password
    depends_on:
      - mysql
      
  mysql:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=rootpassword
      - MYSQL_DATABASE=website_monitor
      - MYSQL_USER=monitor_user
      - MYSQL_PASSWORD=password
    volumes:
      - mysql_data:/var/lib/mysql

volumes:
  mysql_data:
```

## 环境变量

### 必需配置

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `DATABASE_URL` | 数据库连接URL | `mysql://user:pass@host:3306/db` |
| `SECRET_KEY` | Flask密钥 | `your-32-char-secret-key` |
| `JWT_SECRET_KEY` | JWT密钥 | `your-32-char-jwt-secret` |

### 邮件配置

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `MAIL_SERVER` | SMTP服务器 | `smtp.qq.com` |
| `MAIL_PORT` | SMTP端口 | `587` |
| `MAIL_USE_TLS` | 启用TLS | `true` |
| `MAIL_USERNAME` | 邮箱用户名 | `your@example.com` |
| `MAIL_PASSWORD` | 邮箱密码 | `your-password` |

### 可选配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `FLASK_ENV` | 运行环境 | `production` |
| `LOG_LEVEL` | 日志级别 | `INFO` |
| `TZ` | 时区 | `Asia/Shanghai` |

## API接口

### 健康检查
```
GET /api/health
```

### 用户认证
```
POST /api/auth/login
POST /api/auth/logout
GET /api/auth/user
```

### 网站管理
```
GET /api/websites       # 获取网站列表
POST /api/websites      # 添加网站
PUT /api/websites/{id}  # 更新网站
DELETE /api/websites/{id} # 删除网站
```

### 监控任务
```
GET /api/tasks          # 获取任务列表
POST /api/tasks         # 创建任务
PUT /api/tasks/{id}     # 更新任务
POST /api/tasks/{id}/run # 手动运行任务
```

### 监控结果
```
GET /api/results        # 获取监控结果
GET /api/status-changes # 获取状态变化记录
```

## 技术栈

- **后端**: Python 3.11 + Flask
- **数据库**: MySQL 8.0
- **缓存**: Redis (可选)
- **任务队列**: APScheduler
- **认证**: JWT
- **邮件**: Flask-Mail

## 镜像信息

- **基础镜像**: python:3.11-slim
- **多架构支持**: linux/amd64, linux/arm64
- **镜像大小**: ~200MB (优化后)
- **构建方式**: 多阶段构建
- **安全扫描**: 定期更新依赖

## 端口说明

- `5000`: HTTP API服务端口

## 数据卷

- `/app/backend/logs`: 应用日志
- `/app/backend/uploads`: 上传文件
- `/app/backend/downloads`: 下载文件
- `/app/database`: 数据库文件 (SQLite模式)

## 版本标签

- `latest`: 最新稳定版本
- `main`: 主分支最新代码
- `YYYYMMDD-HHmmss`: 时间戳版本
- `main-{commit}`: 带提交ID的版本

## 许可证

MIT License

## 支持

- 项目主页: https://github.com/yourusername/website-monitor
- Issues: https://github.com/yourusername/website-monitor/issues
- 文档: 详见项目README

## 更新日志

### v1.0.0
- 初始版本发布
- 支持网站监控和邮件通知
- 多用户管理功能
- Docker化部署