#!/usr/bin/env python3
"""
启动后端服务器
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False) 