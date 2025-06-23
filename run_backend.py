#!/usr/bin/env python3
"""
启动后端服务器
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.app import app

if __name__ == '__main__':
    print("启动网址监控工具后端服务...")
    print("服务地址: http://localhost:5001")
    print("API文档: http://localhost:5001/api")
    print("按 Ctrl+C 停止服务")
    app.run(host='0.0.0.0', port=5001, debug=False) 