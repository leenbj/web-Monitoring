#!/usr/bin/env python3
"""
网址监控系统数据迁移工具
SQLite -> MySQL 数据迁移，适用于宝塔面板部署
"""

import os
import sys
import sqlite3
import pymysql
from datetime import datetime
import json
import traceback

# MySQL连接配置（从环境变量或命令行参数获取）
MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'monitor_user'),
    'password': os.getenv('MYSQL_PASSWORD', 'BaotaUser2024!'),
    'database': os.getenv('MYSQL_DATABASE', 'website_monitor'),
    'charset': 'utf8mb4'
}

# SQLite数据库路径
SQLITE_DB_PATH = os.getenv('SQLITE_DB_PATH', './database/website_monitor.db')

def check_sqlite_db():
    """检查SQLite数据库是否存在"""
    if not os.path.exists(SQLITE_DB_PATH):
        print(f"错误: SQLite数据库文件不存在: {SQLITE_DB_PATH}")
        return False
    
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        conn.close()
        
        print(f"SQLite数据库检查通过，发现 {len(tables)} 个表")
        return True
    except Exception as e:
        print(f"SQLite数据库检查失败: {e}")
        return False

def check_mysql_connection():
    """检查MySQL连接"""
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        conn.close()
        
        print(f"MySQL连接成功，版本: {version[0]}")
        return True
    except Exception as e:
        print(f"MySQL连接失败: {e}")
        return False

def create_mysql_tables():
    """创建MySQL表结构"""
    sql_statements = [
        # 网站分组表
        """
        CREATE TABLE IF NOT EXISTS website_groups (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            description TEXT,
            is_default BOOLEAN NOT NULL DEFAULT FALSE,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_group_name (name),
            INDEX idx_group_created (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='网站分组表';
        """,
        
        # 网站表
        """
        CREATE TABLE IF NOT EXISTS websites (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            url TEXT NOT NULL,
            domain VARCHAR(255) NOT NULL,
            original_url TEXT NOT NULL,
            normalized_url TEXT,
            description TEXT,
            group_id INT,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES website_groups(id),
            INDEX idx_website_name (name),
            INDEX idx_website_domain (domain),
            INDEX idx_website_active (is_active),
            INDEX idx_website_group (group_id),
            INDEX idx_website_created (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='监控网站表';
        """,
        
        # 检测任务表
        """
        CREATE TABLE IF NOT EXISTS detection_tasks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            interval_hours INT NOT NULL DEFAULT 6,
            max_concurrent INT DEFAULT 10,
            timeout_seconds INT DEFAULT 30,
            retry_times INT DEFAULT 3,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            is_running BOOLEAN NOT NULL DEFAULT FALSE,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            last_run_at DATETIME,
            next_run_at DATETIME,
            total_runs INT DEFAULT 0,
            success_runs INT DEFAULT 0,
            failed_runs INT DEFAULT 0,
            INDEX idx_task_active (is_active),
            INDEX idx_task_running (is_running),
            INDEX idx_task_created (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='检测任务表';
        """,
        
        # 检测记录表
        """
        CREATE TABLE IF NOT EXISTS detection_records (
            id INT AUTO_INCREMENT PRIMARY KEY,
            website_id INT NOT NULL,
            task_id INT,
            status VARCHAR(20) NOT NULL,
            final_url TEXT,
            response_time FLOAT,
            http_status_code INT,
            error_message TEXT,
            failure_reason VARCHAR(50),
            ssl_info JSON,
            redirect_chain JSON,
            page_title TEXT,
            page_content_length INT,
            detected_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            retry_count INT DEFAULT 0,
            detection_duration FLOAT,
            FOREIGN KEY (website_id) REFERENCES websites(id) ON DELETE CASCADE,
            FOREIGN KEY (task_id) REFERENCES detection_tasks(id),
            INDEX idx_record_website_time (website_id, detected_at),
            INDEX idx_record_status_time (status, detected_at),
            INDEX idx_record_task_time (task_id, detected_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='检测记录表';
        """,
        
        # 用户表
        """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            password_hash VARCHAR(128) NOT NULL,
            email VARCHAR(100) NOT NULL UNIQUE,
            real_name VARCHAR(100) NOT NULL,
            role VARCHAR(20) NOT NULL DEFAULT 'user',
            status VARCHAR(20) NOT NULL DEFAULT 'active',
            last_login_at DATETIME,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_user_username (username),
            INDEX idx_user_email (email),
            INDEX idx_user_status (status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';
        """,
        
        # 任务-网站关联表
        """
        CREATE TABLE IF NOT EXISTS task_websites (
            task_id INT NOT NULL,
            website_id INT NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (task_id, website_id),
            FOREIGN KEY (task_id) REFERENCES detection_tasks(id) ON DELETE CASCADE,
            FOREIGN KEY (website_id) REFERENCES websites(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='任务网站关联表';
        """,
        
        # 系统设置表
        """
        CREATE TABLE IF NOT EXISTS system_settings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            `key` VARCHAR(100) NOT NULL UNIQUE,
            `value` TEXT,
            description TEXT,
            category VARCHAR(50),
            data_type VARCHAR(20) DEFAULT 'string',
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_setting_key (`key`),
            INDEX idx_setting_category (category)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统设置表';
        """
    ]
    
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        
        for sql in sql_statements:
            cursor.execute(sql)
        
        conn.commit()
        conn.close()
        print("MySQL表结构创建成功")
        return True
    except Exception as e:
        print(f"创建MySQL表结构失败: {e}")
        return False

