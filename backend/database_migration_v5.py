#!/usr/bin/env python3
"""
数据库迁移脚本 v5
添加网站分组功能
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    """执行数据库迁移"""
    db_path = '../database/website_monitor.db'
    
    if not os.path.exists(db_path):
        print("数据库文件不存在，跳过迁移")
        return
    
    print("开始数据库迁移 v5...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 创建网站分组表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS website_groups (
                id INTEGER PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                description TEXT,
                color VARCHAR(7) DEFAULT '#409EFF',
                is_default BOOLEAN DEFAULT 0 NOT NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
        """)
        print("创建 website_groups 表")
        
        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_website_groups_name 
            ON website_groups(name)
        """)
        
        # 检查网站表是否已有group_id字段
        cursor.execute("PRAGMA table_info(websites)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'group_id' not in columns:
            print("添加 group_id 字段到 websites 表...")
            cursor.execute("""
                ALTER TABLE websites 
                ADD COLUMN group_id INTEGER
            """)
            
            # 创建外键索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_websites_group_id 
                ON websites(group_id)
            """)
            print("group_id 字段添加成功")
        else:
            print("group_id 字段已存在，跳过")
        
        # 创建默认分组
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 检查是否已存在默认分组
        cursor.execute("SELECT id FROM website_groups WHERE is_default = 1")
        default_group = cursor.fetchone()
        
        if not default_group:
            cursor.execute("""
                INSERT INTO website_groups (name, description, color, is_default, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ('默认分组', '系统默认网站分组', '#409EFF', 1, current_time, current_time))
            
            default_group_id = cursor.lastrowid
            print(f"创建默认分组，ID: {default_group_id}")
            
            # 将现有网站分配给默认分组
            cursor.execute("""
                UPDATE websites 
                SET group_id = ? 
                WHERE group_id IS NULL
            """, (default_group_id,))
            
            updated_count = cursor.rowcount
            print(f"将 {updated_count} 个网站分配给默认分组")
        else:
            print("默认分组已存在，跳过创建")
        
        # 创建一些示例分组
        sample_groups = [
            ('政府网站', '政府机构官方网站', '#F56C6C'),
            ('企业网站', '企业官方网站', '#67C23A'),
            ('教育网站', '教育机构网站', '#E6A23C'),
            ('媒体网站', '新闻媒体网站', '#909399')
        ]
        
        for group_name, group_desc, group_color in sample_groups:
            cursor.execute("SELECT id FROM website_groups WHERE name = ?", (group_name,))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO website_groups (name, description, color, is_default, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (group_name, group_desc, group_color, 0, current_time, current_time))
                print(f"创建示例分组: {group_name}")
        
        conn.commit()
        print("数据库迁移 v5 完成！")
        
    except Exception as e:
        print(f"迁移失败: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database() 