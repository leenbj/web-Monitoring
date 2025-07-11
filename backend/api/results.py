"""
网址监控工具 - 检测结果API路由
处理检测结果的查询和导出
"""

from flask import Blueprint, request, jsonify, send_file
from typing import Dict, List
from datetime import datetime, timedelta
import os

from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import Website, DetectionRecord, DetectionTask
from ..services.export_service import ExportService

import logging

logger = logging.getLogger(__name__)

bp = Blueprint('results', __name__, url_prefix='/api/results')


@bp.route('/', methods=['GET'])
def get_detection_results():
    """
    获取检测结果列表
    支持多种筛选条件
    """
    try:
        with get_db() as db:
            # 获取查询参数
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 20, type=int), 100)
        
            # 筛选条件
            task_id = request.args.get('task_id', type=int)
            website_id = request.args.get('website_id', type=int)
            status = request.args.get('status', type=str)
            start_date = request.args.get('start_date', type=str)
            end_date = request.args.get('end_date', type=str)
            search = request.args.get('search', '', type=str)
        
            # 构建查询
            query = db.query(DetectionRecord).join(Website)
        
            if task_id:
                query = query.filter(DetectionRecord.task_id == task_id)
            
            if website_id:
                query = query.filter(DetectionRecord.website_id == website_id)
            
            if status:
                query = query.filter(DetectionRecord.status == status)
        
            if start_date:
                try:
                    start_dt = datetime.fromisoformat(start_date)
                    query = query.filter(DetectionRecord.detected_at >= start_dt)
                except ValueError:
                    return jsonify({
                        'code': 400,
                        'message': '开始日期格式错误',
                        'data': None
                    }), 400
            
            if end_date:
                try:
                    end_dt = datetime.fromisoformat(end_date)
                    query = query.filter(DetectionRecord.detected_at <= end_dt)
                except ValueError:
                    return jsonify({
                        'code': 400,
                        'message': '结束日期格式错误',
                        'data': None
                    }), 400
        
            if search:
                query = query.filter(
                    Website.name.contains(search) | 
                    Website.url.contains(search)
                )
            
            # 分页
            total = query.count()
            records = query.order_by(DetectionRecord.detected_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
            
            # 序列化数据
            results_data = []
            for record in records:
                results_data.append({
                    'id': record.id,
                    'task_id': record.task_id,
                    'task_name': record.task.name if record.task else None,
                    'website_id': record.website_id,
                    'website_name': record.website.name,
                    'website_url': record.website.url,
                    'website_domain': record.website.url,  # 添加website_domain字段
                    'status': record.status,
                    'response_time': record.response_time,
                    'http_status_code': record.http_status_code,
                    'final_url': record.final_url,
                    'error_message': record.error_message,
                    'detected_at': record.detected_at.isoformat()
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
        logger.error(f"获取检测结果失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'获取检测结果失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/statistics', methods=['GET'])
def get_statistics():
    """
    获取检测结果统计信息
    根据最后一次检测结果统计网站状态
    """
    try:
        with get_db() as db:
            # 获取查询参数
            days = request.args.get('days', 7, type=int)
            website_ids = request.args.getlist('website_ids', type=int)
        
            # 计算时间范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
        
            # 构建基础查询（用于总检测次数统计）
            query = db.query(DetectionRecord).filter(
                DetectionRecord.detected_at >= start_date,
                DetectionRecord.detected_at <= end_date
            )
            
            if website_ids:
                query = query.filter(DetectionRecord.website_id.in_(website_ids))
        
            # 总检测次数统计（历史数据）
            total_count = query.count()
            
            # 平均响应时间（历史数据）
            avg_response_time = query.filter(
                DetectionRecord.response_time.isnot(None)
            ).with_entities(
                func.avg(DetectionRecord.response_time)
            ).scalar() or 0
            
            # 获取每个网站的最后一次检测结果（用于网站状态统计）
            subquery = db.query(
                DetectionRecord.website_id,
                func.max(DetectionRecord.detected_at).label('last_detected_at')
            ).group_by(DetectionRecord.website_id).subquery()
            
            latest_records_query = db.query(DetectionRecord).join(
                subquery,
                (DetectionRecord.website_id == subquery.c.website_id) &
                (DetectionRecord.detected_at == subquery.c.last_detected_at)
            )
            
            if website_ids:
                latest_records_query = latest_records_query.filter(
                    DetectionRecord.website_id.in_(website_ids)
                )
            
            latest_records = latest_records_query.all()
            
            # 根据最新检测结果统计网站状态
            status_counts = {'standard': 0, 'redirect': 0, 'failed': 0}
            for record in latest_records:
                if record.status in status_counts:
                    status_counts[record.status] += 1
        
            # 按日期统计
            daily_stats = query.with_entities(
                func.strftime('%Y-%m-%d', DetectionRecord.detected_at).label('date'),
                DetectionRecord.status,
                func.count(DetectionRecord.id).label('count')
            ).group_by(
                func.strftime('%Y-%m-%d', DetectionRecord.detected_at),
                DetectionRecord.status
            ).all()
            
            # 组织每日数据
            daily_data = {}
            for date_str, status, count in daily_stats:
                if date_str not in daily_data:
                    daily_data[date_str] = {'standard': 0, 'redirect': 0, 'failed': 0}
                daily_data[date_str][status] = count
        
            # 网站排行
            website_stats = query.join(Website).with_entities(
                Website.name,
                Website.url,
                DetectionRecord.status,
                func.count(DetectionRecord.id).label('count')
            ).group_by(
                Website.id,
                Website.name,
                Website.url,
                DetectionRecord.status
            ).all()
            
            # 组织网站数据
            website_data = {}
            for name, url, status, count in website_stats:
                key = f"{name}||{url}"
                if key not in website_data:
                    website_data[key] = {
                        'name': name,
                        'url': url,
                        'standard': 0,
                        'redirect': 0,
                        'failed': 0,
                        'total': 0
                    }
                website_data[key][status] = count
                website_data[key]['total'] += count
        
            # 计算可用率排行
            website_ranking = []
            for data in website_data.values():
                success_count = data['standard'] + data['redirect']
                availability = (success_count / data['total']) * 100 if data['total'] > 0 else 0
                website_ranking.append({
                    'name': data['name'],
                    'url': data['url'],
                    'total_checks': data['total'],
                    'availability': round(availability, 2),
                    'standard_count': data['standard'],
                    'redirect_count': data['redirect'],
                    'failed_count': data['failed']
                })
            
            # 按可用率排序
            website_ranking.sort(key=lambda x: x['availability'], reverse=True)
        
            # 计算网站数量统计
            total_websites = len(latest_records)
            success_websites = status_counts.get('standard', 0) + status_counts.get('redirect', 0)
            
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': {
                    'overview': {
                        'total_checks': total_count,  # 总检测次数（历史数据）
                        'total_websites': total_websites,  # 监控网站总数
                        'standard_count': status_counts.get('standard', 0),  # 正常访问网站数
                        'redirect_count': status_counts.get('redirect', 0),  # 跳转访问网站数  
                        'failed_count': status_counts.get('failed', 0),  # 无法访问网站数
                        'success_rate': round(
                            (success_websites / total_websites) * 100, 2
                        ) if total_websites > 0 else 0,  # 网站成功率（基于网站数量）
                        'avg_response_time': round(avg_response_time, 3)
                    },
                    'daily_stats': daily_data,
                    'website_ranking': website_ranking[:20],  # 只返回前20名
                    'time_range': {
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat(),
                        'days': days
                    }
                }
            })
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'获取统计信息失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/export', methods=['POST'])
def export_results():
    """
    导出检测结果
    """
    try:
        with get_db() as db:
            data = request.get_json() or {}
        
            # 获取导出参数
            export_format = data.get('format', 'excel')
            task_id = data.get('task_id')
            website_ids = data.get('website_ids')
            start_date_str = data.get('start_date')
            end_date_str = data.get('end_date')
            include_task_info = data.get('include_task_info', True)
            
            # 解析日期
            start_date = None
            end_date = None
            
            if start_date_str:
                try:
                    start_date = datetime.fromisoformat(start_date_str)
                except ValueError:
                    return jsonify({
                        'code': 400,
                        'message': '开始日期格式错误',
                        'data': None
                    }), 400
            
            if end_date_str:
                try:
                    end_date = datetime.fromisoformat(end_date_str)
                except ValueError:
                    return jsonify({
                        'code': 400,
                        'message': '结束日期格式错误',
                        'data': None
                    }), 400
        
            # 执行导出
            export_service = ExportService()
            result = export_service.export_detection_results(
                db=db,
                task_id=task_id,
                website_ids=website_ids,
                start_date=start_date,
                end_date=end_date,
                export_format=export_format,
                include_task_info=include_task_info
            )
            
            if result.success:
                logger.info(f"导出检测结果成功: {result.file_path}, 记录数: {result.record_count}")
                
                return jsonify({
                    'code': 200,
                    'message': f'导出成功，共 {result.record_count} 条记录',
                    'data': {
                        'file_path': result.file_path,
                        'record_count': result.record_count,
                        'export_time': result.export_time.isoformat(),
                        'download_url': f'/api/results/download/{os.path.basename(result.file_path)}'
                    }
                })
            else:
                return jsonify({
                    'code': 400,
                    'message': result.error_message,
                    'data': None
                }), 400
        
    except Exception as e:
        logger.error(f"导出检测结果失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'导出检测结果失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/export/statistics', methods=['POST'])
def export_statistics():
    """
    导出网站统计报告
    """
    try:
        with get_db() as db:
            data = request.get_json() or {}
        
            # 获取导出参数
            export_format = data.get('format', 'excel')
            website_ids = data.get('website_ids')
            days = data.get('days', 30)
            
            # 执行导出
            export_service = ExportService()
            result = export_service.export_website_statistics(
                db=db,
                website_ids=website_ids,
                days=days,
                export_format=export_format
            )
            
            if result.success:
                logger.info(f"导出统计报告成功: {result.file_path}, 网站数: {result.record_count}")
                
                return jsonify({
                    'code': 200,
                    'message': f'导出成功，共 {result.record_count} 个网站',
                    'data': {
                        'file_path': result.file_path,
                        'record_count': result.record_count,
                        'export_time': result.export_time.isoformat(),
                        'download_url': f'/api/results/download/{os.path.basename(result.file_path)}'
                    }
                })
            else:
                return jsonify({
                    'code': 400,
                    'message': result.error_message,
                    'data': None
                }), 400
        
    except Exception as e:
        logger.error(f"导出统计报告失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'导出统计报告失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/download/<filename>', methods=['GET'])
def download_file(filename: str):
    """
    下载导出文件并保存到用户文件
    """
    try:
        from ..models import UserFile
        from ..utils.helpers import get_beijing_time
        import shutil
        
        export_service = ExportService()
        file_path = os.path.join(export_service.download_dir, filename)
        
        if not os.path.exists(file_path):
            return jsonify({
                'code': 404,
                'message': '文件不存在',
                'data': None
            }), 404
        
        # 检查是否已保存到用户文件
        with get_db() as db:
            existing_user_file = db.query(UserFile).filter(
                UserFile.original_filename == filename,
                UserFile.source_type == 'download'
            ).first()
            
            if not existing_user_file:
                # 首次下载，复制到用户文件目录
                user_files_dir = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                    'user_files'
                )
                os.makedirs(user_files_dir, exist_ok=True)
                
                user_file_path = os.path.join(user_files_dir, filename)
                shutil.copy2(file_path, user_file_path)
                
                # 创建用户文件记录
                file_size = os.path.getsize(user_file_path)
                user_file = UserFile(
                    filename=filename,
                    original_filename=filename,
                    file_path=user_file_path,
                    file_size=file_size,
                    file_type=os.path.splitext(filename)[1].lower(),
                    source_type='download',
                    original_export_path=file_path,
                    download_count=1,
                    last_download_at=get_beijing_time(),
                    created_at=get_beijing_time()
                )
                db.add(user_file)
                db.commit()
                
                logger.info(f"首次下载，保存到用户文件: {filename}")
            else:
                # 更新下载统计
                existing_user_file.download_count += 1
                existing_user_file.last_download_at = get_beijing_time()
                db.commit()
                
                logger.info(f"更新下载统计: {filename}, 下载次数: {existing_user_file.download_count}")
        
        logger.info(f"下载文件: {filename}")
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"下载文件失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'下载文件失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/files', methods=['GET'])
def get_download_files():
    """
    获取可下载文件列表
    """
    try:
        export_service = ExportService()
        files = export_service.get_available_files()
        
        # 格式化文件信息
        files_data = []
        for file_info in files:
            files_data.append({
                'filename': file_info['filename'],
                'size': file_info['size'],
                'size_mb': round(file_info['size'] / 1024 / 1024, 2),
                'created_time': file_info['created_time'].isoformat(),
                'modified_time': file_info['modified_time'].isoformat(),
                'download_url': f'/api/results/download/{file_info["filename"]}'
            })
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'files': files_data,
                'total': len(files_data)
            }
        })
        
    except Exception as e:
        logger.error(f"获取下载文件列表失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'获取下载文件列表失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/files/<filename>', methods=['DELETE'])
def delete_download_file(filename: str):
    """
    删除下载文件
    """
    try:
        export_service = ExportService()
        success = export_service.delete_file(filename)
        
        if success:
            logger.info(f"删除下载文件成功: {filename}")
            return jsonify({
                'code': 200,
                'message': '删除成功',
                'data': None
            })
        else:
            return jsonify({
                'code': 404,
                'message': '文件不存在',
                'data': None
            }), 404
        
    except Exception as e:
        logger.error(f"删除下载文件失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'删除下载文件失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/files/cleanup', methods=['POST'])
def cleanup_old_files():
    """
    清理旧的下载文件
    """
    try:
        data = request.get_json() or {}
        days = data.get('days', 7)
        
        export_service = ExportService()
        deleted_count = export_service.cleanup_old_files(days)
        
        logger.info(f"清理旧文件完成: 删除了 {deleted_count} 个文件")
        
        return jsonify({
            'code': 200,
            'message': f'清理完成，删除了 {deleted_count} 个文件',
            'data': {
                'deleted_count': deleted_count,
                'retention_days': days
            }
        })
        
    except Exception as e:
        logger.error(f"清理旧文件失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'清理旧文件失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/clear-old-data', methods=['DELETE'])
def clear_old_detection_data():
    """
    清除检测数据
    - 当传递retain_days参数且大于0时，只保留指定天数内的检测记录
    - 当不传递参数或retain_days为0时，清除所有检测记录
    """
    try:
        with get_db() as db:
            # 获取保留天数参数，默认为0（清除所有数据）
            retain_days = request.args.get('retain_days', 0, type=int)
            
            if retain_days < 0:
                return jsonify({
                    'code': 400,
                    'message': '保留天数不能为负数',
                    'data': None
                }), 400
            
            # 查询要删除的记录数量
            if retain_days == 0:
                # 清除所有数据
                records_to_delete = db.query(DetectionRecord).count()
                
                if records_to_delete == 0:
                    return jsonify({
                        'code': 200,
                        'message': '没有检测数据需要清理',
                        'data': {
                            'deleted_count': 0,
                            'retain_days': retain_days,
                            'is_clear_all': True
                        }
                    })
                
                # 删除所有检测记录
                deleted_count = db.query(DetectionRecord).delete()
                
                # 同时删除所有状态变化记录
                from ..models import WebsiteStatusChange
                status_changes_deleted = db.query(WebsiteStatusChange).delete()
                
                db.commit()
                
                logger.info(f"清除所有检测数据完成: 删除了 {deleted_count} 条检测记录和 {status_changes_deleted} 条状态变化记录")
                
                return jsonify({
                    'code': 200,
                    'message': f'清除完成，删除了 {deleted_count} 条检测记录',
                    'data': {
                        'deleted_count': deleted_count,
                        'status_changes_deleted': status_changes_deleted,
                        'retain_days': retain_days,
                        'is_clear_all': True
                    }
                })
            else:
                # 只删除过期数据
                cutoff_date = datetime.now() - timedelta(days=retain_days)
                
                records_to_delete = db.query(DetectionRecord).filter(
                    DetectionRecord.detected_at < cutoff_date
                ).count()
                
                if records_to_delete == 0:
                    return jsonify({
                        'code': 200,
                        'message': f'没有超过{retain_days}天的过期数据需要清理',
                        'data': {
                            'deleted_count': 0,
                            'retain_days': retain_days,
                            'cutoff_date': cutoff_date.isoformat(),
                            'is_clear_all': False
                        }
                    })
                
                # 删除过期的检测记录
                deleted_count = db.query(DetectionRecord).filter(
                    DetectionRecord.detected_at < cutoff_date
                ).delete()
                
                # 同时删除相关的状态变化记录
                from ..models import WebsiteStatusChange
                status_changes_deleted = db.query(WebsiteStatusChange).filter(
                    WebsiteStatusChange.detected_at < cutoff_date
                ).delete()
                
                db.commit()
                
                logger.info(f"清除过期检测数据完成: 删除了 {deleted_count} 条检测记录和 {status_changes_deleted} 条状态变化记录")
                
                return jsonify({
                    'code': 200,
                    'message': f'清除完成，删除了 {deleted_count} 条检测记录',
                    'data': {
                        'deleted_count': deleted_count,
                        'status_changes_deleted': status_changes_deleted,
                        'retain_days': retain_days,
                        'cutoff_date': cutoff_date.isoformat(),
                        'is_clear_all': False
                    }
                })
            
    except Exception as e:
        logger.error(f"清除检测数据失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'清除检测数据失败: {str(e)}',
            'data': None
        }), 500