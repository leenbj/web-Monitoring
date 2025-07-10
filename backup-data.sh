#!/bin/bash

# 网址监控系统 - 数据备份脚本
# 版本: 2.0
# 功能: 自动备份数据库、文件和配置
# 日期: 2024-12-27

set -e

# ===========================================
# 配置变量
# ===========================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_BASE_DIR="./backups"
BACKUP_DIR="$BACKUP_BASE_DIR/backup_$(date +%Y%m%d_%H%M%S)"
COMPOSE_FILE="docker-compose.yml"
BAOTA_COMPOSE_FILE="docker-compose-baota.yml"

# 保留备份数量
KEEP_BACKUPS=7

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ===========================================
# 工具函数
# ===========================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_banner() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "💾 网址监控系统 - 数据备份"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📅 备份时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "📁 备份目录: $BACKUP_DIR"
    echo ""
}

# ===========================================
# 检测环境
# ===========================================

detect_environment() {
    log_info "检测部署环境..."
    
    if [[ -f "$BAOTA_COMPOSE_FILE" ]] && docker-compose -f "$BAOTA_COMPOSE_FILE" ps &>/dev/null; then
        COMPOSE_FILE="$BAOTA_COMPOSE_FILE"
        log_info "检测到宝塔面板部署环境"
    elif [[ -f "$COMPOSE_FILE" ]]; then
        log_info "检测到标准部署环境"
    else
        log_error "未找到有效的Docker Compose配置文件"
        return 1
    fi
    
    return 0
}

# ===========================================
# 创建备份目录
# ===========================================

create_backup_directory() {
    log_info "创建备份目录..."
    
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$BACKUP_DIR/database"
    mkdir -p "$BACKUP_DIR/files"
    mkdir -p "$BACKUP_DIR/config"
    mkdir -p "$BACKUP_DIR/logs"
    
    log_success "备份目录创建完成: $BACKUP_DIR"
}

# ===========================================
# 备份数据库
# ===========================================

