#!/usr/bin/env python3
"""
数据库架构更新脚本
更新数据库以支持小时间隔和状态变化监控功能
"""

import sys
import os
import logging
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.database import get_db
from backend.models import db
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def update_detection_tasks_table():
    """更新检测任务表：将interval_minutes改为interval_hours"""
    try:
        with get_db() as database:
            # 检查是否已有interval_hours列
            result = database.execute(text("PRAGMA table_info(detection_tasks)")).fetchall()
            columns = [row[1] for row in result]
            
            if 'interval_hours' not in columns and 'interval_minutes' in columns:
                logger.info("开始更新detection_tasks表结构...")
                
                # 1. 添加新的interval_hours列，默认值为6小时
                database.execute(text("ALTER TABLE detection_tasks ADD COLUMN interval_hours INTEGER DEFAULT 6"))
                
                # 2. 将现有的interval_minutes转换为interval_hours（保留原有逻辑但换算单位）
                database.execute(text("""
                    UPDATE detection_tasks 
                    SET interval_hours = CASE 
                        WHEN interval_minutes <= 60 THEN 1
                        WHEN interval_minutes <= 360 THEN 6
                        WHEN interval_minutes <= 720 THEN 12
                        ELSE 24
                    END
                """))
                
                database.commit()
                logger.info("✅ detection_tasks表更新完成：添加interval_hours列")
            else:
                logger.info("detection_tasks表已包含interval_hours列，跳过更新")
                
    except Exception as e:
        logger.error(f"❌ 更新detection_tasks表失败: {e}")
        raise


def create_status_change_table():
    """创建网站状态变化记录表"""
    try:
        with get_db() as database:
            # 检查表是否已存在
            result = database.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='website_status_changes'"
            )).fetchone()
            
            if not result:
                logger.info("开始创建website_status_changes表...")
                
                database.execute(text("""
                    CREATE TABLE website_status_changes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        website_id INTEGER NOT NULL,
                        task_id INTEGER,
                        previous_status VARCHAR(20),
                        current_status VARCHAR(20) NOT NULL,
                        change_type VARCHAR(20) NOT NULL,
                        previous_detection_id INTEGER,
                        current_detection_id INTEGER,
                        detected_at DATETIME NOT NULL,
                        FOREIGN KEY (website_id) REFERENCES websites (id),
                        FOREIGN KEY (task_id) REFERENCES detection_tasks (id),
                        FOREIGN KEY (previous_detection_id) REFERENCES detection_records (id),
                        FOREIGN KEY (current_detection_id) REFERENCES detection_records (id)
                    )
                """))
                
                # 创建索引
                database.execute(text(
                    "CREATE INDEX idx_status_changes_website_time ON website_status_changes(website_id, detected_at)"
                ))
                database.execute(text(
                    "CREATE INDEX idx_status_changes_task_time ON website_status_changes(task_id, detected_at)"
                ))
                database.execute(text(
                    "CREATE INDEX idx_status_changes_type ON website_status_changes(change_type)"
                ))
                
                database.commit()
                logger.info("✅ website_status_changes表创建完成")
            else:
                logger.info("website_status_changes表已存在，跳过创建")
                
    except Exception as e:
        logger.error(f"❌ 创建website_status_changes表失败: {e}")
        raise


def create_failed_monitor_table():
    """创建失败网站监控任务表"""
    try:
        with get_db() as database:
            # 检查表是否已存在
            result = database.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='failed_site_monitor_tasks'"
            )).fetchone()
            
            if not result:
                logger.info("开始创建failed_site_monitor_tasks表...")
                
                database.execute(text("""
                    CREATE TABLE failed_site_monitor_tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name VARCHAR(255) NOT NULL,
                        description TEXT,
                        parent_task_id INTEGER NOT NULL,
                        interval_hours INTEGER NOT NULL DEFAULT 1,
                        max_concurrent INTEGER DEFAULT 10,
                        timeout_seconds INTEGER DEFAULT 30,
                        retry_times INTEGER DEFAULT 3,
                        is_active BOOLEAN DEFAULT 1,
                        is_running BOOLEAN DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        last_run_at DATETIME,
                        next_run_at DATETIME,
                        FOREIGN KEY (parent_task_id) REFERENCES detection_tasks (id)
                    )
                """))
                
                # 创建关联表
                database.execute(text("""
                    CREATE TABLE failed_site_monitor_websites (
                        monitor_task_id INTEGER,
                        website_id INTEGER,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (monitor_task_id, website_id),
                        FOREIGN KEY (monitor_task_id) REFERENCES failed_site_monitor_tasks (id),
                        FOREIGN KEY (website_id) REFERENCES websites (id)
                    )
                """))
                
                database.commit()
                logger.info("✅ failed_site_monitor_tasks表创建完成")
            else:
                logger.info("failed_site_monitor_tasks表已存在，跳过创建")
                
    except Exception as e:
        logger.error(f"❌ 创建failed_site_monitor_tasks表失败: {e}")
        raise


def backup_database():
    """备份数据库"""
    try:
        import shutil
        backup_name = f"database/website_monitor_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2("database/website_monitor.db", backup_name)
        logger.info(f"✅ 数据库备份完成: {backup_name}")
        return backup_name
    except Exception as e:
        logger.error(f"❌ 数据库备份失败: {e}")
        raise


def main():
    """主函数"""
    logger.info("🚀 开始数据库架构更新...")
    
    try:
        # 备份数据库
        backup_file = backup_database()
        
        # 执行更新
        update_detection_tasks_table()
        create_status_change_table()
        create_failed_monitor_table()
        
        logger.info("🎉 数据库架构更新完成！")
        logger.info("新功能:")
        logger.info("  ✅ 支持小时间隔监控（默认6小时）")
        logger.info("  ✅ 网站状态变化跟踪")
        logger.info("  ✅ 失败网站专项监控（1小时间隔）")
        logger.info("  ✅ 跳转状态视为可访问")
        logger.info(f"数据库备份文件: {backup_file}")
        
    except Exception as e:
        logger.error(f"❌ 数据库架构更新失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 