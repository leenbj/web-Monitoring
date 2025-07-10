#!/bin/bash

# 灵活的数据库初始化脚本

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

# 检测MySQL连接方式
detect_mysql_access() {
    log_blue "检测MySQL访问方式..."
    
    # 方式1: 尝试无密码连接（开发环境）
    if mysql -h "$DB_HOST" -P "$DB_PORT" -u root -e "SELECT 1;" >/dev/null 2>&1; then
        log_info "检测到无密码root访问"
        MYSQL_ROOT_AUTH="mysql -h $DB_HOST -P $DB_PORT -u root"
        return 0
    fi
    
    # 方式2: 尝试宝塔面板常见密码
    local common_passwords=("" "root" "123456" "password" "admin")
    for pwd in "${common_passwords[@]}"; do
        if mysql -h "$DB_HOST" -P "$DB_PORT" -u root -p"$pwd" -e "SELECT 1;" >/dev/null 2>&1; then
            log_info "检测到root密码: [已隐藏]"
            MYSQL_ROOT_AUTH="mysql -h $DB_HOST -P $DB_PORT -u root -p$pwd"
            return 0
        fi
    done
    
    # 方式3: 手动输入密码
    echo "请输入MySQL root密码:"
    read -s ROOT_PASSWORD
    
    if mysql -h "$DB_HOST" -P "$DB_PORT" -u root -p"$ROOT_PASSWORD" -e "SELECT 1;" >/dev/null 2>&1; then
        log_info "root密码验证成功"
        MYSQL_ROOT_AUTH="mysql -h $DB_HOST -P $DB_PORT -u root -p$ROOT_PASSWORD"
        return 0
    else
        log_error "root密码验证失败"
        return 1
    fi
}

# 生成SQL脚本
generate_sql() {
    cat > /tmp/init_db.sql << EOF
-- 创建数据库
CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建用户（如果不存在）
CREATE USER IF NOT EXISTS '$DB_USER'@'%' IDENTIFIED BY '$DB_PASSWORD';
CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';

-- 授权
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'%';
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';

-- 刷新权限
FLUSH PRIVILEGES;

-- 验证创建结果
USE $DB_NAME;
SELECT 'Database created successfully' AS result;
SELECT User, Host FROM mysql.user WHERE User = '$DB_USER';
EOF
}

# 执行数据库初始化
execute_database_init() {
    log_blue "执行数据库初始化..."
    
    generate_sql
    
    if $MYSQL_ROOT_AUTH < /tmp/init_db.sql; then
        log_info "数据库初始化成功"
        rm -f /tmp/init_db.sql
        return 0
    else
        log_error "数据库初始化失败"
        rm -f /tmp/init_db.sql
        return 1
    fi
}

# 测试连接
test_connection() {
    log_blue "测试应用数据库连接..."
    
    if mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" -e "USE $DB_NAME; SELECT 1 as test;" >/dev/null 2>&1; then
        log_info "✅ 应用数据库连接成功"
        return 0
    else
        log_error "❌ 应用数据库连接失败"
        
        # 显示调试信息
        echo ""
        echo "调试信息："
        echo "  连接字符串: mysql://$DB_USER:***@$DB_HOST:$DB_PORT/$DB_NAME"
        echo ""
        echo "请检查："
        echo "  1. 数据库服务是否运行"
        echo "  2. 用户名和密码是否正确"
        echo "  3. 网络连接是否正常"
        echo ""
        return 1
    fi
}

# 手动创建指南
show_manual_guide() {
    log_blue "手动创建数据库指南"
    
    echo ""
    echo "如果自动创建失败，请手动执行以下SQL："
    echo ""
    echo "-- 1. 登录MySQL"
    echo "mysql -u root -p"
    echo ""
    echo "-- 2. 执行以下SQL语句："
    echo "CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    echo "CREATE USER IF NOT EXISTS '$DB_USER'@'%' IDENTIFIED BY '$DB_PASSWORD';"
    echo "CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';"
    echo "GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'%';"
    echo "GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';"
    echo "FLUSH PRIVILEGES;"
    echo ""
    echo "-- 3. 验证创建"
    echo "USE $DB_NAME;"
    echo "SELECT User, Host FROM mysql.user WHERE User = '$DB_USER';"
    echo ""
}

# 检查宝塔面板环境
check_baota_panel() {
    log_blue "检查宝塔面板环境..."
    
    if [ -d "/www/server" ] || [ -d "/usr/local/bt" ]; then
        log_info "检测到宝塔面板环境"
        
        echo ""
        echo "宝塔面板MySQL管理："
        echo "  1. 登录宝塔面板 -> 数据库"
        echo "  2. 添加数据库: $DB_NAME"
        echo "  3. 添加用户: $DB_USER"
        echo "  4. 设置密码: $DB_PASSWORD"
        echo "  5. 权限设置: 所有权限"
        echo ""
        
        read -p "是否已在宝塔面板中创建数据库？(y/n): " panel_created
        if [ "$panel_created" = "y" ]; then
            log_info "跳过自动创建，直接测试连接"
            test_connection
            return $?
        fi
    fi
    
    return 1
}

# 显示连接信息
show_connection_info() {
    log_blue "数据库连接信息"
    
    echo ""
    echo "配置信息："
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
    echo "🗄️  灵活数据库初始化脚本"
    echo "========================================="
    echo ""
    
    # 加载配置
    load_config
    
    # 显示连接信息
    show_connection_info
    
    # 检查宝塔面板环境
    if check_baota_panel; then
        echo ""
        echo "✅ 数据库配置完成！"
        return 0
    fi
    
    # 检查MySQL客户端
    if ! command -v mysql &> /dev/null; then
        log_error "MySQL客户端未安装"
        echo ""
        echo "安装MySQL客户端："
        echo "  CentOS/RHEL: yum install mysql"
        echo "  Ubuntu/Debian: apt install mysql-client"
        echo ""
        show_manual_guide
        return 1
    fi
    
    # 检测MySQL连接方式
    if detect_mysql_access; then
        # 执行数据库初始化
        if execute_database_init; then
            # 测试连接
            test_connection
        else
            show_manual_guide
            return 1
        fi
    else
        log_error "无法连接到MySQL服务器"
        show_manual_guide
        return 1
    fi
    
    echo ""
    echo "========================================="
    echo "✅ 数据库初始化完成！"
    echo "========================================="
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi