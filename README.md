# 网址监控系统

一个功能完整的网址监控平台，支持多网站监控、状态检测、用户管理和邮件通知。

## 功能特性

### 核心功能
- **网站监控**：支持批量导入和监控多个网站
- **状态检测**：实时检测网站可用性和响应时间
- **智能分组**：按需求对监控网站进行分组管理
- **状态变化跟踪**：记录和展示网站状态变化历史
- **邮件通知**：网站状态异常时自动发送邮件提醒

### 用户管理
- **用户认证**：完整的登录注册系统
- **权限控制**：管理员可管理用户账户
- **用户权限**：登录后才能操作系统功能
- **默认管理员**：系统预设管理员账户

### 系统功能
- **文件管理**：支持文件上传下载
- **任务调度**：自动化监控任务执行
- **性能监控**：系统性能实时监控
- **数据导出**：监控结果数据导出功能

## 技术架构

### 后端技术栈
- **框架**：Flask
- **数据库**：MySQL/SQLite
- **任务调度**：APScheduler
- **邮件服务**：SMTP
- **API**：RESTful API设计

### 前端技术栈
- **框架**：Vue.js 3
- **UI组件**：Element Plus
- **状态管理**：Pinia
- **路由**：Vue Router
- **构建工具**：Vite

### 部署方案
- **容器化**：Docker & Docker Compose
- **反向代理**：Nginx
- **SSL支持**：HTTPS配置
- **环境变量**：灵活的配置管理

## 快速开始

### 环境要求
- Python 3.8+
- Node.js 16+
- MySQL 5.7+ 或 SQLite
- Docker (可选)

### 安装部署

#### 1. 克隆项目
```bash
git clone https://github.com/leenbj/web-Monitoring.git
cd web-Monitoring
```

#### 2. 后端部署
```bash
# 安装Python依赖
pip install -r requirements.txt

# 初始化数据库
python init_database.py

# 创建默认管理员用户
python create_default_user.py

# 启动后端服务
python run_backend.py
```

#### 3. 前端部署
```bash
cd frontend

# 安装依赖
npm install

# 开发模式启动
npm run dev

# 生产构建
npm run build
```

#### 4. Docker部署（推荐）
```bash
# 使用Docker Compose一键部署
docker-compose up -d

# 检查服务状态
docker-compose ps
```

### 配置说明

#### 环境变量配置
复制环境变量模板：
```bash
cp .env.template .env
```

主要配置项：
- `DATABASE_URL`：数据库连接地址
- `SECRET_KEY`：应用密钥
- `MAIL_SERVER`：邮件服务器配置
- `ADMIN_EMAIL`：管理员邮箱

#### 数据库配置
支持MySQL和SQLite两种数据库：

**MySQL配置**：
```env
DATABASE_URL=mysql://username:password@localhost:3306/web_monitoring
```

**SQLite配置**：
```env
DATABASE_URL=sqlite:///database/web_monitoring.db
```

## 使用指南

### 默认登录信息
- 用户名：`admin`
- 密码：`admin123`

### 主要功能操作

#### 1. 网站管理
- 添加监控网站：在"网站管理"页面添加URL
- 批量导入：支持CSV文件批量导入网站
- 分组管理：创建分组并分配网站

#### 2. 监控设置
- 检测间隔：设置监控频率
- 邮件通知：配置异常通知邮箱
- 超时设置：设置网站响应超时时间

#### 3. 结果查看
- 实时状态：查看网站当前状态
- 历史记录：查看状态变化历史
- 性能数据：查看响应时间趋势

## API接口

### 认证接口
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/logout` - 用户登出
- `GET /api/auth/user` - 获取用户信息

### 网站监控接口
- `GET /api/websites` - 获取网站列表
- `POST /api/websites` - 添加网站
- `PUT /api/websites/{id}` - 更新网站
- `DELETE /api/websites/{id}` - 删除网站

### 监控结果接口
- `GET /api/results` - 获取监控结果
- `GET /api/status-changes` - 获取状态变化记录

## 开发指南

### 目录结构
```
网址监控/
├── backend/          # 后端代码
│   ├── api/         # API接口
│   ├── services/    # 业务服务
│   ├── models.py    # 数据模型
│   └── app.py       # 应用入口
├── frontend/        # 前端代码
│   ├── src/
│   │   ├── components/  # Vue组件
│   │   ├── views/      # 页面视图
│   │   ├── stores/     # 状态管理
│   │   └── utils/      # 工具函数
├── mysql/           # MySQL配置
├── nginx/           # Nginx配置
└── docs/            # 文档
```

### 开发环境设置
```bash
# 启动开发服务器
./start-backend.sh
./start-frontend-dev.sh

# 运行测试
python -m pytest tests/

# 代码格式化
black backend/
prettier --write frontend/src/
```

## 部署说明

### 生产环境部署

#### 1. 服务器要求
- CPU：2核心以上
- 内存：4GB以上
- 存储：20GB以上
- 操作系统：Ubuntu 20.04+ / CentOS 7+

#### 2. 宝塔面板部署
```bash
# 使用宝塔部署脚本
./start-baota.sh

# 配置Nginx
cp nginx-baota.conf /www/server/nginx/conf.d/
```

#### 3. 性能优化
- 数据库连接池配置
- Redis缓存配置
- 静态文件CDN配置
- 监控任务优化

### 安全配置
- SSL证书配置
- 防火墙设置
- 数据库安全配置
- API访问限制

## 故障排除

### 常见问题

#### 1. 数据库连接失败
```bash
# 检查数据库服务状态
systemctl status mysql

# 测试数据库连接
python -c "from backend.database import test_connection; test_connection()"
```

#### 2. 前端无法访问API
```bash
# 检查后端服务状态
ps aux | grep python

# 检查端口占用
netstat -tulpn | grep :5000
```

#### 3. 邮件发送失败
- 检查SMTP服务器配置
- 验证邮箱授权码
- 确认防火墙端口开放

### 日志查看
```bash
# 查看应用日志
tail -f logs/app.log

# 查看错误日志
tail -f logs/error.log

# 查看Nginx日志
tail -f nginx/logs/access.log
```

## 版本更新

### 更新步骤
1. 备份数据库和配置文件
2. 拉取最新代码
3. 安装新依赖
4. 运行数据库迁移
5. 重启服务

### 数据库迁移
```bash
# 运行数据库迁移脚本
python database_migration_v5.py
```

## 贡献指南

### 开发规范
- 遵循PEP 8代码规范
- 编写单元测试
- 提交前运行代码检查
- 编写清晰的提交信息

### 提交流程
1. Fork项目
2. 创建功能分支
3. 编写代码和测试
4. 提交Pull Request

## 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

## 联系方式

- 项目地址：https://github.com/leenbj/web-Monitoring
- 问题反馈：请在GitHub Issues中提交
- 邮箱：admin@example.com

## 更新日志

### v2.0.0 (2024-01-20)
- 新增用户认证和权限管理系统
- 优化监控性能和稳定性
- 添加Docker部署支持
- 改进前端UI和用户体验

### v1.0.0 (2023-12-01)
- 基础网站监控功能
- 邮件通知系统
- Web管理界面
- RESTful API接口

---

感谢使用网址监控系统！如有问题请提交Issue或联系维护者。 