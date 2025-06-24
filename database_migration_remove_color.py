#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：移除WebsiteGroup表的color字段
执行此脚本将从website_groups表中删除color列
"""

import os
import sys
import sqlite3
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def backup_database(db_path):
    """备份数据库"""
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"数据库已备份到: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"备份数据库失败: {e}")
        return None

def migrate_database():
    """执行数据库迁移"""
    db_path = os.path.join('database', 'website_monitor.db')
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False
    
    # 备份数据库
    backup_path = backup_database(db_path)
    if not backup_path:
        print("无法备份数据库，迁移终止")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查color列是否存在
        cursor.execute("PRAGMA table_info(website_groups)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'color' not in columns:
            print("color列不存在，无需迁移")
            conn.close()
            return True
        
        print("开始移除color列...")
        
        # SQLite不支持直接删除列，需要重建表
        # 1. 创建新表（不包含color列）
        cursor.execute('''
            CREATE TABLE website_groups_new (
                id INTEGER PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                description TEXT,
                is_default BOOLEAN NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
        ''')
        
        # 2. 复制数据（排除color列）
        cursor.execute('''
            INSERT INTO website_groups_new (id, name, description, is_default, created_at, updated_at)
            SELECT id, name, description, is_default, created_at, updated_at
            FROM website_groups
        ''')
        
        # 3. 删除原表
        cursor.execute('DROP TABLE website_groups')
        
        # 4. 重命名新表
        cursor.execute('ALTER TABLE website_groups_new RENAME TO website_groups')
        
        # 5. 重建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_website_groups_name ON website_groups(name)')
        
        # 提交事务
        conn.commit()
        print("✅ 成功移除color列")
        
        # 验证迁移结果
        cursor.execute("PRAGMA table_info(website_groups)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"迁移后的列: {', '.join(columns)}")
        
        # 检查数据完整性
        cursor.execute("SELECT COUNT(*) FROM website_groups")
        count = cursor.fetchone()[0]
        print(f"迁移后记录数: {count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        
        # 尝试恢复备份
        if backup_path and os.path.exists(backup_path):
            try:
                import shutil
                shutil.copy2(backup_path, db_path)
                print(f"已从备份恢复数据库: {backup_path}")
            except Exception as restore_error:
                print(f"恢复备份失败: {restore_error}")
        
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("数据库迁移：移除WebsiteGroup.color字段")
    print("=" * 50)
    
    # 确认执行
    confirm = input("确定要移除color字段吗？这将删除所有分组的颜色信息。(y/N): ")
    if confirm.lower() != 'y':
        print("迁移取消")
        return
    
    success = migrate_database()
    
    if success:
        print("\n✅ 迁移完成！分组管理不再支持颜色功能。")
    else:
        print("\n❌ 迁移失败！请检查错误信息。")

if __name__ == '__main__':
    main()