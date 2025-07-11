"""
性能监控API
提供系统性能、内存使用、检测统计等监控信息
"""

from flask import Blueprint, jsonify, request
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any

from ..services.memory_monitor import get_memory_manager
from ..database import get_db_session
from ..models import DetectionRecord
from ..utils.helpers import get_beijing_time

logger = logging.getLogger(__name__)

performance_bp = Blueprint('performance', __name__, url_prefix='/api/performance')


@performance_bp.route('/memory', methods=['GET'])
def get_memory_status():
    """
    获取内存使用状态
    
    Returns:
        内存监控信息
    """
    try:
        memory_manager = get_memory_manager()
        status = memory_manager.get_status()
        
        return jsonify({
            'code': 200,
            'message': '获取内存状态成功',
            'data': status
        })
        
    except Exception as e:
        logger.error(f"获取内存状态失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'获取内存状态失败: {str(e)}'
        }), 500


@performance_bp.route('/memory/optimize', methods=['POST'])
def optimize_memory():
    """
    手动触发内存优化
    
    Request Body:
        level: 优化级别 ('light', 'normal', 'aggressive')
    
    Returns:
        优化结果
    """
    try:
        data = request.get_json() or {}
        level = data.get('level', 'normal')
        
        if level not in ['light', 'normal', 'aggressive']:
            return jsonify({
                'code': 400,
                'message': '无效的优化级别，支持: light, normal, aggressive'
            }), 400
        
        memory_manager = get_memory_manager()
        result = memory_manager.optimize_now(level)
        
        return jsonify({
            'code': 200,
            'message': '内存优化完成',
            'data': {
                'optimization_result': result,
                'current_status': memory_manager.get_status()
            }
        })
        
    except Exception as e:
        logger.error(f"内存优化失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'内存优化失败: {str(e)}'
        }), 500


@performance_bp.route('/detection/stats', methods=['GET'])
def get_detection_stats():
    """
    获取检测统计信息
    
    Query Parameters:
        hours: 统计时间范围(小时，默认24)
        detailed: 是否返回详细统计(默认false)
    
    Returns:
        检测统计信息
    """
    try:
        hours = int(request.args.get('hours', 24))
        detailed = request.args.get('detailed', 'false').lower() == 'true'
        
        # 计算时间范围
        cutoff_time = get_beijing_time() - timedelta(hours=hours)
        
        with get_db_session() as session:
            # 基础统计查询
            query = session.query(DetectionRecord).filter(
                DetectionRecord.detected_at >= cutoff_time
            )
            
            total_checks = query.count()
            
            if total_checks == 0:
                return jsonify({
                    'code': 200,
                    'message': '获取检测统计成功',
                    'data': {
                        'period_hours': hours,
                        'total_checks': 0,
                        'summary': {},
                        'detailed': {}
                    }
                })
            
            # 按状态统计
            status_stats = {}
            for status in ['standard', 'redirect', 'failed']:
                count = query.filter(DetectionRecord.status == status).count()
                status_stats[status] = {
                    'count': count,
                    'percentage': round(count / total_checks * 100, 1)
                }
            
            # 响应时间统计
            response_times = [
                r.response_time for r in query.all() 
                if r.response_time is not None and r.response_time > 0
            ]
            
            response_time_stats = {}
            if response_times:
                response_time_stats = {
                    'avg': round(sum(response_times) / len(response_times), 3),
                    'min': round(min(response_times), 3),
                    'max': round(max(response_times), 3),
                    'count': len(response_times)
                }
            
            # 构建基础响应
            stats_data = {
                'period_hours': hours,
                'total_checks': total_checks,
                'summary': {
                    'status_distribution': status_stats,
                    'response_time': response_time_stats,
                    'success_rate': round((status_stats['standard']['count'] + 
                                         status_stats['redirect']['count']) / total_checks * 100, 1)
                }
            }
            
            # 详细统计
            if detailed:
                detailed_stats = _get_detailed_detection_stats(session, cutoff_time)
                stats_data['detailed'] = detailed_stats
            
            return jsonify({
                'code': 200,
                'message': '获取检测统计成功',
                'data': stats_data
            })
        
    except Exception as e:
        logger.error(f"获取检测统计失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'获取检测统计失败: {str(e)}'
        }), 500


def _get_detailed_detection_stats(session, cutoff_time) -> Dict[str, Any]:
    """
    获取详细检测统计信息
    
    Args:
        session: 数据库会话
        cutoff_time: 统计起始时间
        
    Returns:
        详细统计信息
    """
    try:
        # 按小时分布统计
        hourly_stats = []
        current_time = get_beijing_time()
        
        for i in range(24):  # 最近24小时
            hour_start = current_time - timedelta(hours=i+1)
            hour_end = current_time - timedelta(hours=i)
            
            hour_query = session.query(DetectionRecord).filter(
                DetectionRecord.detected_at >= hour_start,
                DetectionRecord.detected_at < hour_end
            )
            
            hour_count = hour_query.count()
            hour_stats = {
                'hour': hour_start.strftime('%H:00'),
                'total': hour_count,
                'standard': hour_query.filter(DetectionRecord.status == 'standard').count(),
                'redirect': hour_query.filter(DetectionRecord.status == 'redirect').count(),
                'failed': hour_query.filter(DetectionRecord.status == 'failed').count()
            }
            
            hourly_stats.append(hour_stats)
        
        # 失败原因统计
        failure_reasons = {}
        failed_results = session.query(DetectionRecord).filter(
            DetectionRecord.detected_at >= cutoff_time,
            DetectionRecord.status == 'failed',
            DetectionRecord.failure_reason.isnot(None)
        ).all()
        
        for result in failed_results:
            reason = result.failure_reason or 'unknown'
            failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
        
        # 性能分布统计
        performance_distribution = {
            'fast': 0,      # < 2s
            'normal': 0,    # 2-5s
            'slow': 0,      # 5-10s
            'very_slow': 0  # > 10s
        }
        
        all_results = session.query(DetectionRecord).filter(
            DetectionRecord.detected_at >= cutoff_time,
            DetectionRecord.response_time.isnot(None),
            DetectionRecord.response_time > 0
        ).all()
        
        for result in all_results:
            response_time = result.response_time
            if response_time < 2:
                performance_distribution['fast'] += 1
            elif response_time < 5:
                performance_distribution['normal'] += 1
            elif response_time < 10:
                performance_distribution['slow'] += 1
            else:
                performance_distribution['very_slow'] += 1
        
        return {
            'hourly_distribution': hourly_stats,
            'failure_reasons': failure_reasons,
            'performance_distribution': performance_distribution
        }
        
    except Exception as e:
        logger.error(f"获取详细统计失败: {e}")
        return {}


