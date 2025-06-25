"""
网址监控工具 - Flask主应用
"""

import os
import sys
import signal
import atexit
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import logging

logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import Config
from backend.database import init_db, get_db
from backend.utils.helpers import ensure_dir

# 导入API蓝图
from backend.api import websites, tasks, results, files, groups, performance, status_changes, settings, auth, dify_api


def create_app(config_class=Config):
    """应用工厂函数"""
    
    # 创建Flask应用实例
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 配置JWT
    setup_jwt(app)
    
    # 配置CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # 配置日志
    configure_logging(app)
    
    # 确保必要目录存在
    ensure_directories()
    
    # 初始化数据库
    init_db()
    
    # 启动优化组件
    setup_optimizations(app)
    
    # 注册API蓝图
    register_blueprints(app)
    
    # 注册错误处理器
    register_error_handlers(app)
    
    # 注册请求钩子
    register_request_hooks(app)
    
    # 设置关闭处理器
    setup_shutdown_handlers(app)
    
    logger.info("Flask应用创建完成")
    
    return app


def configure_logging(app):
    """配置日志"""
    import logging
    from logging.handlers import RotatingFileHandler
    
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO').upper())
    log_file = app.config.get('LOG_FILE', 'logs/app.log')
    
    # 确保日志目录存在
    ensure_dir(os.path.dirname(log_file))
    
    # 配置日志格式
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s'
    )
    
    # 文件处理器 - 优化版本，减少日志文件大小
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5*1024*1024,   # 5MB（从10MB降到5MB）
        backupCount=3           # 从5个备份降到3个
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    
    # 配置Flask应用日志
    app.logger.setLevel(log_level)
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    
    # 配置根日志记录器
    logging.basicConfig(
        level=log_level,
        handlers=[file_handler, console_handler]
    )
    
    logger.info("日志系统初始化完成")


def ensure_directories():
    """确保必要的目录存在"""
    directories = [
        'logs',
        'uploads',
        'downloads',
        'database'
    ]
    
    for directory in directories:
        ensure_dir(directory)


def register_blueprints(app):
    """注册API蓝图"""
    app.register_blueprint(websites.bp)
    app.register_blueprint(tasks.bp)
    app.register_blueprint(results.bp)
    app.register_blueprint(files.bp)
    app.register_blueprint(groups.bp)
    app.register_blueprint(performance.performance_bp)
    app.register_blueprint(status_changes.bp)
    app.register_blueprint(settings.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(dify_api.bp)

    logger.info("API蓝图注册完成")


def setup_optimizations(app):
    """设置优化组件"""
    try:
        # 启动内存监控
        from backend.services.memory_monitor import start_global_memory_monitoring, register_global_cleanup_callback
        from backend.database import close_all_connections
        
        logger.info("启动内存监控...")
        start_global_memory_monitoring()
        
        # 注册数据库连接清理回调
        register_global_cleanup_callback(close_all_connections)
        
        # 启动调度服务
        try:
            from backend.services.scheduler_service import SchedulerService
            scheduler = SchedulerService()
            scheduler.start()
            app.scheduler = scheduler  # 保存引用
            logger.info("调度服务已启动")
        except Exception as e:
            logger.warning(f"调度服务启动失败: {e}")
        
        logger.info("优化组件设置完成")
        
    except Exception as e:
        logger.error(f"设置优化组件失败: {e}")


def register_error_handlers(app):
    """注册错误处理器"""
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'code': 404,
            'message': '请求的资源不存在',
            'data': None
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'code': 405,
            'message': '请求方法不被允许',
            'data': None
        }), 405
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'code': 400,
            'message': '请求参数错误',
            'data': None
        }), 400
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"服务器内部错误: {error}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误',
            'data': None
        }), 500
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.error(f"未处理的异常: {e}", exc_info=True)
        return jsonify({
            'code': 500,
            'message': '服务器发生未知错误',
            'data': None
        }), 500


def register_request_hooks(app):
    """注册请求钩子"""
    
    @app.before_request
    def log_request():
        """记录请求信息"""
        if request.path.startswith('/api/'):
            logger.info(f"{request.method} {request.path} from {request.remote_addr}")
    
    @app.after_request
    def after_request(response):
        """请求后处理"""
        if request.path.startswith('/api/'):
            logger.info(f"{request.method} {request.path} -> {response.status_code}")
        return response


