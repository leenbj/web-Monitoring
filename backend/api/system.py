"""
系统监控API
提供内存使用、缓存状态等系统信息
"""

from flask import Blueprint, jsonify
import psutil
import gc
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('system', __name__, url_prefix='/api/system')


@bp.route('/status', methods=['GET'])
def get_system_status():
    """获取系统状态信息"""
    try:
        # 内存使用情况
        from ..services.memory_manager import memory_manager
        memory_stats = memory_manager.get_memory_stats()
        
        # 缓存状态
        from ..utils.cache import app_cache
        cache_stats = app_cache.get_stats()
        
        # 进程信息
        process = psutil.Process()
        cpu_percent = process.cpu_percent()
        
        # 数据库连接信息
        from ..database import engine
        pool_status = {
            'pool_size': engine.pool.size(),
            'checked_in': engine.pool.checkedin(),
            'checked_out': engine.pool.checkedout(),
            'overflow': engine.pool.overflow(),
            'invalid': engine.pool.invalid()
        }
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'memory': memory_stats,
                'cache': cache_stats,
                'cpu_percent': cpu_percent,
                'database_pool': pool_status,
                'garbage_collection': {
                    'generation_0': gc.get_count()[0],
                    'generation_1': gc.get_count()[1], 
                    'generation_2': gc.get_count()[2]
                }
            }
        })
        
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'获取系统状态失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/cleanup', methods=['POST'])
def force_cleanup():
    """手动触发系统清理"""
    try:
        # 内存清理
        from ..services.memory_manager import memory_manager
        memory_manager.force_cleanup()
        
        # 缓存清理
        from ..utils.cache import app_cache
        app_cache.cleanup_expired()
        
        # 垃圾回收
        collected = gc.collect()
        
        return jsonify({
            'code': 200,
            'message': '系统清理完成',
            'data': {
                'garbage_collected': collected,
                'cleanup_completed': True
            }
        })
        
    except Exception as e:
        logger.error(f"系统清理失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'系统清理失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/optimize', methods=['POST'])
def optimize_system():
    """系统优化建议"""
    try:
        suggestions = []
        
        # 检查内存使用
        from ..services.memory_manager import memory_manager
        memory_stats = memory_manager.get_memory_stats()
        
        if memory_stats.get('rss_mb', 0) > 256:
            suggestions.append({
                'type': 'memory',
                'level': 'warning',
                'message': '内存使用较高，建议执行清理操作'
            })
        
        # 检查缓存状态
        from ..utils.cache import app_cache
        cache_stats = app_cache.get_stats()
        
        if cache_stats.get('expired_entries', 0) > 10:
            suggestions.append({
                'type': 'cache',
                'level': 'info',
                'message': '存在较多过期缓存，建议清理'
            })
        
        # 检查数据库连接
        from ..database import engine
        checked_out = engine.pool.checkedout()
        if checked_out > 5:
            suggestions.append({
                'type': 'database',
                'level': 'warning',
                'message': '数据库连接使用较多，注意连接释放'
            })
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'suggestions': suggestions,
                'total_suggestions': len(suggestions)
            }
        })
        
    except Exception as e:
        logger.error(f"获取优化建议失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'获取优化建议失败: {str(e)}',
            'data': None
        }), 500