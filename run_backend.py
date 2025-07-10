#!/usr/bin/env python3
"""
启动后端服务器
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.app import app

if __name__ == '__main__':
    # 从环境变量获取端口，默认5000
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'

    print("启动网址监控工具后端服务...")
    print(f"服务地址: http://localhost:{port}")
    print(f"API文档: http://localhost:{port}/api")
    print("按 Ctrl+C 停止服务")

    app.run(host='0.0.0.0', port=port, debug=debug)