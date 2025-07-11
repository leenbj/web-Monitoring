#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网址监控系统后端启动脚本
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# 导入应用
from backend.app import create_app

if __name__ == '__main__':
    # 创建应用实例
    app = create_app()
    
    # 启动应用
    port = int(os.environ.get('PORT', 5000))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,
        threaded=True
    ) 