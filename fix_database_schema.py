#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库结构修复脚本
修复 websites 表缺少的字段
"""

import os
import sys
import logging
from urllib.parse import urlparse
import mysql.connector
from mysql.connector import Error

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('fix_database_schema.log')
    ]
)
logger = logging.getLogger(__name__)

def get_domain_from_url(url):
    """从 URL 中提取域名"""
    try:
        parsed = urlparse(url)
        return parsed.netloc
    except Exception as e:
        logger.warning(f"无法解析 URL {url}: {e}")
        return url

def fix_websites_table():
    """修复 websites 表结构"""
    
    # 数据库连接配置
    config = {
        'host': 'localhost',
        'port': 33061,
        'user': 'webmonitor',
        'password': 'webmonitor123',
        'database': 'website_monitor',
        'charset': 'utf8mb4',
        'collation': 'utf8mb4_unicode_ci'
    }
    
    connection = None
    cursor = None
    
    try:
        # 连接数据库
        logger.info("正在连接到数据库...")
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        # 检查表结构
        logger.info("检查当前 websites 表结构...")
        cursor.execute("DESCRIBE websites")
        columns = [col[0] for col in cursor.fetchall()]
        logger.info(f"当前字段: {columns}")
        
        # 需要添加的字段
        fields_to_add = [
            ("domain", "VARCHAR(255) NOT NULL DEFAULT '' COMMENT '中文域名'"),
            ("original_url", "TEXT NOT NULL COMMENT '原始网址'"),
            ("normalized_url", "TEXT NULL COMMENT '标准化网址'"),
            ("description", "TEXT NULL COMMENT '网站描述'"),
            ("group_id", "INT NULL COMMENT '所属分组ID'"),
        ]
        
        # 添加缺失的字段
        for field_name, field_definition in fields_to_add:
            if field_name not in columns:
                logger.info(f"添加字段: {field_name}")
                alter_sql = f"ALTER TABLE websites ADD COLUMN {field_name} {field_definition}"
                cursor.execute(alter_sql)
                logger.info(f"已添加字段: {field_name}")
            else:
                logger.info(f"字段 {field_name} 已存在")
        
        # 更新现有数据
        logger.info("更新现有数据...")
        
        # 获取所有网站记录
        cursor.execute("SELECT id, url FROM websites")
        websites = cursor.fetchall()
        
        for website_id, url in websites:
            try:
                # 提取域名
                domain = get_domain_from_url(url)
                
                # 更新记录
                update_sql = """
                UPDATE websites 
                SET domain = %s, original_url = %s, normalized_url = %s 
                WHERE id = %s
                """
                cursor.execute(update_sql, (domain, url, url, website_id))
                
                logger.info(f"更新网站 {website_id}: {domain}")
                
            except Exception as e:
                logger.error(f"更新网站 {website_id} 失败: {e}")
                continue
        
        # 添加索引
        logger.info("添加索引...")
        
        # 检查是否存在索引
        cursor.execute("SHOW INDEX FROM websites")
        existing_indexes = [idx[2] for idx in cursor.fetchall()]
        
        indexes_to_add = [
            ("idx_website_domain_active", "domain, is_active"),
            ("idx_website_created", "created_at"),
        ]
        
        for index_name, index_columns in indexes_to_add:
            if index_name not in existing_indexes:
                try:
                    index_sql = f"CREATE INDEX {index_name} ON websites ({index_columns})"
                    cursor.execute(index_sql)
                    logger.info(f"已添加索引: {index_name}")
                except Error as e:
                    logger.warning(f"添加索引 {index_name} 失败: {e}")
            else:
                logger.info(f"索引 {index_name} 已存在")
        
        # 提交事务
        connection.commit()
        logger.info("数据库结构修复完成！")
        
        # 验证修复结果
        logger.info("验证修复结果...")
        cursor.execute("DESCRIBE websites")
        final_columns = [col[0] for col in cursor.fetchall()]
        logger.info(f"修复后字段: {final_columns}")
        
        cursor.execute("SELECT COUNT(*) FROM websites")
        count = cursor.fetchone()[0]
        logger.info(f"websites 表共有 {count} 条记录")
        
        return True
        
    except Error as e:
        logger.error(f"数据库操作失败: {e}")
        if connection:
            connection.rollback()
        return False
        
    except Exception as e:
        logger.error(f"修复过程中发生错误: {e}")
        if connection:
            connection.rollback()
        return False
        
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        logger.info("数据库连接已关闭")

def create_website_groups_table():
    """创建 website_groups 表"""
    
    # 数据库连接配置
    config = {
        'host': 'localhost',
        'port': 33061,
        'user': 'webmonitor',
        'password': 'webmonitor123',
        'database': 'website_monitor',
        'charset': 'utf8mb4',
        'collation': 'utf8mb4_unicode_ci'
    }
    
    connection = None
    cursor = None
    
    try:
        # 连接数据库
        logger.info("正在连接到数据库...")
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        # 检查表是否存在
        cursor.execute("SHOW TABLES LIKE 'website_groups'")
        if cursor.fetchone():
            logger.info("website_groups 表已存在")
            return True
        
        # 创建 website_groups 表
        logger.info("创建 website_groups 表...")
        create_table_sql = """
        CREATE TABLE website_groups (
            id INT AUTO_INCREMENT PRIMARY KEY COMMENT '分组ID',
            name VARCHAR(255) NOT NULL UNIQUE COMMENT '分组名称',
            description TEXT COMMENT '分组描述',
            color VARCHAR(20) DEFAULT '#409EFF' COMMENT '分组颜色',
            is_default BOOLEAN DEFAULT FALSE NOT NULL COMMENT '是否默认分组',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
            INDEX idx_group_name (name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        cursor.execute(create_table_sql)
        logger.info("website_groups 表创建成功")
        
        # 创建默认分组
        logger.info("创建默认分组...")
        insert_default_group_sql = """
        INSERT INTO website_groups (name, description, color, is_default)
        VALUES ('默认分组', '系统默认分组', '#409EFF', TRUE)
        """
        cursor.execute(insert_default_group_sql)
        logger.info("默认分组创建成功")
        
        # 提交事务
        connection.commit()
        logger.info("website_groups 表创建完成！")
        
        return True
        
    except Error as e:
        logger.error(f"创建 website_groups 表失败: {e}")
        if connection:
            connection.rollback()
        return False
        
    except Exception as e:
        logger.error(f"创建过程中发生错误: {e}")
        if connection:
            connection.rollback()
        return False
        
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        logger.info("数据库连接已关闭")

def main():
    """主函数"""
    logger.info("开始数据库结构修复...")
    
    # 创建 website_groups 表
    if not create_website_groups_table():
        logger.error("创建 website_groups 表失败，退出")
        sys.exit(1)
    
    # 修复 websites 表
    if not fix_websites_table():
        logger.error("修复 websites 表失败，退出")
        sys.exit(1)
    
    logger.info("数据库结构修复完成！")
    logger.info("现在可以正常使用网址监控系统了")

if __name__ == "__main__":
    main()