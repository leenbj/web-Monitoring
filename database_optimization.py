#!/usr/bin/env python3
"""
数据库优化脚本
添加索引、优化查询性能、修复数据一致性问题
"""

import sys
import os
import logging
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.database import engine, get_db
from backend.models import db
from sqlalchemy import text, Index

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_performance_indexes():
    """创建性能优化索引"""
    logger.info("开始创建性能优化索引...")
    
    indexes_to_create = [
        # DetectionRecord表索引
        "CREATE INDEX IF NOT EXISTS idx_detection_record_compound ON detection_records(website_id, detected_at DESC, status)",
        "CREATE INDEX IF NOT EXISTS idx_detection_record_status_time ON detection_records(status, detected_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_detection_record_task_time ON detection_records(task_id, detected_at DESC)",
        
        # Website表索引
        "CREATE INDEX IF NOT EXISTS idx_website_group_active ON websites(group_id, is_active)",
        "CREATE INDEX IF NOT EXISTS idx_website_domain_active ON websites(domain, is_active)",
        "CREATE INDEX IF NOT EXISTS idx_website_active_created ON websites(is_active, created_at DESC)",
        
        # DetectionTask表索引
        "CREATE INDEX IF NOT EXISTS idx_detection_task_active_next ON detection_tasks(is_active, next_run_at)",
        "CREATE INDEX IF NOT EXISTS idx_detection_task_interval ON detection_tasks(interval_hours, is_active)",
        
        # WebsiteStatusChange表索引
        "CREATE INDEX IF NOT EXISTS idx_status_change_website_time ON website_status_changes(website_id, detected_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_status_change_status_time ON website_status_changes(current_status, detected_at DESC)",
        
        # FailedSiteMonitorTask表索引（如果存在）
        "CREATE INDEX IF NOT EXISTS idx_failed_monitor_active ON failed_site_monitor_tasks(is_active, next_run_at) WHERE EXISTS (SELECT 1 FROM sqlite_master WHERE type='table' AND name='failed_site_monitor_tasks')",
    ]
    
    try:
        with engine.connect() as conn:
            for index_sql in indexes_to_create:
                try:
                    logger.info(f"创建索引: {index_sql[:50]}...")
                    conn.execute(text(index_sql))
                    conn.commit()
                except Exception as e:
                    logger.warning(f"创建索引失败: {e}")
                    
        logger.info("性能索引创建完成")
        
    except Exception as e:
        logger.error(f"创建索引时出错: {e}")


def optimize_sqlite_settings():
    """优化SQLite设置"""
    logger.info("优化SQLite设置...")
    
    optimizations = [
        "PRAGMA journal_mode = WAL",           # WAL模式提高并发
        "PRAGMA synchronous = NORMAL",         # 平衡性能和安全
        "PRAGMA cache_size = -64000",          # 64MB缓存
        "PRAGMA temp_store = memory",          # 临时表在内存中
        "PRAGMA mmap_size = 268435456",        # 256MB内存映射
        "PRAGMA page_size = 4096",             # 4KB页面大小
        "PRAGMA auto_vacuum = INCREMENTAL",    # 增量清理
        "PRAGMA optimize",                     # 优化查询计划
    ]
    
    try:
        with engine.connect() as conn:
            for pragma in optimizations:
                try:
                    logger.info(f"执行优化: {pragma}")
                    conn.execute(text(pragma))
                    conn.commit()
                except Exception as e:
                    logger.warning(f"优化失败: {e}")
                    
        logger.info("SQLite优化完成")
        
    except Exception as e:
        logger.error(f"SQLite优化时出错: {e}")


def analyze_table_stats():
    """分析表统计信息"""
    logger.info("分析表统计信息...")
    
    try:
        with engine.connect() as conn:
            # 获取表信息
            tables_info = conn.execute(text("""
                SELECT name, 
                       (SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND tbl_name=m.name) as index_count
                FROM sqlite_master m 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)).fetchall()
            
            logger.info("数据库表统计:")
            for table_name, index_count in tables_info:
                try:
                    # 获取记录数
                    count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).fetchone()
                    record_count = count_result[0] if count_result else 0
                    
                    logger.info(f"  {table_name}: {record_count} 条记录, {index_count} 个索引")
                    
                except Exception as e:
                    logger.warning(f"获取表 {table_name} 统计信息失败: {e}")
            
            # 执行ANALYZE更新统计信息
            logger.info("更新查询优化器统计信息...")
            conn.execute(text("ANALYZE"))
            conn.commit()
            
    except Exception as e:
        logger.error(f"分析表统计信息时出错: {e}")


def clean_old_data():
    """清理旧数据"""
    logger.info("清理旧数据...")
    
    try:
        with get_db() as db:
            # 删除30天前的检测记录（保留最近的数据）
            thirty_days_ago = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            thirty_days_ago = thirty_days_ago.replace(day=thirty_days_ago.day - 30)
            
            delete_query = text("""
                DELETE FROM detection_records 
                WHERE detected_at < :cutoff_date 
                AND id NOT IN (
                    SELECT id FROM detection_records 
                    WHERE website_id = detection_records.website_id 
                    ORDER BY detected_at DESC 
                    LIMIT 5
                )
            """)
            
            result = db.execute(delete_query, {"cutoff_date": thirty_days_ago})
            deleted_count = result.rowcount
            
            logger.info(f"删除了 {deleted_count} 条旧检测记录")
            
            # 清理孤立的状态变更记录
            orphan_query = text("""
                DELETE FROM website_status_changes 
                WHERE website_id NOT IN (SELECT id FROM websites)
            """)
            
            result = db.execute(orphan_query)
            orphan_count = result.rowcount
            
            logger.info(f"删除了 {orphan_count} 条孤立状态变更记录")
            
    except Exception as e:
        logger.error(f"清理旧数据时出错: {e}")


def vacuum_database():
    """压缩数据库"""
    logger.info("压缩数据库...")
    
    try:
        with engine.connect() as conn:
            # 获取压缩前大小
            before_size = conn.execute(text("PRAGMA page_count")).fetchone()[0]
            page_size = conn.execute(text("PRAGMA page_size")).fetchone()[0]
            before_mb = (before_size * page_size) / (1024 * 1024)
            
            logger.info(f"压缩前数据库大小: {before_mb:.1f} MB")
            
            # 执行压缩
            conn.execute(text("VACUUM"))
            conn.commit()
            
            # 获取压缩后大小
            after_size = conn.execute(text("PRAGMA page_count")).fetchone()[0]
            after_mb = (after_size * page_size) / (1024 * 1024)
            
            saved_mb = before_mb - after_mb
            logger.info(f"压缩后数据库大小: {after_mb:.1f} MB (节省 {saved_mb:.1f} MB)")
            
    except Exception as e:
        logger.error(f"压缩数据库时出错: {e}")


def main():
    """主函数"""
    logger.info("开始数据库优化...")
    logger.info("=" * 50)
    
    try:
        # 1. 分析当前状态
        analyze_table_stats()
        
        # 2. 创建性能索引
        create_performance_indexes()
        
        # 3. 优化SQLite设置
        optimize_sqlite_settings()
        
        # 4. 清理旧数据
        clean_old_data()
        
        # 5. 压缩数据库
        vacuum_database()
        
        # 6. 再次分析统计信息
        analyze_table_stats()
        
        logger.info("=" * 50)
        logger.info("数据库优化完成!")
        
    except Exception as e:
        logger.error(f"数据库优化失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()