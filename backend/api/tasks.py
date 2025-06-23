"""
网址监控工具 - 检测任务API路由
处理检测任务的管理和执行
"""

from flask import Blueprint, request, jsonify
from typing import Dict, List
import threading
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import Website, DetectionTask, DetectionRecord
from ..services.website_detector import WebsiteDetector
from ..services.scheduler import TaskScheduler

import logging

logger = logging.getLogger(__name__)

bp = Blueprint('tasks', __name__, url_prefix='/api/tasks')

# 全局任务调度器实例
task_scheduler = None


def get_scheduler() -> TaskScheduler:
    """获取任务调度器实例"""
    global task_scheduler
    if not task_scheduler:
        task_scheduler = TaskScheduler()
    return task_scheduler


def execute_detection_task(task_id: int):
    """
    执行检测任务的核心逻辑
    
    Args:
        task_id: 任务ID
    """
    logger.info(f"开始执行检测任务: {task_id}")
    try:
        with get_db() as db:
            # 获取任务对象
            task = db.query(DetectionTask).filter(DetectionTask.id == task_id).first()
            if not task:
                logger.error(f"任务 {task_id} 不存在")
                return False
            
            if task.is_running:
                logger.warning(f"任务 {task_id} 正在运行中，跳过本次执行")
                return False
            
            logger.info(f"任务查询成功: {task.name}")
            
            # 获取要检测的网站
            websites = [w for w in task.websites if w.is_active] if hasattr(task, 'websites') else []
            
            if not websites:
                logger.warning(f"任务 {task_id} 没有找到可检测的网站")
                return False
            
            # 更新任务状态
            task.is_running = True
            task.last_run_at = datetime.now()
            db.commit()
            
            logger.info(f"开始执行任务 {task_id}，检测 {len(websites)} 个网站")
            
            # 详细记录网站信息和顺序
            for i, website in enumerate(websites):
                logger.info(f"网站 {i}: ID={website.id}, 名称={website.name}, URL={website.url}")
            
            # 执行检测
            detector = WebsiteDetector()
            urls = [w.url for w in websites]
            
            logger.info(f"开始批量检测 {len(urls)} 个URL: {urls}")
            results = detector.detect_batch_websites(urls)
            logger.info(f"检测完成，获得 {len(results)} 个结果")
            
            # 详细记录检测结果和对应关系
            for i, result in enumerate(results):
                website = websites[i]
                logger.info(f"结果 {i}: 网站ID={website.id}, URL={result.original_url}, 状态={result.status}, Final={result.final_url}")
            
            # 保存检测结果
            detection_records = []
            for i, result in enumerate(results):
                website = websites[i]
                
                record = DetectionRecord(
                    task_id=task.id,
                    website_id=website.id,
                    status=result.status,
                    response_time=result.response_time or 0.0,
                    http_status_code=result.http_status_code,
                    final_url=result.final_url or '',
                    error_message=result.error_message or '',
                    failure_reason=getattr(result, 'failure_reason', '') or '',
                    ssl_info=getattr(result, 'ssl_info', {}) or {},
                    page_title=getattr(result, 'page_title', ''),
                    page_content_length=getattr(result, 'page_content_length', 0),
                    retry_count=getattr(result, 'retry_count', 0),
                    redirect_chain=getattr(result, 'redirect_chain', []),
                    detected_at=result.detected_at.replace(tzinfo=None) if result.detected_at else datetime.now()
                )
                
                detection_records.append(record)
                db.add(record)
                logger.debug(f"添加检测记录: 网站{website.id}, 状态{result.status}")
            
            db.commit()
            
            # 检测状态变化
            try:
                from ..services.status_change_service import StatusChangeService
                status_change_service = StatusChangeService()
                status_changes = status_change_service.detect_status_changes(task.id, detection_records)
                logger.info(f"检测到 {len(status_changes)} 个网站状态变化")
                
                # 创建或更新失败网站监控任务
                from ..services.failed_site_monitor_service import FailedSiteMonitorService
                failed_monitor_service = FailedSiteMonitorService()
                failed_monitor_service.create_or_update_failed_monitor_task(task.id)
                
            except Exception as change_error:
                logger.error(f"状态变化检测失败: {change_error}")
            
            logger.info(f"任务 {task_id} 执行完成，检测 {len(websites)} 个网站，生成 {len(results)} 条记录")
            
            # 重置任务状态
            task.is_running = False
            db.commit()
            
            return True
            
    except Exception as e:
        import traceback
        logger.error(f"任务 {task_id} 执行失败: {e}")
        logger.error(f"堆栈跟踪: {traceback.format_exc()}")
        # 尝试重置任务状态
        try:
            with get_db() as error_db:
                error_task = error_db.query(DetectionTask).filter(DetectionTask.id == task_id).first()
                if error_task:
                    error_task.is_running = False
                    error_db.commit()
        except Exception as reset_error:
            logger.error(f"重置任务状态失败: {reset_error}")
        return False