def setup_shutdown_handlers(app):
    """设置关闭处理器"""
    
    def cleanup():
        """清理资源"""
        try:
            logger.info("正在清理应用资源...")
            
            # 关闭调度器
            if hasattr(app, 'scheduler'):
                app.scheduler.shutdown()
            
            # 停止内存监控
            from backend.services.memory_monitor import stop_global_memory_monitoring
            stop_global_memory_monitoring()
            
            # 关闭数据库连接
            from backend.database import close_all_connections
            close_all_connections()
            
            logger.info("应用资源清理完成")
            
        except Exception as e:
            logger.error(f"清理资源时出错: {e}")
    
    # 注册退出处理器
    atexit.register(cleanup)
    
    # 注册信号处理器
    def signal_handler(signum, frame):
        logger.info(f"收到信号 {signum}，正在关闭应用...")
        cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def start_scheduler_service(app):
    """启动调度器服务"""
    try:
        from .services.scheduler_service import SchedulerService
        
        # 创建调度器服务实例
        scheduler_service = SchedulerService()
        
        # 将调度器服务添加到应用配置中
        app.config['SCHEDULER_SERVICE'] = scheduler_service
        
        # 启动调度器
        scheduler_service.start()
        
        logger.info("调度器服务已启动")
        
        # 注册应用关闭时的清理函数
        import atexit
        def cleanup_scheduler():
            try:
                if scheduler_service:
                    scheduler_service.stop()
                    logger.info("调度器服务已停止")
            except Exception as e:
                logger.error(f"停止调度器服务失败: {e}")
        
        atexit.register(cleanup_scheduler)
        
    except Exception as e:
        logger.error(f"启动调度器服务失败: {e}")


def setup_jwt(app):
    """配置JWT"""
    # 设置JWT密钥
    app.config['JWT_SECRET_KEY'] = app.config.get('JWT_SECRET_KEY', 'your-secret-key-change-it-in-production')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False  # 不自动过期，由前端控制
    
    # 初始化JWT管理器
    jwt = JWTManager(app)
    
    # 设置JWT在黑名单中的回调
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        from backend.api.auth import blacklisted_tokens
        jti = jwt_payload['jti']
        return jti in blacklisted_tokens
    
    return jwt


# 创建应用实例
app = create_app()


@app.route('/')
def index():
    """首页"""
    return jsonify({
        'code': 200,
        'message': '网址监控工具API服务运行正常',
        'data': {
            'version': '1.0.0',
            'api_prefix': '/api',
            'endpoints': {
                'websites': '/api/websites',
                'tasks': '/api/tasks',
                'results': '/api/results'
            }
        }
    })


@app.route('/api/health')
def health_check():
    """健康检查"""
    try:
        # 检查数据库连接
        from sqlalchemy import text
        with get_db() as db:
            db.execute(text('SELECT 1'))
        
        return jsonify({
            'code': 200,
            'message': '服务健康',
            'data': {
                'status': 'healthy',
                'database': 'connected',
                'timestamp': datetime.now().isoformat()
            }
        })
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return jsonify({
            'code': 500,
            'message': '服务异常',
            'data': {
                'status': 'unhealthy',
                'error': str(e)
            }
        }), 500


@app.route('/api/system/info')
def system_info():
    """系统信息"""
    try:
        import platform
        import psutil
        from datetime import datetime
        
        # 系统信息
        system_info = {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'memory_total': psutil.virtual_memory().total,
            'memory_available': psutil.virtual_memory().available,
            'disk_usage': psutil.disk_usage('/').percent,
            'uptime': datetime.now().isoformat()
        }
        
        # 数据库统计
        with get_db() as db:
            from backend.models import Website, DetectionTask, DetectionRecord
            
            website_count = db.query(Website).count()
            task_count = db.query(DetectionTask).count()
            record_count = db.query(DetectionRecord).count()
        
        # 调度器状态
        scheduler_status = {}
        if 'SCHEDULER_SERVICE' in app.config:
            scheduler = app.config['SCHEDULER_SERVICE']
            scheduler_status = scheduler.get_status()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'system': system_info,
                'database': {
                    'websites': website_count,
                    'tasks': task_count,
                    'records': record_count
                },
                'scheduler_status': scheduler_status
            }
        })
        
    except Exception as e:
        logger.error(f"获取系统信息失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'获取系统信息失败: {str(e)}',
            'data': None
        }), 500


if __name__ == '__main__':
    # 开发模式运行
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"启动Flask应用，端口: {port}, 调试模式: {debug}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True
    )