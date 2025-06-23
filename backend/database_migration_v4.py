#!/usr/bin/env python3
"""
数据库迁移脚本 v4
添加SSL检测和失败原因分析字段
"""

import sqlite3
import os
import json
from datetime import datetime

def migrate_database():
    """执行数据库迁移"""
    db_path = '../database/website_monitor.db'
    
    if not os.path.exists(db_path):
        print("数据库文件不存在，跳过迁移")
        return
    
    print("开始数据库迁移 v4...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(detection_records)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # 添加 failure_reason 字段
        if 'failure_reason' not in columns:
            print("添加 failure_reason 字段...")
            cursor.execute("""
                ALTER TABLE detection_records 
                ADD COLUMN failure_reason VARCHAR(50)
            """)
            
            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_failure_reason 
                ON detection_records(failure_reason)
            """)
            print("failure_reason 字段添加成功")
        else:
            print("failure_reason 字段已存在，跳过")
        
        # 添加 ssl_info 字段
        if 'ssl_info' not in columns:
            print("添加 ssl_info 字段...")
            cursor.execute("""
                ALTER TABLE detection_records 
                ADD COLUMN ssl_info TEXT
            """)
            print("ssl_info 字段添加成功")
        else:
            print("ssl_info 字段已存在，跳过")
        
        # 根据现有错误信息推断失败原因
        print("更新现有记录的失败原因...")
        cursor.execute("""
            UPDATE detection_records 
            SET failure_reason = CASE 
                WHEN error_message LIKE '%超时%' OR error_message LIKE '%timeout%' THEN 'timeout'
                WHEN error_message LIKE '%SSL%' OR error_message LIKE '%证书%' OR error_message LIKE '%certificate%' THEN 'ssl_error'
                WHEN error_message LIKE '%连接%' OR error_message LIKE '%connection%' THEN 'connection_error'
                WHEN error_message LIKE '%解析%' OR error_message LIKE '%resolution%' THEN 'dns_error'
                WHEN status = 'failed' AND error_message != '' THEN 'request_error'
                ELSE ''
            END
            WHERE failure_reason IS NULL OR failure_reason = ''
        """)
        
        # 为HTTPS网站初始化空的SSL信息
        cursor.execute("""
            UPDATE detection_records 
            SET ssl_info = '{}'
            WHERE ssl_info IS NULL
        """)
        
        conn.commit()
        print("数据库迁移 v4 完成！")
        
    except Exception as e:
        print(f"迁移失败: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database() 