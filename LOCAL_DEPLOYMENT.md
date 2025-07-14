# 本地构建和部署指南

## 📋 概述

本指南详细介绍如何在本地环境中构建前后端镜像并部署网址监控系统。

## 🛠️ 准备工作

### 系统要求
- Docker >= 20.0
- Docker Compose >= 1.29
- Git（可选，用于版本控制）
- 至少 4GB 可用内存
- 至少 10GB 可用磁盘空间

### 检查环境
```bash
# 检查 Docker 版本
docker --version

# 检查 Docker Compose 版本
docker-compose --version

# 检查 Docker 服务状态
docker info
```

## 🚀 快速开始

### 方法1：一键启动（推荐）
```bash
# 自动构建镜像并启动服务
bash quick_start.sh
```

### 方法2：完整构建部署
```bash
# 运行完整的构建和部署流程
bash build_and_deploy.sh
```

### 方法3：手动构建
```bash
# 仅构建镜像
bash build_images.sh

# 然后启动服务
docker-compose up -d
```

## 📦 镜像构建详情

### 后端镜像构建
```bash
# 构建后端镜像
docker build -t web-monitoring-backend:latest -f Dockerfile .

# 查看构建的镜像
docker images | grep web-monitoring-backend
```

**后端镜像特性：**
- 基于 Python 3.11-slim
- 包含完整的 Flask 应用
- 预装 MySQL 和 Redis 客户端
- 集成健康检查
- 优化的启动脚本

### 前端镜像构建
```bash
# 进入前端目录
cd frontend

# 构建前端镜像
docker build -t web-monitoring-frontend:latest -f Dockerfile .

# 返回项目根目录
cd ..
```

**前端镜像特性：**
- 多阶段构建（Node.js 构建 + Nginx 运行）
- 基于 Nginx Alpine
- 集成 API 代理配置
- 静态文件压缩和缓存
- 支持 Vue Router 的 SPA 模式

## 🔧 部署配置

### 端口映射
| 服务 | 容器端口 | 主机端口 | 说明 |
|------|----------|----------|------|
| 前端 | 80 | 8080 | Vue.js 前端页面 |
| 后端 | 5000 | 5012 | Flask API 服务 |
| MySQL | 3306 | 33061 | 数据库服务 |
| Redis | 6379 | 63791 | 缓存服务 |

### 环境变量
```bash
# 数据库配置
DATABASE_URL=mysql://webmonitor:webmonitor123@mysql:3306/website_monitor

# 应用配置
SECRET_KEY=WebMonitorSecretKey2024ChangeMeInProduction
FLASK_ENV=production

# 时区设置
TZ=Asia/Shanghai
```

## 📊 服务管理

### 查看服务状态
```bash
# 查看所有服务状态
docker-compose ps

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mysql
```

### 重启服务
```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart backend
docker-compose restart frontend
```

### 停止服务
```bash
# 停止所有服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v
```

## 🔐 用户管理

### 默认登录信息
- **用户名**: admin
- **密码**: admin123
- **角色**: 管理员

### 登录问题修复
如果遇到登录问题，使用以下命令修复：
```bash
# 快速修复管理员用户
bash quick_fix_admin.sh

# 或者手动修复
docker-compose exec backend python3 -c "
import sys, os
sys.path.insert(0, '/app')
os.environ['DATABASE_URL'] = 'mysql://webmonitor:webmonitor123@mysql:3306/website_monitor'

from backend.app import create_app
from backend.models import User
from backend.database import get_db

app = create_app()
with app.app_context():
    with get_db() as db:
        existing = db.query(User).filter(User.username == 'admin').first()
        if existing:
            db.delete(existing)
            db.commit()
        
        admin = User(username='admin', email='admin@example.com', role='admin', status='active')
        admin.set_password('admin123')
        db.add(admin)
        db.commit()
        print('✅ 管理员用户创建成功!')
"
```

## 🔍 健康检查

