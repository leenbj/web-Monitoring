#!/bin/bash

# 数据库初始化脚本（用于宝塔面板MySQL）

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_blue() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 读取配置
load_config() {
    if [ -f ".env.backend" ]; then
        source .env.backend
    else
        log_warn "配置文件 .env.backend 不存在，使用默认配置"
        DB_HOST=${DB_HOST:-localhost}
        DB_PORT=${DB_PORT:-3306}
        DB_USER=${DB_USER:-monitor_user}
        DB_PASSWORD=${DB_PASSWORD:-BaotaUser2024!}
        DB_NAME=${DB_NAME:-website_monitor}
    fi
}

# 创建数据库和用户
create_database() {
    log_blue "创建数据库和用户..."
    
    # 提示用户输入root密码
    echo "请输入MySQL root密码:"
    read -s ROOT_PASSWORD
    
    if [ -z "$ROOT_PASSWORD" ]; then
        log_error "root密码不能为空"
        return 1
    fi
    
    # 连接MySQL创建数据库
    mysql -h "$DB_HOST" -P "$DB_PORT" -u root -p"$ROOT_PASSWORD" << EOF
-- 创建数据库
CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建用户
CREATE USER IF NOT EXISTS '$DB_USER'@'%' IDENTIFIED BY '$DB_PASSWORD';
CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';

-- 授权
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'%';
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';

-- 刷新权限
FLUSH PRIVILEGES;

-- 显示创建结果
SELECT User, Host FROM mysql.user WHERE User = '$DB_USER';
SHOW DATABASES LIKE '$DB_NAME';
EOF
    
    if [ $? -eq 0 ]; then
        log_info "数据库和用户创建成功"
    else
        log_error "数据库创建失败"
        return 1
    fi
}

# 测试数据库连接
test_connection() {
    log_blue "测试数据库连接..."
    
    mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" -e "USE $DB_NAME; SELECT 1 as test;" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        log_info "数据库连接测试成功"
    else
        log_error "数据库连接测试失败"
        return 1
    fi
}

# 初始化数据表（使用后端容器）
init_tables() {
    log_blue "初始化数据表..."
    
    # 检查后端容器是否运行
    if ! docker ps | grep -q "website_monitor_backend"; then
        log_warn "后端容器未运行，跳过表初始化"
        log_info "请在后端启动后运行: docker exec website_monitor_backend python /app/init_user_table_baota.py"
        return 0
    fi
    
    # 在后端容器中执行初始化
    docker exec website_monitor_backend python /app/init_user_table_baota.py
    
    if [ $? -eq 0 ]; then
        log_info "数据表初始化成功"
    else
        log_error "数据表初始化失败"
        return 1
    fi
}

# 显示配置信息
show_config() {
    log_blue "数据库配置信息"
    
    echo ""
    echo "数据库连接信息："
    echo "  主机: $DB_HOST:$DB_PORT"
    echo "  数据库: $DB_NAME"
    echo "  用户: $DB_USER"
    echo "  密码: $DB_PASSWORD"
    echo ""
    echo "后端连接字符串："
    echo "  DATABASE_URL=mysql+pymysql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME?charset=utf8mb4"
    echo ""
}

# 主函数
main() {
    echo ""
    echo "========================================="
    echo "🗄️  数据库初始化脚本"
    echo "========================================="
    echo ""
    
    # 检查MySQL客户端
    if ! command -v mysql &> /dev/null; then
        log_error "MySQL客户端未安装"
        echo "请安装MySQL客户端:"
        echo "  CentOS/RHEL: yum install mysql"
        echo "  Ubuntu/Debian: apt install mysql-client"
        exit 1
    fi
    
    # 加载配置
    load_config
    
    # 显示配置
    show_config
    
    # 执行初始化
    echo "请确认数据库配置正确，然后按Enter继续..."
    read
    
    create_database
    test_connection
    init_tables
    
    echo ""
    echo "========================================="
    echo "✅ 数据库初始化完成！"
    echo "========================================="
    echo ""
    echo "下一步："
    echo "  1. 启动后端: docker-compose -f docker-compose-backend-only.yml up -d"
    echo "  2. 构建前端: ./build-frontend.sh"
    echo "  3. 配置Nginx"
    echo ""
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi