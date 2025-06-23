"""
网址监控工具 - 结果导出服务
支持多种格式的检测结果导出
"""

import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import csv
from pathlib import Path

import logging

logger = logging.getLogger(__name__)
from sqlalchemy.orm import Session

from ..models import Website, DetectionRecord, DetectionTask
from ..utils.helpers import ensure_dir, format_datetime


class ExportResult:
    """导出结果类"""
    
    def __init__(self, success: bool = False, file_path: str = None, 
                 error_message: str = None, record_count: int = 0):
        self.success = success
        self.file_path = file_path
        self.error_message = error_message
        self.record_count = record_count
        self.export_time = datetime.now()


class ExportService:
    """结果导出服务"""
    
    def __init__(self, download_dir: str = None):
        """
        初始化导出服务
        
        Args:
            download_dir: 下载文件保存目录
        """
        if download_dir is None:
            # 获取项目根目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            download_dir = os.path.join(project_root, "downloads")
            
        self.download_dir = download_dir
        ensure_dir(self.download_dir)
        
        logger.info(f"导出服务初始化完成，下载目录: {self.download_dir}")
    
    def export_detection_results(self, db: Session, 
                                task_id: Optional[int] = None,
                                website_ids: List[int] = None,
                                start_date: Optional[datetime] = None,
                                end_date: Optional[datetime] = None,
                                export_format: str = 'excel',
                                include_task_info: bool = True) -> ExportResult:
        """
        导出检测结果
        
        Args:
            db: 数据库会话
            task_id: 任务ID（可选）
            website_ids: 网站ID列表（可选）
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            export_format: 导出格式 ('excel', 'csv', 'json')
            include_task_info: 是否包含任务信息
            
        Returns:
            导出结果
        """
        try:
            # 构建查询
            query = db.query(DetectionRecord).join(Website)
            
            if task_id:
                query = query.filter(DetectionRecord.task_id == task_id)
            
            if website_ids:
                query = query.filter(Website.id.in_(website_ids))
            
            if start_date:
                query = query.filter(DetectionRecord.detected_at >= start_date)
            
            if end_date:
                query = query.filter(DetectionRecord.detected_at <= end_date)
            
            # 执行查询
            records = query.order_by(DetectionRecord.detected_at.desc()).all()
            
            if not records:
                return ExportResult(False, None, "没有找到匹配的检测记录", 0)
            
            # 准备数据
            data = self._prepare_export_data(records, include_task_info)
            
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"网址检测结果_{timestamp}"
            
            # 根据格式导出
            if export_format.lower() == 'excel':
                file_path = self._export_to_excel(data, filename)
            elif export_format.lower() == 'csv':
                file_path = self._export_to_csv(data, filename)
            elif export_format.lower() == 'json':
                file_path = self._export_to_json(data, filename)
            else:
                return ExportResult(False, None, f"不支持的导出格式: {export_format}", 0)
            
            logger.info(f"导出完成: {file_path}, 记录数: {len(records)}")
            return ExportResult(True, file_path, None, len(records))
            
        except Exception as e:
            logger.error(f"导出检测结果失败: {e}")
            return ExportResult(False, None, str(e), 0)
    
    def _prepare_export_data(self, records: List[DetectionRecord], 
                           include_task_info: bool = True) -> List[Dict]:
        """准备导出数据"""
        data = []
        for record in records:
            row = {
                '网站名称': record.website.name,
                '网址': record.website.url,
                '检测时间': format_datetime(record.detected_at),
                '检测状态': self._get_status_name(record.status),
                '响应时间(秒)': round(record.response_time, 2) if record.response_time else None,
                '状态码': record.http_status_code,
                '最终URL': record.final_url,
                '错误信息': record.error_message
            }
            
            # 暂时禁用任务信息以避免错误
            # if include_task_info and record.task:
            #     row['任务名称'] = record.task.name
            #     row['任务描述'] = getattr(record.task, 'description', '')
            
            data.append(row)
        
        return data
    
    def _get_status_name(self, status: str) -> str:
        """获取状态中文名称"""
        status_map = {
            'standard': '标准解析',
            'redirect': '跳转解析',
            'failed': '无法访问'
        }
        return status_map.get(status, status)
    
    def _export_to_excel(self, data: List[Dict], filename: str) -> str:
        """导出到Excel"""
        file_path = os.path.join(self.download_dir, f"{filename}.xlsx")
        
        df = pd.DataFrame(data)
        
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='检测结果', index=False)
            
            # 调整列宽
            worksheet = writer.sheets['检测结果']
            for column in worksheet.columns:
                max_length = max(len(str(cell.value)) for cell in column)
                worksheet.column_dimensions[column[0].column_letter].width = min(max_length + 2, 50)
        
        return file_path
    
    def _export_to_csv(self, data: List[Dict], filename: str) -> str:
        """导出到CSV"""
        file_path = os.path.join(self.download_dir, f"{filename}.csv")
        
        df = pd.DataFrame(data)
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        
        return file_path
    
    def _export_to_json(self, data: List[Dict], filename: str) -> str:
        """导出到JSON"""
        file_path = os.path.join(self.download_dir, f"{filename}.json")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        return file_path
    
    def export_website_statistics(self, db: Session,
                                 website_ids: List[int] = None,
                                 days: int = 30,
                                 export_format: str = 'excel') -> ExportResult:
        """
        导出网站统计数据
        
        Args:
            db: 数据库会话
            website_ids: 网站ID列表（可选）
            days: 统计天数
            export_format: 导出格式
            
        Returns:
            导出结果
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # 获取网站列表
            websites_query = db.query(Website)
            if website_ids:
                websites_query = websites_query.filter(Website.id.in_(website_ids))
            
            websites = websites_query.all()
            
            if not websites:
                return ExportResult(False, None, "没有找到匹配的网站", 0)
            
            # 计算统计数据
            stats_data = []
            for website in websites:
                stats = self._calculate_website_statistics(db, website, start_date, end_date)
                stats_data.append(stats)
            
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"网站统计报告_{days}天_{timestamp}"
            
            # 导出
            if export_format.lower() == 'excel':
                file_path = self._export_statistics_to_excel(stats_data, filename, days)
            elif export_format.lower() == 'csv':
                file_path = self._export_statistics_to_csv(stats_data, filename)
            else:
                return ExportResult(False, None, f"不支持的导出格式: {export_format}", 0)
            
            logger.info(f"统计报告导出完成: {file_path}, 网站数: {len(websites)}")
            return ExportResult(True, file_path, None, len(websites))
            
        except Exception as e:
            logger.error(f"导出网站统计失败: {e}")
            return ExportResult(False, None, str(e), 0)
    
    def _calculate_website_statistics(self, db: Session, website: Website, 
                                    start_date: datetime, end_date: datetime) -> Dict:
        """计算网站统计数据"""
        records = db.query(DetectionRecord).filter(
            DetectionRecord.website_id == website.id,
            DetectionRecord.detected_at >= start_date,
            DetectionRecord.detected_at <= end_date
        ).all()
        
        total_count = len(records)
        if total_count == 0:
            return {
                '网站名称': website.name,
                '网址': website.url,
                '总检测次数': 0,
                '标准解析次数': 0,
                '跳转解析次数': 0,
                '失败次数': 0,
                '可用率(%)': 0,
                '平均响应时间(秒)': 0
            }
        
        status_counts = {}
        total_response_time = 0
        valid_response_count = 0
        
        for record in records:
            status = record.status
            status_counts[status] = status_counts.get(status, 0) + 1
            
            if record.response_time:
                total_response_time += record.response_time
                valid_response_count += 1
        
        success_count = status_counts.get('standard', 0) + status_counts.get('redirect', 0)
        availability = (success_count / total_count) * 100 if total_count > 0 else 0
        avg_response_time = total_response_time / valid_response_count if valid_response_count > 0 else 0
        
        return {
            '网站名称': website.name,
            '网址': website.url,
            '总检测次数': total_count,
            '标准解析次数': status_counts.get('standard', 0),
            '跳转解析次数': status_counts.get('redirect', 0),
            '失败次数': status_counts.get('failed', 0),
            '可用率(%)': round(availability, 2),
                            '平均响应时间(秒)': round(avg_response_time, 2)
        }
    
    def _export_statistics_to_excel(self, stats_data: List[Dict], 
                                   filename: str, days: int) -> str:
        """导出统计数据到Excel"""
        file_path = os.path.join(self.download_dir, f"{filename}.xlsx")
        
        df = pd.DataFrame(stats_data)
        
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=f'统计报告({days}天)', index=False)
            
            # 调整列宽
            worksheet = writer.sheets[f'统计报告({days}天)']
            for column in worksheet.columns:
                max_length = max(len(str(cell.value)) for cell in column)
                worksheet.column_dimensions[column[0].column_letter].width = min(max_length + 2, 50)
        
        return file_path
    
    def _export_statistics_to_csv(self, stats_data: List[Dict], filename: str) -> str:
        """导出统计数据到CSV"""
        file_path = os.path.join(self.download_dir, f"{filename}.csv")
        
        df = pd.DataFrame(stats_data)
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        
        return file_path
    
    def get_available_files(self) -> List[Dict]:
        """
        获取可用的下载文件列表
        
        Returns:
            文件信息列表
        """
        files = []
        try:
            for filename in os.listdir(self.download_dir):
                file_path = os.path.join(self.download_dir, filename)
                if os.path.isfile(file_path):
                    stat = os.stat(file_path)
                    files.append({
                        'filename': filename,
                        'size': stat.st_size,
                        'created_time': datetime.fromtimestamp(stat.st_ctime),
                        'modified_time': datetime.fromtimestamp(stat.st_mtime)
                    })
            
            # 按修改时间倒序排列
            files.sort(key=lambda x: x['modified_time'], reverse=True)
            
        except Exception as e:
            logger.error(f"获取文件列表失败: {e}")
        
        return files
    
    def delete_file(self, filename: str) -> bool:
        """
        删除下载文件
        
        Args:
            filename: 文件名
            
        Returns:
            是否删除成功
        """
        try:
            file_path = os.path.join(self.download_dir, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"文件删除成功: {filename}")
                return True
            else:
                logger.warning(f"文件不存在: {filename}")
                return False
                
        except Exception as e:
            logger.error(f"删除文件失败: {filename}, 错误: {e}")
            return False
    
    def cleanup_old_files(self, days: int = 7) -> int:
        """
        清理旧文件
        
        Args:
            days: 保留天数
            
        Returns:
            删除的文件数量
        """
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            deleted_count = 0
            
            for filename in os.listdir(self.download_dir):
                file_path = os.path.join(self.download_dir, filename)
                if os.path.isfile(file_path):
                    modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if modified_time < cutoff_time:
                        os.remove(file_path)
                        deleted_count += 1
                        logger.info(f"清理旧文件: {filename}")
            
            logger.info(f"清理完成，删除了 {deleted_count} 个文件")
            return deleted_count
            
        except Exception as e:
            logger.error(f"清理旧文件失败: {e}")
            return 0