backup_database() {
    log_info "备份数据库..."
    
    # 获取MySQL容器
    local mysql_container
    mysql_container=$(docker-compose -f "$COMPOSE_FILE" ps -q mysql 2>/dev/null || echo "")
    
    if [[ -n "$mysql_container" ]]; then
        # 从环境文件获取数据库密码
        local env_file=".env"
        if [[ "$COMPOSE_FILE" == *"baota"* ]]; then
            env_file=".env.baota"
        fi
        
        local mysql_root_password
        if [[ -f "$env_file" ]]; then
            mysql_root_password=$(grep "MYSQL_ROOT_PASSWORD" "$env_file" | cut -d'=' -f2 | tr -d ' ' 2>/dev/null || echo "")
        fi
        
        if [[ -z "$mysql_root_password" ]]; then
            mysql_root_password="WebMonitor2024!"
            log_warning "使用默认MySQL密码"
        fi
        
        # 备份所有数据库
        log_info "备份MySQL数据库..."
        if docker exec "$mysql_container" mysqldump -u root -p"$mysql_root_password" --all-databases --single-transaction --routines --triggers > "$BACKUP_DIR/database/mysql_all_databases.sql" 2>/dev/null; then
            log_success "MySQL数据库备份完成"
        else
            log_error "MySQL数据库备份失败"
            return 1
        fi
        
        # 备份特定数据库
        log_info "备份website_monitor数据库..."
        if docker exec "$mysql_container" mysqldump -u root -p"$mysql_root_password" --single-transaction --routines --triggers website_monitor > "$BACKUP_DIR/database/website_monitor.sql" 2>/dev/null; then
            log_success "website_monitor数据库备份完成"
        else
            log_warning "website_monitor数据库备份失败，可能数据库不存在"
        fi
    else
        log_warning "未找到MySQL容器，跳过MySQL备份"
    fi
    
    # 备份SQLite数据库（如果存在）
    if [[ -d "database" ]]; then
        log_info "备份SQLite数据库..."
        cp -r database/* "$BACKUP_DIR/database/" 2>/dev/null || true
        log_success "SQLite数据库备份完成"
    fi
    
    return 0
}

# ===========================================
# 备份文件
# ===========================================

backup_files() {
    log_info "备份应用文件..."
    
    # 备份上传文件
    if [[ -d "backend/uploads" ]]; then
        log_info "备份上传文件..."
        cp -r backend/uploads "$BACKUP_DIR/files/" 2>/dev/null || true
        log_success "上传文件备份完成"
    fi
    
    # 备份下载文件
    if [[ -d "backend/downloads" ]]; then
        log_info "备份下载文件..."
        cp -r backend/downloads "$BACKUP_DIR/files/" 2>/dev/null || true
        log_success "下载文件备份完成"
    fi
    
    # 备份用户文件
    if [[ -d "backend/user_files" ]]; then
        log_info "备份用户文件..."
        cp -r backend/user_files "$BACKUP_DIR/files/" 2>/dev/null || true
        log_success "用户文件备份完成"
    fi
    
    # 备份前端构建文件（可选）
    if [[ -d "frontend/dist" ]]; then
        log_info "备份前端构建文件..."
        cp -r frontend/dist "$BACKUP_DIR/files/" 2>/dev/null || true
        log_success "前端构建文件备份完成"
    fi
    
    return 0
}

# ===========================================
# 备份配置文件
# ===========================================

backup_configuration() {
    log_info "备份配置文件..."
    
    # 备份Docker配置
    cp docker-compose*.yml "$BACKUP_DIR/config/" 2>/dev/null || true
    cp Dockerfile* "$BACKUP_DIR/config/" 2>/dev/null || true
    
    # 备份环境配置
    cp .env* "$BACKUP_DIR/config/" 2>/dev/null || true
    
    # 备份Nginx配置
    if [[ -d "nginx" ]]; then
        cp -r nginx "$BACKUP_DIR/config/" 2>/dev/null || true
    fi
    
    # 备份MySQL配置
    if [[ -d "mysql/conf" ]]; then
        cp -r mysql/conf "$BACKUP_DIR/config/mysql_conf" 2>/dev/null || true
    fi
    
    # 备份初始化脚本
    cp *.sh "$BACKUP_DIR/config/" 2>/dev/null || true
    cp *.py "$BACKUP_DIR/config/" 2>/dev/null || true
    
    log_success "配置文件备份完成"
    return 0
}

# ===========================================
# 备份日志
# ===========================================

backup_logs() {
    log_info "备份日志文件..."
    
    # 备份应用日志
    if [[ -d "backend/logs" ]]; then
        cp -r backend/logs "$BACKUP_DIR/logs/backend_logs" 2>/dev/null || true
    fi
    
    if [[ -d "logs" ]]; then
        cp -r logs "$BACKUP_DIR/logs/system_logs" 2>/dev/null || true
    fi
    
    # 备份Nginx日志
    if [[ -d "nginx/logs" ]]; then
        cp -r nginx/logs "$BACKUP_DIR/logs/nginx_logs" 2>/dev/null || true
    fi
    
    # 备份Docker容器日志
    log_info "导出Docker容器日志..."
    if docker-compose -f "$COMPOSE_FILE" ps &>/dev/null; then
        docker-compose -f "$COMPOSE_FILE" logs > "$BACKUP_DIR/logs/docker_logs.txt" 2>/dev/null || true
    fi
    
    log_success "日志文件备份完成"
    return 0
}

# ===========================================
# 压缩备份
# ===========================================

compress_backup() {
    log_info "压缩备份文件..."
    
    local backup_name="website_monitor_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
    local backup_path="$BACKUP_BASE_DIR/$backup_name"
    
    if tar -czf "$backup_path" -C "$BACKUP_BASE_DIR" "$(basename "$BACKUP_DIR")" 2>/dev/null; then
        log_success "备份压缩完成: $backup_path"
        
        # 删除未压缩的备份目录
        rm -rf "$BACKUP_DIR"
        
        # 显示备份文件大小
        local backup_size
        backup_size=$(du -h "$backup_path" | cut -f1)
        log_info "备份文件大小: $backup_size"
        
        echo "$backup_path"
        return 0
    else
        log_error "备份压缩失败"
        return 1
    fi
}

# ===========================================
# 清理旧备份
# ===========================================

cleanup_old_backups() {
    log_info "清理旧备份文件..."
    
    # 查找并删除超过保留数量的备份文件
    local backup_files
    backup_files=$(find "$BACKUP_BASE_DIR" -name "website_monitor_backup_*.tar.gz" -type f | sort -r)
    
    local count=0
    while IFS= read -r backup_file; do
        count=$((count + 1))
        if [[ $count -gt $KEEP_BACKUPS ]]; then
            log_info "删除旧备份: $(basename "$backup_file")"
            rm -f "$backup_file"
        fi
    done <<< "$backup_files"
    
    log_success "旧备份清理完成，保留最近 $KEEP_BACKUPS 个备份"
}

# ===========================================
# 生成备份报告
# ===========================================

generate_backup_report() {
    local backup_file="$1"
    local report_file="$BACKUP_BASE_DIR/backup_report_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "网址监控系统备份报告"
        echo "生成时间: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "========================================"
        echo ""
        
        echo "备份文件: $backup_file"
        echo "备份大小: $(du -h "$backup_file" 2>/dev/null | cut -f1 || echo "未知")"
        echo ""
        
        echo "备份内容:"
        echo "- 数据库备份 (MySQL/SQLite)"
        echo "- 应用文件 (uploads, downloads, user_files)"
        echo "- 配置文件 (Docker, Nginx, 环境变量)"
        echo "- 日志文件 (应用日志, 系统日志)"
        echo ""
        
        echo "系统信息:"
        echo "- 服务器时间: $(date)"
        echo "- 磁盘使用: $(df -h . | tail -1 | awk '{print $5}')"
        echo "- 内存使用: $(free -m | awk 'NR==2{printf "%.2f%%", $3*100/$2}')"
        echo ""
        
        echo "Docker状态:"
        docker-compose -f "$COMPOSE_FILE" ps 2>/dev/null || echo "无法获取Docker状态"
        
    } > "$report_file"
    
    log_info "备份报告已生成: $report_file"
}

# ===========================================
# 主备份函数
# ===========================================

run_backup() {
    local backup_file
    
    show_banner
    detect_environment || return 1
    create_backup_directory
    
    # 执行各项备份
    backup_database || log_warning "数据库备份部分失败"
    backup_files
    backup_configuration
    backup_logs
    
    # 压缩备份
    backup_file=$(compress_backup)
    if [[ $? -eq 0 ]]; then
        generate_backup_report "$backup_file"
        cleanup_old_backups
        
        echo ""
        log_success "🎉 备份完成！"
        echo "备份文件: $backup_file"
        echo "备份大小: $(du -h "$backup_file" 2>/dev/null | cut -f1 || echo "未知")"
        
        return 0
    else
        log_error "备份失败"
        return 1
    fi
}

# ===========================================
# 恢复备份
# ===========================================

restore_backup() {
    local backup_file="$1"
    
    if [[ -z "$backup_file" ]] || [[ ! -f "$backup_file" ]]; then
        log_error "请指定有效的备份文件"
        echo "用法: $0 restore <backup_file.tar.gz>"
        return 1
    fi
    
    log_info "开始恢复备份: $backup_file"
    
    # 创建临时恢复目录
    local restore_dir="/tmp/restore_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$restore_dir"
    
    # 解压备份文件
    if tar -xzf "$backup_file" -C "$restore_dir"; then
        log_success "备份文件解压完成"
        
        # 这里可以添加具体的恢复逻辑
        log_warning "恢复功能需要手动执行，请查看解压后的文件: $restore_dir"
        
        return 0
    else
        log_error "备份文件解压失败"
        return 1
    fi
}

# ===========================================
# 主函数
# ===========================================

main() {
    case "${1:-backup}" in
        "backup")
            run_backup
            ;;
        "restore")
            restore_backup "$2"
            ;;
        "list")
            echo "可用的备份文件:"
            find "$BACKUP_BASE_DIR" -name "website_monitor_backup_*.tar.gz" -type f | sort -r | head -10
            ;;
        "cleanup")
            cleanup_old_backups
            ;;
        *)
            echo "用法: $0 [backup|restore|list|cleanup]"
            echo "  backup           - 创建备份 (默认)"
            echo "  restore <file>   - 恢复备份"
            echo "  list             - 列出备份文件"
            echo "  cleanup          - 清理旧备份"
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
