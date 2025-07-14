#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
在 Docker 容器内修复数据库结构
"""

import os
import sys
sys.path.insert(0, '/app')

# 设置环境变量
os.environ['DATABASE_URL'] = 'mysql://webmonitor:webmonitor123@mysql:3306/website_monitor'

from backend.app import create_app
from backend.database import get_db
from backend.models import Website, WebsiteGroup
from urllib.parse import urlparse
import logging
from sqlalchemy import text

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
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

def fix_database_schema():
    """修复数据库结构"""
    
    app = create_app()
    
    with app.app_context():
        try:
            with get_db() as db:
                # 1. 修复 websites 表结构
                logger.info("开始修复 websites 表结构...")
                
                # 执行 SQL 命令添加缺失的字段
                missing_fields = [
                    "ALTER TABLE websites ADD COLUMN domain VARCHAR(255) NOT NULL DEFAULT '' COMMENT '中文域名'",
                    "ALTER TABLE websites ADD COLUMN original_url TEXT NOT NULL DEFAULT '' COMMENT '原始网址'",
                    "ALTER TABLE websites ADD COLUMN normalized_url TEXT NULL COMMENT '标准化网址'",
                    "ALTER TABLE websites ADD COLUMN description TEXT NULL COMMENT '网站描述'",
                    "ALTER TABLE websites ADD COLUMN group_id INT NULL COMMENT '所属分组ID'"
                ]
                
                for sql in missing_fields:
                    try:
                        db.execute(text(sql))
                        logger.info(f"执行成功: {sql}")
                    except Exception as e:
                        if "Duplicate column name" in str(e):
                            logger.info(f"字段已存在，跳过: {sql}")
                        else:
                            logger.error(f"执行失败: {sql}, 错误: {e}")
                
                # 2. 创建 website_groups 表
                logger.info("创建 website_groups 表...")
                create_groups_table_sql = """
                CREATE TABLE IF NOT EXISTS website_groups (
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
                
                try:
                    db.execute(text(create_groups_table_sql))
                    logger.info("website_groups 表创建成功")
                except Exception as e:
                    logger.error(f"创建 website_groups 表失败: {e}")
                
                # 3. 创建默认分组
                logger.info("创建默认分组...")
                try:
                    db.execute(text("""
                        INSERT IGNORE INTO website_groups (name, description, color, is_default)
                        VALUES ('默认分组', '系统默认分组', '#409EFF', TRUE)
                    """))
                    logger.info("默认分组创建成功")
                except Exception as e:
                    logger.error(f"创建默认分组失败: {e}")
                
                # 4. 更新现有 websites 数据
                logger.info("更新现有 websites 数据...")
                try:
                    # 获取所有网站记录
                    result = db.execute(text("SELECT id, url FROM websites"))
                    websites = result.fetchall()
                    
                    for website_id, url in websites:
                        try:
                            # 提取域名
                            domain = get_domain_from_url(url)
                            
                            # 更新记录
                            db.execute(text("""
                                UPDATE websites 
                                SET domain = :domain, original_url = :original_url, normalized_url = :normalized_url 
                                WHERE id = :id
                            """), {
                                'domain': domain,
                                'original_url': url,
                                'normalized_url': url,
                                'id': website_id
                            })
                            
                            logger.info(f"更新网站 {website_id}: {domain}")
                            
                        except Exception as e:
                            logger.error(f"更新网站 {website_id} 失败: {e}")
                            continue
                    
                    logger.info("websites 数据更新完成")
                    
                except Exception as e:
                    logger.error(f"更新 websites 数据失败: {e}")
                
                # 5. 添加索引
                logger.info("添加索引...")
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_website_domain_active ON websites (domain, is_active)",
                    "CREATE INDEX IF NOT EXISTS idx_website_created ON websites (created_at)"
                ]
                
                for index_sql in indexes:
                    try:
                        db.execute(text(index_sql))
                        logger.info(f"索引创建成功: {index_sql}")
                    except Exception as e:
                        logger.error(f"创建索引失败: {index_sql}, 错误: {e}")
                
                # 6. 提交事务
                db.commit()
                logger.info("数据库结构修复完成！")
                
                # 7. 验证修复结果
                logger.info("验证修复结果...")
                result = db.execute(text("DESCRIBE websites"))
                columns = [col[0] for col in result.fetchall()]
                logger.info(f"修复后的 websites 表字段: {columns}")
                
                result = db.execute(text("SELECT COUNT(*) FROM websites"))
                count = result.fetchone()[0]
                logger.info(f"websites 表共有 {count} 条记录")
                
                result = db.execute(text("SELECT COUNT(*) FROM website_groups"))
                group_count = result.fetchone()[0]
                logger.info(f"website_groups 表共有 {group_count} 条记录")
                
                return True
                
        except Exception as e:
            logger.error(f"修复过程中发生错误: {e}")
            return False

if __name__ == "__main__":
    if fix_database_schema():
        print("✅ 数据库结构修复成功！")
    else:
        print("❌ 数据库结构修复失败！")
        sys.exit(1)