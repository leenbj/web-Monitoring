#!/usr/bin/env python3
"""
启动资源优化版本的后端服务器
使用资源优化配置，适合低配置环境
"""

import sys
import os
import gc
import logging
from pathlib import Path

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置环境变量使用优化配置
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_CONFIG'] = 'resource_optimized'

# 优化Python垃圾回收
gc.set_threshold(700, 10, 10)  # 更激进的GC设置

# 配置日志只记录WARNING及以上级别
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/optimized_backend.log'),
        logging.StreamHandler()
    ]
)

# 导入优化配置
from backend.config_resource_optimized import get_optimized_config

# 修改原配置模块
import backend.config as config_module
config_module.config['resource_optimized'] = get_optimized_config()

from backend.app import app

def setup_optimized_app():
    """设置资源优化版本的应用"""
    print("正在设置资源优化版本的应用...")
    
    # 添加内存监控中间件
    @app.before_request
    def monitor_memory():
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        if memory_mb > 256:  # 超过256MB发出警告
            app.logger.warning(f"内存使用过高: {memory_mb:.1f}MB")
    
    # 添加请求后清理
    @app.after_request
    def cleanup_request(response):
        # 强制垃圾回收
        if gc.get_count()[0] > 500:
            gc.collect()
        return response
    
    return app

if __name__ == '__main__':
    # 创建日志目录
    Path('logs').mkdir(exist_ok=True)
    
    print("="*60)
    print("网址监控工具 - 资源优化版后端服务")
    print("="*60)
    print("配置: 资源优化模式")
    print("服务地址: http://localhost:5001")
    print("特性:")
    print("  - 最小化内存使用")
    print("  - 降低CPU占用")
    print("  - 优化数据库连接")
    print("  - 减少并发请求")
    print("  - 智能垃圾回收")
    print("="*60)
    print("按 Ctrl+C 停止服务")
    print()
    
    try:
        optimized_app = setup_optimized_app()
        
        # 启动服务器，使用优化配置
        optimized_app.run(
            host='0.0.0.0', 
            port=5001, 
            debug=False,           # 关闭DEBUG
            threaded=True,         # 启用线程模式
            processes=1,           # 单进程
            use_reloader=False,    # 关闭自动重载
            use_debugger=False     # 关闭调试器
        )
        
    except KeyboardInterrupt:
        print("\n正在关闭服务...")
    except Exception as e:
        print(f"启动失败: {e}")
        sys.exit(1)
    finally:
        print("资源优化版后端服务已停止")