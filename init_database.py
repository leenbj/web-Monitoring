#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def init_database():
    """初始化数据库"""
    try:
        from backend.app import create_app
        from backend.database import init_db
        
        # 创建应用实例
        app = create_app()
        
        with app.app_context():
            # 创建所有数据表
            init_db()
            print("数据库初始化成功")
            
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    init_database() 