@bp.route('/', methods=['GET'])
def get_tasks():
    """
    获取检测任务列表
    """
    try:
        with get_db() as db:
            # 获取查询参数
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 20, type=int), 100)
            status = request.args.get('status', '', type=str)
            
            # 构建查询
            query = db.query(DetectionTask)
            
            if status:
                query = query.filter(DetectionTask.is_active == (status == 'active'))
            
            # 分页
            total = query.count()
            tasks = query.order_by(DetectionTask.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
            
            # 序列化数据
            tasks_data = []
            for task in tasks:
                # 获取任务关联的网站数量
                website_count = len(task.websites) if hasattr(task, 'websites') else 0
                
                tasks_data.append({
                    'id': task.id,
                    'name': task.name,
                    'description': task.description,
                    'website_count': website_count,
                    'interval_hours': task.interval_hours,
                    'is_active': task.is_active,
                    'is_running': task.is_running,
                    'created_at': task.created_at.isoformat(),
                    'last_run_at': task.last_run_at.isoformat() if task.last_run_at else None,
                    'next_run_at': task.next_run_at.isoformat() if task.next_run_at else None
                })
            
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': {
                    'tasks': tasks_data,
                    'pagination': {
                        'page': page,
                        'per_page': per_page,
                        'total': total,
                        'pages': (total - 1) // per_page + 1 if total > 0 else 0
                    }
                }
            })
        
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'获取任务列表失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/', methods=['POST'])
def create_task():
    """
    创建检测任务
    """
    try:
        with get_db() as db:
            data = request.get_json()
            
            # 验证必填字段
            if not data or not data.get('name'):
                return jsonify({
                    'code': 400,
                    'message': '任务名称不能为空',
                    'data': None
                }), 400
            
            name = data['name'].strip()
            task_description = data.get('description', '').strip()
            website_ids = data.get('website_ids', [])
            group_ids = data.get('group_ids', [])
            interval_minutes = data.get('interval_minutes', 60)
            max_concurrent = data.get('max_concurrent', 10)
            timeout_seconds = data.get('timeout_seconds', 30)
            retry_times = data.get('retry_times', 3)
            
            # 验证参数
            if interval_minutes < 1:
                return jsonify({
                    'code': 400,
                    'message': '检测间隔不能少于1分钟',
                    'data': None
                }), 400
            
            if interval_minutes > 1000:
                return jsonify({
                    'code': 400,
                    'message': '检测间隔不能超过1000分钟',
                    'data': None
                }), 400
            
            # 获取要检测的网站
            websites = []
            
            # 优先使用分组选择
            if group_ids:
                from ..models import WebsiteGroup
                websites = db.query(Website).filter(
                    Website.group_id.in_(group_ids),
                    Website.is_active == True
                ).all()
            elif website_ids:
                # 兼容旧的网站选择方式
                websites = db.query(Website).filter(
                    Website.id.in_(website_ids),
                    Website.is_active == True
                ).all()
            else:
                # 如果没有指定分组或网站，检测所有活跃网站
                websites = db.query(Website).filter(Website.is_active == True).all()
            
            if not websites:
                return jsonify({
                    'code': 400,
                    'message': '没有找到可检测的网站',
                    'data': None
                }), 400
            
            # 创建检测任务 - 将分钟转换为小时存储
            interval_hours = interval_minutes / 60
            task = DetectionTask(
                name=name,
                description=task_description,
                interval_hours=interval_hours,
                max_concurrent=max_concurrent,
                timeout_seconds=timeout_seconds,
                retry_times=retry_times
            )
            
            db.add(task)
            db.commit()
            db.refresh(task)
            
            # 添加网站关联关系
            for website in websites:
                task.websites.append(website)
            db.commit()
            
            logger.info(f"创建检测任务成功: {task.name}, 网站数量: {len(websites)}")
            
            return jsonify({
                'code': 200,
                'message': '创建任务成功',
                'data': {
                    'id': task.id,
                    'name': task.name,
                    'description': task.description,
                    'interval_minutes': task.interval_hours * 60,
                    'max_concurrent': task.max_concurrent,
                    'timeout_seconds': task.timeout_seconds,
                    'retry_times': task.retry_times,
                    'website_count': len(websites),
                    'created_at': task.created_at.isoformat()
                }
            })
        
    except Exception as e:
        logger.error(f"创建检测任务失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'创建检测任务失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/<int:task_id>', methods=['GET'])
def get_task(task_id: int):
    """
    获取任务详情
    """
    try:
        with get_db() as db:
            task = db.query(DetectionTask).filter(DetectionTask.id == task_id).first()
            
            if not task:
                return jsonify({
                    'code': 404,
                    'message': '任务不存在',
                    'data': None
                }), 404
            
            # 获取任务相关的网站
            websites = task.websites if hasattr(task, 'websites') else []
            
            # 获取网站所属的分组
            from ..models import WebsiteGroup
            group_ids = set()
            for website in websites:
                if website.group_id:
                    group_ids.add(website.group_id)
            
            groups = db.query(WebsiteGroup).filter(WebsiteGroup.id.in_(group_ids)).all() if group_ids else []
            
            groups_data = [
                {
                    'id': g.id,
                    'name': g.name,
                    'color': g.color,
                    'description': g.description
                } for g in groups
            ]
            
            websites_data = [
                {
                    'id': w.id,
                    'name': w.name,
                    'url': w.url,
                    'is_active': w.is_active
                } for w in websites
            ]
            
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': {
                    'id': task.id,
                    'name': task.name,
                    'description': task.description,
                    'website_count': len(websites),
                    'interval_minutes': task.interval_hours * 60,
                    'is_active': task.is_active,
                    'is_running': task.is_running,
                    'created_at': task.created_at.isoformat(),
                    'last_run_at': task.last_run_at.isoformat() if task.last_run_at else None,
                    'next_run_at': task.next_run_at.isoformat() if task.next_run_at else None,
                    'groups': groups_data,
                    'websites': websites_data
                }
            })
        
    except Exception as e:
        logger.error(f"获取任务详情失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'获取任务详情失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/<int:task_id>/start', methods=['POST'])
def start_task(task_id: int):
    """
    启动检测任务（立即执行）
    """
    logger.info(f"收到启动任务请求: task_id={task_id}")
    try:
        with get_db() as db:
            task = db.query(DetectionTask).filter(DetectionTask.id == task_id).first()
            
            if not task:
                return jsonify({
                    'code': 404,
                    'message': '任务不存在',
                    'data': None
                }), 404
            
            if task.is_running:
                return jsonify({
                    'code': 400,
                    'message': '任务正在运行中',
                    'data': None
                }), 400
            
            # 在后台线程中执行检测任务
            def run_detection():
                logger.info(f"线程启动：开始执行任务 {task.id}")
                execute_detection_task(task.id)
            
            # 启动后台线程
            logger.info(f"准备启动线程执行任务 {task.id}")
            thread = threading.Thread(target=run_detection)
            thread.daemon = True
            thread.start()
            logger.info(f"线程已启动，任务 {task.id}")
            
            return jsonify({
                'code': 200,
                'message': '任务已启动',
                'data': {
                    'task_id': task.id,
                    'status': 'starting'
                }
            })
        
    except Exception as e:
        logger.error(f"启动任务失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'启动任务失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/<int:task_id>/schedule', methods=['POST'])
def schedule_task(task_id: int):
    """
    设置任务定时调度
    """
    try:
        with get_db() as db:
            task = db.query(DetectionTask).filter(DetectionTask.id == task_id).first()
            
            if not task:
                return jsonify({
                    'code': 404,
                    'message': '任务不存在',
                    'data': None
                }), 404
            
            scheduler = get_scheduler()
            
            if task.is_active:
                # 停止现有调度
                scheduler.stop_task(task.id)
            
            # 启动新调度
            task.is_active = True
            task.next_run_at = datetime.now() + timedelta(hours=task.interval_hours)
            db.commit()
            
            success = scheduler.start_task(task.id, task.interval_hours * 60)  # 调度器需要分钟
            
            if success:
                logger.info(f"任务 {task.id} 调度设置成功，间隔: {task.interval_hours * 60} 分钟")
                return jsonify({
                    'code': 200,
                    'message': '任务调度设置成功',
                    'data': {
                        'task_id': task.id,
                        'interval_minutes': task.interval_hours * 60,
                        'next_run_at': task.next_run_at.isoformat()
                    }
                })
            else:
                return jsonify({
                    'code': 500,
                    'message': '任务调度设置失败',
                    'data': None
                }), 500
        
    except Exception as e:
        logger.error(f"设置任务调度失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'设置任务调度失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/<int:task_id>/stop', methods=['POST'])
def stop_task(task_id: int):
    """
    停止任务调度
    """
    try:
        with get_db() as db:
            task = db.query(DetectionTask).filter(DetectionTask.id == task_id).first()
            
            if not task:
                return jsonify({
                    'code': 404,
                    'message': '任务不存在',
                    'data': None
                }), 404
            
            scheduler = get_scheduler()
            
            # 停止调度
            success = scheduler.stop_task(task.id)
            
            if success:
                task.is_active = False
                task.next_run_at = None
                db.commit()
                
                logger.info(f"任务 {task.id} 已停止调度")
                return jsonify({
                    'code': 200,
                    'message': '任务已停止',
                    'data': {
                        'task_id': task.id,
                        'status': 'stopped'
                    }
                })
            else:
                return jsonify({
                    'code': 500,
                    'message': '停止任务失败',
                    'data': None
                }), 500
        
    except Exception as e:
        logger.error(f"停止任务失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'停止任务失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/<int:task_id>/update', methods=['PUT'])
def update_task(task_id: int):
    """
    更新检测任务
    """
    logger.info(f"收到PUT请求: /api/tasks/{task_id}/update")
    return update_task_impl(task_id)


@bp.route('/<int:task_id>/delete', methods=['DELETE'])
def delete_task(task_id: int):
    """
    删除检测任务
    """
    logger.info(f"收到DELETE请求: /api/tasks/{task_id}/delete")
    return delete_task_impl(task_id)


def update_task_impl(task_id: int):
    """
    更新检测任务
    """
    try:
        with get_db() as db:
            task = db.query(DetectionTask).filter(DetectionTask.id == task_id).first()
            
            if not task:
                return jsonify({
                    'code': 404,
                    'message': '任务不存在',
                    'data': None
                }), 404
            
            data = request.get_json()
            
            # 验证必填字段
            if not data or not data.get('name'):
                return jsonify({
                    'code': 400,
                    'message': '任务名称不能为空',
                    'data': None
                }), 400
            
            name = data['name'].strip()
            task_description = data.get('description', '').strip()
            website_ids = data.get('website_ids', [])
            group_ids = data.get('group_ids', [])
            interval_minutes = data.get('interval_minutes', task.interval_hours * 60)
            max_concurrent = data.get('max_concurrent', task.max_concurrent)
            timeout_seconds = data.get('timeout_seconds', task.timeout_seconds)
            retry_times = data.get('retry_times', task.retry_times)
            
            # 验证参数 - 将分钟转换为小时
            interval_hours = interval_minutes / 60
            if interval_hours < 0.1:
                return jsonify({
                    'code': 400,
                    'message': '检测间隔不能少于6分钟(0.1小时)',
                    'data': None
                }), 400
            
            if interval_hours > 168:
                return jsonify({
                    'code': 400,
                    'message': '检测间隔不能超过168小时(7天)',
                    'data': None
                }), 400
            
            # 如果任务正在运行，需要先停止调度
            was_active = task.is_active
            if was_active:
                scheduler = get_scheduler()
                scheduler.stop_task(task.id)
                task.is_active = False
                task.next_run_at = None
            
            # 更新任务基本信息
            task.name = name
            task.description = task_description
            task.interval_hours = interval_hours
            task.max_concurrent = max_concurrent
            task.timeout_seconds = timeout_seconds
            task.retry_times = retry_times
            
            # 更新网站关联关系
            # 清除现有关联
            task.websites.clear()
            
            # 获取要检测的网站
            websites = []
            
            # 优先使用分组选择
            if group_ids:
                from ..models import WebsiteGroup
                websites = db.query(Website).filter(
                    Website.group_id.in_(group_ids),
                    Website.is_active == True
                ).all()
            elif website_ids:
                # 兼容旧的网站选择方式
                websites = db.query(Website).filter(
                    Website.id.in_(website_ids),
                    Website.is_active == True
                ).all()
            
            if not websites:
                return jsonify({
                    'code': 400,
                    'message': '没有找到可检测的网站',
                    'data': None
                }), 400
            
            # 添加新的关联
            for website in websites:
                task.websites.append(website)
            
            db.commit()
            
            # 如果之前是活跃状态，重新启动调度
            if was_active:
                task.is_active = True
                task.next_run_at = datetime.now() + timedelta(hours=task.interval_hours)
                db.commit()
                
                scheduler = get_scheduler()
                scheduler.start_task(task.id, task.interval_hours * 60)  # 调度器需要分钟
            
            logger.info(f"更新任务成功: {task.name}, 网站数量: {len(task.websites)}")
            
            return jsonify({
                'code': 200,
                'message': '更新任务成功',
                'data': {
                    'id': task.id,
                    'name': task.name,
                    'description': task.description,
                    'interval_minutes': task.interval_hours * 60,
                    'max_concurrent': task.max_concurrent,
                    'timeout_seconds': task.timeout_seconds,
                    'retry_times': task.retry_times,
                    'website_count': len(task.websites),
                    'is_active': task.is_active,
                    'updated_at': datetime.now().isoformat()
                }
            })
        
    except Exception as e:
        logger.error(f"更新任务失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'更新任务失败: {str(e)}',
            'data': None
        }), 500


def delete_task_impl(task_id: int):
    """
    删除检测任务
    """
    try:
        with get_db() as db:
            task = db.query(DetectionTask).filter(DetectionTask.id == task_id).first()
            
            if not task:
                return jsonify({
                    'code': 404,
                    'message': '任务不存在',
                    'data': None
                }), 404
            
            # 如果任务正在运行，先停止
            if task.is_active:
                scheduler = get_scheduler()
                scheduler.stop_task(task.id)
            
            # 删除相关记录
            db.query(DetectionRecord).filter(DetectionRecord.task_id == task_id).delete()
            
            # 删除任务
            db.delete(task)
            db.commit()
            
            logger.info(f"删除任务成功: {task_id}")
            
            return jsonify({
                'code': 200,
                'message': '删除任务成功',
                'data': None
            })
        
    except Exception as e:
        logger.error(f"删除任务失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'删除任务失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/<int:task_id>/results', methods=['GET'])
def get_task_results(task_id: int):
    """
    获取任务检测结果
    """
    try:
        with get_db() as db:
            task = db.query(DetectionTask).filter(DetectionTask.id == task_id).first()
            
            if not task:
                return jsonify({
                    'code': 404,
                    'message': '任务不存在',
                    'data': None
                }), 404
            
            # 获取查询参数
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 20, type=int), 100)
            
            # 获取检测结果
            query = db.query(DetectionRecord).filter(DetectionRecord.task_id == task_id)
            
            total = query.count()
            results = query.order_by(DetectionRecord.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
            
            # 序列化数据
            results_data = []
            for result in results:
                results_data.append({
                    'id': result.id,
                    'website_id': result.website_id,
                    'website_name': result.website.name if result.website else 'N/A',
                    'website_url': result.website.url if result.website else 'N/A',
                    'status': result.status,
                    'response_time': result.response_time,
                    'http_status_code': result.http_status_code,
                    'final_url': result.final_url,
                    'error_message': result.error_message,
                    'created_at': result.created_at.isoformat()
                })
            
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': {
                    'results': results_data,
                    'pagination': {
                        'page': page,
                        'per_page': per_page,
                        'total': total,
                        'pages': (total - 1) // per_page + 1 if total > 0 else 0
                    }
                }
            })
        
    except Exception as e:
        logger.error(f"获取任务结果失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'获取任务结果失败: {str(e)}',
            'data': None
        }), 500