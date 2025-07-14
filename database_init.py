#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
确保数据库结构正确，适用于生产环境
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def wait_for_database(database_url, max_retries=30, retry_delay=2):
    """等待数据库连接就绪"""
    logger.info("等待数据库连接...")
    
    for attempt in range(max_retries):
        try:
            engine = create_engine(database_url)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("数据库连接成功！")
            return True
        except Exception as e:
            logger.warning(f"数据库连接失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                logger.error("数据库连接超时，请检查数据库服务是否正常运行")
                return False
    
    return False

def create_tables(database_url):
    """创建数据库表结构"""
    logger.info("开始创建数据库表结构...")
    
    engine = create_engine(database_url)
    
    # 创建表的SQL语句
    create_tables_sql = [
        # 1. 用户表
        """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(80) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(20) DEFAULT 'user',
            status VARCHAR(20) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            last_login_at TIMESTAMP NULL,
            INDEX idx_username (username),
            INDEX idx_email (email),
            INDEX idx_role (role),
            INDEX idx_status (status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        
        # 2. 网站分组表
        """
        CREATE TABLE IF NOT EXISTS website_groups (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            description TEXT,
            color VARCHAR(20) DEFAULT '#409EFF',
            is_default BOOLEAN DEFAULT FALSE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_group_name (name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        
        # 3. 网站表
        """
        CREATE TABLE IF NOT EXISTS websites (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            url TEXT NOT NULL,
            domain VARCHAR(255) NOT NULL DEFAULT '',
            original_url TEXT NOT NULL,
            normalized_url TEXT,
            description TEXT,
            group_id INT,
            is_active BOOLEAN DEFAULT TRUE NOT NULL,
            check_interval INT DEFAULT 300,
            timeout INT DEFAULT 30,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_name (name),
            INDEX idx_domain (domain),
            INDEX idx_is_active (is_active),
            INDEX idx_group_id (group_id),
            INDEX idx_created_at (created_at),
            FOREIGN KEY (group_id) REFERENCES website_groups(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        
        # 4. 检测任务表
        """
        CREATE TABLE IF NOT EXISTS detection_tasks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            interval_hours DECIMAL(4,2) DEFAULT 0.5,
            max_concurrent INT DEFAULT 10,
            timeout_seconds INT DEFAULT 30,
            retry_times INT DEFAULT 3,
            is_active BOOLEAN DEFAULT TRUE NOT NULL,
            is_running BOOLEAN DEFAULT FALSE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            last_run_at TIMESTAMP NULL,
            next_run_at TIMESTAMP NULL,
            total_runs INT DEFAULT 0,
            success_runs INT DEFAULT 0,
            failed_runs INT DEFAULT 0,
            INDEX idx_name (name),
            INDEX idx_is_active (is_active),
            INDEX idx_is_running (is_running),
            INDEX idx_next_run_at (next_run_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        
        # 5. 任务-网站关联表
        """
        CREATE TABLE IF NOT EXISTS task_websites (
            task_id INT NOT NULL,
            website_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (task_id, website_id),
            FOREIGN KEY (task_id) REFERENCES detection_tasks(id) ON DELETE CASCADE,
            FOREIGN KEY (website_id) REFERENCES websites(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        
        # 6. 检测记录表
        """
        CREATE TABLE IF NOT EXISTS detection_records (
            id INT AUTO_INCREMENT PRIMARY KEY,
            task_id INT NOT NULL,
            website_id INT NOT NULL,
            status VARCHAR(20) NOT NULL,
            response_time INT,
            http_status_code INT,
            final_url TEXT,
            error_message TEXT,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_task_id (task_id),
            INDEX idx_website_id (website_id),
            INDEX idx_status (status),
            INDEX idx_detected_at (detected_at),
            INDEX idx_task_website_time (task_id, website_id, detected_at),
            FOREIGN KEY (task_id) REFERENCES detection_tasks(id) ON DELETE CASCADE,
            FOREIGN KEY (website_id) REFERENCES websites(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        
        # 7. 网站状态变化记录表
        """
        CREATE TABLE IF NOT EXISTS website_status_changes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            website_id INT NOT NULL,
            task_id INT,
            previous_status VARCHAR(20),
            current_status VARCHAR(20) NOT NULL,
            change_type VARCHAR(20) NOT NULL,
            previous_detection_id INT,
            current_detection_id INT,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_website_id (website_id),
            INDEX idx_task_id (task_id),
            INDEX idx_current_status (current_status),
            INDEX idx_change_type (change_type),
            INDEX idx_detected_at (detected_at),
            INDEX idx_website_time (website_id, detected_at),
            FOREIGN KEY (website_id) REFERENCES websites(id) ON DELETE CASCADE,
            FOREIGN KEY (task_id) REFERENCES detection_tasks(id) ON DELETE SET NULL,
            FOREIGN KEY (previous_detection_id) REFERENCES detection_records(id) ON DELETE SET NULL,
            FOREIGN KEY (current_detection_id) REFERENCES detection_records(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        
        # 8. 失败网站监控任务表
        """
        CREATE TABLE IF NOT EXISTS failed_site_monitor_tasks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            parent_task_id INT NOT NULL,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            interval_minutes INT DEFAULT 5,
            max_concurrent INT DEFAULT 5,
            timeout_seconds INT DEFAULT 15,
            retry_times INT DEFAULT 2,
            is_active BOOLEAN DEFAULT TRUE NOT NULL,
            is_running BOOLEAN DEFAULT FALSE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            last_run_at TIMESTAMP NULL,
            next_run_at TIMESTAMP NULL,
            total_runs INT DEFAULT 0,
            success_runs INT DEFAULT 0,
            failed_runs INT DEFAULT 0,
            INDEX idx_parent_task_id (parent_task_id),
            INDEX idx_is_active (is_active),
            INDEX idx_is_running (is_running),
            INDEX idx_next_run_at (next_run_at),
            FOREIGN KEY (parent_task_id) REFERENCES detection_tasks(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        
        # 9. 失败网站监控任务-网站关联表
        """
        CREATE TABLE IF NOT EXISTS failed_monitor_websites (
            failed_task_id INT NOT NULL,
            website_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (failed_task_id, website_id),
            FOREIGN KEY (failed_task_id) REFERENCES failed_site_monitor_tasks(id) ON DELETE CASCADE,
            FOREIGN KEY (website_id) REFERENCES websites(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    ]
    
    try:
        with engine.connect() as conn:
            # 创建表
            for i, sql in enumerate(create_tables_sql, 1):
                logger.info(f"创建表 {i}/{len(create_tables_sql)}...")
                conn.execute(text(sql))
                conn.commit()
            
            logger.info("数据库表结构创建完成！")
            return True
            
    except SQLAlchemyError as e:
        logger.error(f"创建表结构失败: {e}")
        return False

def create_default_data(database_url):
    """创建默认数据"""
    logger.info("创建默认数据...")
    
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            # 1. 创建默认管理员用户
            from werkzeug.security import generate_password_hash
            password_hash = generate_password_hash('admin123')
            
            conn.execute(text("""
                INSERT IGNORE INTO users (username, email, password_hash, role, status)
                VALUES ('admin', 'admin@example.com', :password_hash, 'admin', 'active')
            """), {'password_hash': password_hash})
            
            # 2. 创建默认分组
            conn.execute(text("""
                INSERT IGNORE INTO website_groups (name, description, color, is_default)
                VALUES ('默认分组', '系统默认分组', '#409EFF', TRUE)
            """))
            
            conn.commit()
            logger.info("默认数据创建完成！")
            return True
            
    except SQLAlchemyError as e:
        logger.error(f"创建默认数据失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("开始数据库初始化...")
    
    # 从环境变量获取数据库URL
    database_url = os.getenv('DATABASE_URL', 'mysql://webmonitor:webmonitor123@mysql:3306/website_monitor')
    
    # 等待数据库就绪
    if not wait_for_database(database_url):
        logger.error("数据库连接失败，退出")
        sys.exit(1)
    
    # 创建表结构
    if not create_tables(database_url):
        logger.error("创建表结构失败，退出")
        sys.exit(1)
    
    # 创建默认数据
    if not create_default_data(database_url):
        logger.error("创建默认数据失败，退出")
        sys.exit(1)
    
    logger.info("数据库初始化完成！")
    logger.info("默认登录信息: admin / admin123")

if __name__ == "__main__":
    main()