### 服务健康状态
```bash
# 检查后端健康状态
curl http://localhost:5012/api/health

# 检查前端健康状态
curl http://localhost:8080/health

# 检查 MySQL 连接
docker-compose exec mysql mysqladmin ping

# 检查 Redis 连接
docker-compose exec redis redis-cli ping
```

### 容器健康检查
```bash
# 查看容器健康状态
docker-compose ps

# 查看具体的健康检查日志
docker inspect --format='{{json .State.Health}}' webmonitor-backend
```

## 📈 性能优化

### 镜像优化
- 使用多阶段构建减少镜像大小
- 利用 Docker 缓存层
- 最小化系统依赖

### 运行时优化
- 配置合适的资源限制
- 使用健康检查确保服务稳定
- 实施日志轮转

### 网络优化
- 使用自定义网络隔离服务
- 配置适当的端口映射
- 启用 gzip 压缩

## 🚨 故障排除

### 常见问题

#### 1. 构建失败
```bash
# 清理 Docker 缓存
docker system prune -a

# 重新构建镜像
docker-compose build --no-cache
```

#### 2. 服务启动失败
```bash
# 查看服务日志
docker-compose logs backend

# 检查容器状态
docker-compose ps

# 重启服务
docker-compose restart
```

#### 3. 数据库连接失败
```bash
# 检查 MySQL 服务状态
docker-compose exec mysql mysqladmin ping

# 重启 MySQL 服务
docker-compose restart mysql

# 查看 MySQL 日志
docker-compose logs mysql
```

#### 4. 前端无法访问
```bash
# 检查 Nginx 配置
docker-compose exec frontend nginx -t

# 重启前端服务
docker-compose restart frontend

# 查看前端日志
docker-compose logs frontend
```

### 日志分析
```bash
# 查看所有服务日志
docker-compose logs

# 实时查看特定服务日志
docker-compose logs -f backend

# 查看最近的错误日志
docker-compose logs --tail=100 backend | grep -i error
```

## 🔄 升级和维护

### 镜像更新
```bash
# 停止服务
docker-compose down

# 重新构建镜像
bash build_images.sh

# 启动服务
docker-compose up -d
```

### 数据备份
```bash
# 备份数据库
docker-compose exec mysql mysqldump -u webmonitor -p website_monitor > backup.sql

# 备份上传文件
docker cp webmonitor-backend:/app/backend/uploads ./backup_uploads/
```

### 数据恢复
```bash
# 恢复数据库
cat backup.sql | docker-compose exec -T mysql mysql -u webmonitor -p website_monitor

# 恢复上传文件
docker cp ./backup_uploads/ webmonitor-backend:/app/backend/uploads/
```

## 📋 检查清单

### 部署前检查
- [ ] Docker 和 Docker Compose 已安装
- [ ] 端口 8080、5012、33061、63791 未被占用
- [ ] 至少 4GB 可用内存
- [ ] 至少 10GB 可用磁盘空间

### 部署后验证
- [ ] 所有服务状态为 healthy
- [ ] 前端页面可正常访问
- [ ] 后端 API 响应正常
- [ ] 数据库连接成功
- [ ] 可以正常登录系统

### 生产环境建议
- [ ] 修改默认密码
- [ ] 配置 HTTPS
- [ ] 设置防火墙规则
- [ ] 配置日志轮转
- [ ] 定期备份数据

## 🎯 下一步

1. **访问系统**: http://localhost:8080
2. **登录系统**: admin / admin123
3. **修改密码**: 首次登录后立即修改
4. **配置监控**: 添加要监控的网站
5. **设置通知**: 配置邮件通知
6. **查看报告**: 查看监控结果和统计

## 📞 技术支持

如果遇到问题，请：
1. 查看日志文件
2. 检查系统资源
3. 参考故障排除部分
4. 提交 GitHub Issue

---

**注意**: 本指南适用于本地开发和测试环境。生产环境部署请参考生产部署指南。