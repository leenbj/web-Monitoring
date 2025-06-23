"""
网址监控工具 - 状态变化监控API路由
处理网站状态变化的查询和展示
"""

from flask import Blueprint, request, jsonify
from typing import Dict, List
import logging

from ..database import get_db
from ..models import DetectionTask
from ..services.status_change_service import StatusChangeService
from ..services.failed_site_monitor_service import FailedSiteMonitorService

logger = logging.getLogger(__name__)

bp = Blueprint('status_changes', __name__, url_prefix='/api/status-changes')

# 创建服务实例
status_change_service = StatusChangeService()
failed_monitor_service = FailedSiteMonitorService()


@bp.route('/task/<int:task_id>/recent', methods=['GET'])
def get_recent_changes(task_id: int):
    """
    获取任务的最近状态变化
    
    Args:
        task_id: 任务ID
    """
    try:
        # 获取查询参数
        hours = request.args.get('hours', 24, type=int)
        limit = request.args.get('limit', 100, type=int)
        
        # 验证任务存在
        with get_db() as db:
            task = db.query(DetectionTask).filter(DetectionTask.id == task_id).first()
            if not task:
                return jsonify({
                    'code': 404,
                    'message': '任务不存在',
                    'data': None
                }), 404
        
        # 获取状态变化记录
        changes = status_change_service.get_recent_status_changes(
            task_id=task_id,
            hours=hours,
            limit=limit
        )
        
        # 分类变化记录
        became_accessible = []
        became_failed = []
        status_changed = []
        
        for change in changes:
            if change['change_type'] == 'became_accessible':
                became_accessible.append(change)
            elif change['change_type'] == 'became_failed':
                became_failed.append(change)
            else:
                status_changed.append(change)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'task_id': task_id,
                'time_range_hours': hours,
                'total_changes': len(changes),
                'became_accessible': became_accessible,
                'became_failed': became_failed,
                'status_changed': status_changed,
                'statistics': {
                    'became_accessible_count': len(became_accessible),
                    'became_failed_count': len(became_failed),
                    'status_changed_count': len(status_changed)
                }
            }
        })
        
    except Exception as e:
        logger.error(f"获取状态变化失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'获取状态变化失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/task/<int:task_id>/summary', methods=['GET'])
def get_accessibility_summary(task_id: int):
    """
    获取任务的可访问性摘要
    
    Args:
        task_id: 任务ID
    """
    try:
        # 验证任务存在
        with get_db() as db:
            task = db.query(DetectionTask).filter(DetectionTask.id == task_id).first()
            if not task:
                return jsonify({
                    'code': 404,
                    'message': '任务不存在',
                    'data': None
                }), 404
        
        # 获取可访问性摘要
        summary = status_change_service.get_accessibility_summary(task_id=task_id)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': summary
        })
        
    except Exception as e:
        logger.error(f"获取可访问性摘要失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'获取可访问性摘要失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/task/<int:task_id>/failed-monitor', methods=['GET'])
def get_failed_monitor_status(task_id: int):
    """
    获取失败网站监控任务状态
    
    Args:
        task_id: 父任务ID
    """
    try:
        # 获取监控任务状态
        monitor_status = failed_monitor_service.get_monitor_task_status(task_id)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': monitor_status
        })
        
    except Exception as e:
        logger.error(f"获取失败监控状态失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'获取失败监控状态失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/task/<int:task_id>/failed-monitor', methods=['POST'])
def create_or_update_failed_monitor(task_id: int):
    """
    创建或更新失败网站监控任务
    
    Args:
        task_id: 父任务ID
    """
    try:
        # 验证任务存在
        with get_db() as db:
            task = db.query(DetectionTask).filter(DetectionTask.id == task_id).first()
            if not task:
                return jsonify({
                    'code': 404,
                    'message': '任务不存在',
                    'data': None
                }), 404
        
        # 创建或更新失败监控任务
        monitor_task = failed_monitor_service.create_or_update_failed_monitor_task(task_id)
        
        if monitor_task:
            return jsonify({
                'code': 200,
                'message': '失败网站监控任务创建/更新成功',
                'data': {
                    'monitor_task_id': monitor_task.id,
                    'monitor_task_name': monitor_task.name,
                    'monitored_websites_count': len(monitor_task.monitored_websites),
                    'is_active': monitor_task.is_active
                }
            })
        else:
            return jsonify({
                'code': 500,
                'message': '创建失败监控任务失败',
                'data': None
            }), 500
        
    except Exception as e:
        logger.error(f"创建失败监控任务失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'创建失败监控任务失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/task/<int:task_id>/recovered', methods=['GET'])
def get_recovered_websites(task_id: int):
    """
    获取最近恢复的网站列表
    
    Args:
        task_id: 任务ID
    """
    try:
        # 获取查询参数
        hours = request.args.get('hours', 24, type=int)
        
        # 验证任务存在
        with get_db() as db:
            task = db.query(DetectionTask).filter(DetectionTask.id == task_id).first()
            if not task:
                return jsonify({
                    'code': 404,
                    'message': '任务不存在',
                    'data': None
                }), 404
        
        # 获取恢复的网站列表
        recovered_websites = failed_monitor_service.get_recovered_websites(
            parent_task_id=task_id,
            hours=hours
        )
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'task_id': task_id,
                'time_range_hours': hours,
                'recovered_websites': recovered_websites,
                'recovered_count': len(recovered_websites)
            }
        })
        
    except Exception as e:
        logger.error(f"获取恢复网站列表失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'获取恢复网站列表失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/task/<int:task_id>/failed-monitor/run', methods=['POST'])
def run_failed_monitor_task(task_id: int):
    """
    手动运行失败网站监控任务
    
    Args:
        task_id: 父任务ID
    """
    try:
        # 获取监控任务
        monitor_status = failed_monitor_service.get_monitor_task_status(task_id)
        
        if not monitor_status.get('exists', False):
            return jsonify({
                'code': 404,
                'message': '失败监控任务不存在',
                'data': None
            }), 404
        
        # 运行监控任务
        monitor_task_id = monitor_status['id']
        success = failed_monitor_service.run_failed_site_monitor_task(monitor_task_id)
        
        if success:
            return jsonify({
                'code': 200,
                'message': '失败网站监控任务执行成功',
                'data': {
                    'monitor_task_id': monitor_task_id,
                    'execution_result': 'success'
                }
            })
        else:
            return jsonify({
                'code': 500,
                'message': '失败网站监控任务执行失败',
                'data': None
            }), 500
        
    except Exception as e:
        logger.error(f"运行失败监控任务失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'运行失败监控任务失败: {str(e)}',
            'data': None
        }), 500 