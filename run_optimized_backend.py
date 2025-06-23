#!/usr/bin/env python3
"""
优化版后端启动脚本
专门针对低资源占用进行优化
"""

import sys
import os
import gc
import logging

# 设置环境变量启用优化模式
os.environ['OPTIMIZED_MODE'] = '1'
os.environ['PYTHONOPTIMIZE'] = '1'  # 启用Python优化
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # 不生成.pyc文件

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入优化配置
from backend.config_optimized import optimized_config

# 配置日志为WARNING级别
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s | %(levelname)-8s | %(name)s - %(message)s'
)

# 强制垃圾回收
gc.collect()

# 设置垃圾回收阈值（更激进的回收）
gc.set_threshold(400, 5, 5)  # 默认是(700, 10, 10)

from backend.app import create_app

def create_optimized_app():
    """创建优化版应用"""
    
    # 使用优化配置创建应用
    app = create_app()
    
    # 应用优化配置
    app.config.update({
        'LOG_LEVEL': optimized_config.LOG_LEVEL,
        'DETECTION_CONFIG': optimized_config.DETECTION_CONFIG,
        'ASYNC_DETECTION_CONFIG': optimized_config.ASYNC_DETECTION_CONFIG,
        'MEMORY_CONFIG': optimized_config.MEMORY_CONFIG,
        'SCHEDULER_CONFIG': optimized_config.SCHEDULER_CONFIG
    })
    
    # 添加内存优化中间件
    @app.before_request
    def optimize_memory():
        """请求前内存优化"""
        # 每100个请求执行一次垃圾回收
        if not hasattr(optimize_memory, 'counter'):
            optimize_memory.counter = 0
        
        optimize_memory.counter += 1
        if optimize_memory.counter % 100 == 0:
            gc.collect()
    
    @app.after_request
    def cleanup_response(response):
        """响应后清理"""
        # 对于大响应，立即清理
        if hasattr(response, 'content_length') and response.content_length and response.content_length > 1024*1024:
            gc.collect()
        return response
    
    return app

if __name__ == '__main__':
    print("🚀 启动优化版网址监控工具后端服务...")
    print("📊 优化配置:")
    print(f"   - 最大内存限制: {optimized_config.MEMORY_CONFIG['max_memory_mb']}MB")
    print(f"   - 最大并发数: {optimized_config.ASYNC_DETECTION_CONFIG['max_concurrent']}")
    print(f"   - 日志级别: {optimized_config.LOG_LEVEL}")
    print(f"   - 调度器轮询间隔: {optimized_config.SCHEDULER_CONFIG['poll_interval']}秒")
    print("🌐 服务地址: http://localhost:5001")
    print("📚 API文档: http://localhost:5001/api")
    print("⚡ 按 Ctrl+C 停止服务")
    
    # 创建优化应用
    app = create_optimized_app()
    
    # 启动服务（使用优化参数）
    app.run(
        host='0.0.0.0', 
        port=5001, 
        debug=False,           # 关闭调试模式
        threaded=True,         # 启用多线程
        processes=1,           # 单进程
        use_reloader=False     # 关闭自动重载
    ) 