@performance_bp.route('/system', methods=['GET'])
def get_system_info():
    """
    获取系统信息
    
    Returns:
        系统信息
    """
    try:
        import psutil
        import platform
        
        # CPU信息
        cpu_info = {
            'count': psutil.cpu_count(),
            'usage_percent': psutil.cpu_percent(interval=1),
            'frequency': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
        }
        
        # 内存信息
        memory = psutil.virtual_memory()
        memory_info = {
            'total_mb': round(memory.total / 1024 / 1024, 1),
            'available_mb': round(memory.available / 1024 / 1024, 1),
            'used_mb': round(memory.used / 1024 / 1024, 1),
            'percent': memory.percent
        }
        
        # 磁盘信息
        disk = psutil.disk_usage('/')
        disk_info = {
            'total_gb': round(disk.total / 1024 / 1024 / 1024, 1),
            'used_gb': round(disk.used / 1024 / 1024 / 1024, 1),
            'free_gb': round(disk.free / 1024 / 1024 / 1024, 1),
            'percent': round(disk.used / disk.total * 100, 1)
        }
        
        # 系统信息
        system_info = {
            'platform': platform.platform(),
            'architecture': platform.architecture()[0],
            'python_version': platform.python_version(),
            'hostname': platform.node(),
            'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat()
        }
        
        return jsonify({
            'code': 200,
            'message': '获取系统信息成功',
            'data': {
                'cpu': cpu_info,
                'memory': memory_info,
                'disk': disk_info,
                'system': system_info,
                'timestamp': get_beijing_time().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"获取系统信息失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'获取系统信息失败: {str(e)}'
        }), 500


@performance_bp.route('/monitoring/start', methods=['POST'])
def start_monitoring():
    """
    启动性能监控
    
    Returns:
        操作结果
    """
    try:
        memory_manager = get_memory_manager()
        
        if memory_manager.is_monitoring:
            return jsonify({
                'code': 200,
                'message': '性能监控已在运行',
                'data': memory_manager.get_status()
            })
        
        memory_manager.start_monitoring()
        
        return jsonify({
            'code': 200,
            'message': '性能监控已启动',
            'data': memory_manager.get_status()
        })
        
    except Exception as e:
        logger.error(f"启动性能监控失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'启动性能监控失败: {str(e)}'
        }), 500


@performance_bp.route('/monitoring/stop', methods=['POST'])
def stop_monitoring():
    """
    停止性能监控
    
    Returns:
        操作结果
    """
    try:
        memory_manager = get_memory_manager()
        
        if not memory_manager.is_monitoring:
            return jsonify({
                'code': 200,
                'message': '性能监控未在运行'
            })
        
        memory_manager.stop_monitoring()
        
        return jsonify({
            'code': 200,
            'message': '性能监控已停止'
        })
        
    except Exception as e:
        logger.error(f"停止性能监控失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'停止性能监控失败: {str(e)}'
        }), 500


@performance_bp.route('/health', methods=['GET'])
def health_check():
    """
    健康检查端点
    
    Returns:
        系统健康状态
    """
    try:
        # 检查数据库连接
        db_healthy = True
        try:
            with get_db_session() as session:
                session.execute("SELECT 1").fetchone()
        except Exception as e:
            logger.error(f"数据库健康检查失败: {e}")
            db_healthy = False
        
        # 检查内存状态
        memory_manager = get_memory_manager()
        memory_status = memory_manager.get_status()
        memory_healthy = memory_status['current_status'] != 'critical'
        
        # 整体健康状态
        overall_healthy = db_healthy and memory_healthy
        
        health_data = {
            'healthy': overall_healthy,
            'timestamp': get_beijing_time().isoformat(),
            'components': {
                'database': {
                    'healthy': db_healthy,
                    'status': 'ok' if db_healthy else 'error'
                },
                'memory': {
                    'healthy': memory_healthy,
                    'status': memory_status['current_status'],
                    'usage_percent': memory_status['current_stats']['memory_usage_percent']
                },
                'monitoring': {
                    'active': memory_manager.is_monitoring,
                    'status': 'active' if memory_manager.is_monitoring else 'inactive'
                }
            }
        }
        
        status_code = 200 if overall_healthy else 503
        
        return jsonify({
            'code': status_code,
            'message': '健康检查完成',
            'data': health_data
        }), status_code
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'健康检查失败: {str(e)}',
            'data': {
                'healthy': False,
                'timestamp': get_beijing_time().isoformat()
            }
        }), 500 