def migrate_data():
    """迁移数据"""
    try:
        # 连接SQLite
        sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
        sqlite_conn.row_factory = sqlite3.Row
        
        # 连接MySQL
        mysql_conn = pymysql.connect(**MYSQL_CONFIG)
        mysql_cursor = mysql_conn.cursor()
        
        # 迁移网站分组
        print("迁移网站分组数据...")
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute("SELECT * FROM website_groups")
        groups = sqlite_cursor.fetchall()
        
        for group in groups:
            mysql_cursor.execute("""
                INSERT INTO website_groups (id, name, description, is_default, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                name = VALUES(name),
                description = VALUES(description),
                is_default = VALUES(is_default)
            """, (group['id'], group['name'], group['description'], 
                 group['is_default'], group['created_at'], group['updated_at']))
        
        print(f"迁移了 {len(groups)} 个网站分组")
        
        # 迁移网站
        print("迁移网站数据...")
        sqlite_cursor.execute("SELECT * FROM websites")
        websites = sqlite_cursor.fetchall()
        
        for website in websites:
            mysql_cursor.execute("""
                INSERT INTO websites (id, name, url, domain, original_url, normalized_url,
                                    description, group_id, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                name = VALUES(name),
                url = VALUES(url),
                domain = VALUES(domain)
            """, (website['id'], website['name'], website['url'], website['domain'],
                 website['original_url'], website['normalized_url'], website['description'],
                 website['group_id'], website['is_active'], website['created_at'], website['updated_at']))
        
        print(f"迁移了 {len(websites)} 个网站")
        
        # 迁移用户
        print("迁移用户数据...")
        sqlite_cursor.execute("SELECT * FROM users")
        users = sqlite_cursor.fetchall()
        
        for user in users:
            mysql_cursor.execute("""
                INSERT INTO users (id, username, password_hash, email, real_name, role, status,
                                 last_login_at, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                password_hash = VALUES(password_hash),
                email = VALUES(email),
                real_name = VALUES(real_name),
                role = VALUES(role),
                status = VALUES(status)
            """, (user['id'], user['username'], user['password_hash'], user['email'],
                 user['real_name'], user['role'], user['status'], user['last_login_at'],
                 user['created_at'], user['updated_at']))
        
        print(f"迁移了 {len(users)} 个用户")
        
        # 迁移检测任务
        print("迁移检测任务数据...")
        sqlite_cursor.execute("SELECT * FROM detection_tasks")
        tasks = sqlite_cursor.fetchall()
        
        for task in tasks:
            mysql_cursor.execute("""
                INSERT INTO detection_tasks (id, name, description, interval_hours, max_concurrent,
                                           timeout_seconds, retry_times, is_active, is_running,
                                           created_at, updated_at, last_run_at, next_run_at,
                                           total_runs, success_runs, failed_runs)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                name = VALUES(name),
                description = VALUES(description),
                interval_hours = VALUES(interval_hours)
            """, (task['id'], task['name'], task['description'], task['interval_hours'],
                 task['max_concurrent'], task['timeout_seconds'], task['retry_times'],
                 task['is_active'], task['is_running'], task['created_at'], task['updated_at'],
                 task['last_run_at'], task['next_run_at'], task['total_runs'],
                 task['success_runs'], task['failed_runs']))
        
        print(f"迁移了 {len(tasks)} 个检测任务")
        
        # 迁移任务-网站关联
        print("迁移任务网站关联数据...")
        sqlite_cursor.execute("SELECT * FROM task_websites")
        task_websites = sqlite_cursor.fetchall()
        
        for tw in task_websites:
            mysql_cursor.execute("""
                INSERT INTO task_websites (task_id, website_id, created_at)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE created_at = VALUES(created_at)
            """, (tw['task_id'], tw['website_id'], tw['created_at']))
        
        print(f"迁移了 {len(task_websites)} 条任务网站关联")
        
        # 迁移检测记录（仅最近的记录，避免数据过大）
        print("迁移最近30天的检测记录...")
        sqlite_cursor.execute("""
            SELECT * FROM detection_records 
            WHERE detected_at >= datetime('now', '-30 days')
            ORDER BY detected_at DESC
        """)
        records = sqlite_cursor.fetchall()
        
        batch_size = 1000
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            values = []
            for record in batch:
                values.append((
                    record['website_id'], record['task_id'], record['status'],
                    record['final_url'], record['response_time'], record['http_status_code'],
                    record['error_message'], record['failure_reason'], record['ssl_info'],
                    record['redirect_chain'], record['page_title'], record['page_content_length'],
                    record['detected_at'], record['retry_count'], record['detection_duration']
                ))
            
            if values:
                mysql_cursor.executemany("""
                    INSERT INTO detection_records (website_id, task_id, status, final_url,
                                                 response_time, http_status_code, error_message,
                                                 failure_reason, ssl_info, redirect_chain,
                                                 page_title, page_content_length, detected_at,
                                                 retry_count, detection_duration)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, values)
            
            print(f"已迁移 {min(i + batch_size, len(records))}/{len(records)} 条检测记录")
        
        # 提交事务
        mysql_conn.commit()
        
        # 关闭连接
        sqlite_conn.close()
        mysql_conn.close()
        
        print("数据迁移完成!")
        return True
        
    except Exception as e:
        print(f"数据迁移失败: {e}")
        traceback.print_exc()
        return False

def create_default_admin():
    """创建默认管理员账号"""
    try:
        from werkzeug.security import generate_password_hash
        
        conn = pymysql.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        
        # 检查是否已存在admin用户
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        if cursor.fetchone():
            print("默认管理员账号已存在")
            conn.close()
            return True
        
        # 创建默认管理员
        password_hash = generate_password_hash('admin123')
        cursor.execute("""
            INSERT INTO users (username, password_hash, email, real_name, role, status)
            VALUES ('admin', %s, 'admin@example.com', '系统管理员', 'admin', 'active')
        """, (password_hash,))
        
        conn.commit()
        conn.close()
        
        print("默认管理员账号创建成功 (admin/admin123)")
        return True
        
    except Exception as e:
        print(f"创建默认管理员失败: {e}")
        return False

def main():
    """主函数"""
    print("=== 网址监控系统数据迁移工具 ===")
    print(f"迁移时间: {datetime.now()}")
    print(f"SQLite数据库: {SQLITE_DB_PATH}")
    print(f"MySQL数据库: {MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}/{MYSQL_CONFIG['database']}")
    print()
    
    # 检查SQLite数据库
    if not check_sqlite_db():
        sys.exit(1)
    
    # 检查MySQL连接
    if not check_mysql_connection():
        sys.exit(1)
    
    # 询问是否继续
    confirm = input("确认开始数据迁移? (y/N): ")
    if confirm.lower() != 'y':
        print("迁移已取消")
        sys.exit(0)
    
    # 创建MySQL表结构
    if not create_mysql_tables():
        sys.exit(1)
    
    # 迁移数据
    if not migrate_data():
        sys.exit(1)
    
    # 创建默认管理员（如果不存在）
    create_default_admin()
    
    print("\n=== 迁移完成 ===")
    print("请验证数据完整性后，配置后端服务连接MySQL数据库")

if __name__ == "__main__":
    main()