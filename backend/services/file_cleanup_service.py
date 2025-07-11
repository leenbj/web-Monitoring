"""
文件清理服务
负责清理过期的系统文件，保留用户文件
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

from ..database import get_db
from ..models import UserFile
from ..utils.helpers import get_beijing_time

logger = logging.getLogger(__name__)


class FileCleanupService:
    """文件清理服务"""
    
    def __init__(self, project_root: str = None):
        """
        初始化清理服务
        
        Args:
            project_root: 项目根目录
        """
        if project_root is None:
            # 获取项目根目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            
        self.project_root = project_root
        self.downloads_dir = os.path.join(project_root, "downloads")
        self.user_files_dir = os.path.join(project_root, "user_files")
        
        # 确保目录存在
        os.makedirs(self.downloads_dir, exist_ok=True)
        os.makedirs(self.user_files_dir, exist_ok=True)
        
        logger.info(f"文件清理服务初始化完成")
        logger.info(f"系统文件目录: {self.downloads_dir}")
        logger.info(f"用户文件目录: {self.user_files_dir}")
    
    def cleanup_old_files(self, retention_days: int = 30) -> Dict[str, int]:
        """
        清理旧文件
        
        Args:
            retention_days: 保留天数，默认30天
            
        Returns:
            清理结果统计
        """
        result = {
            'system_files_deleted': 0,
            'orphaned_user_files_deleted': 0,
            'total_size_freed': 0
        }
        
        try:
            cutoff_time = datetime.now() - timedelta(days=retention_days)
            
            # 清理系统导出文件
            system_result = self._cleanup_system_files(cutoff_time)
            result['system_files_deleted'] = system_result['count']
            result['total_size_freed'] += system_result['size']
            
            # 清理孤立的用户文件（文件不存在但数据库记录存在）
            orphaned_result = self._cleanup_orphaned_user_files()
            result['orphaned_user_files_deleted'] = orphaned_result['count']
            
            logger.info(f"文件清理完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"文件清理失败: {e}")
            return result
    
    def _cleanup_system_files(self, cutoff_time: datetime) -> Dict[str, int]:
        """
        清理系统导出文件
        
        Args:
            cutoff_time: 截止时间
            
        Returns:
            清理结果
        """
        result = {'count': 0, 'size': 0}
        
        try:
            if not os.path.exists(self.downloads_dir):
                return result
            
            with get_db() as db:
                # 获取所有用户已保存的文件，避免误删
                user_files = db.query(UserFile).filter(
                    UserFile.source_type == 'download'
                ).all()
                protected_files = {uf.original_filename for uf in user_files}
            
            for filename in os.listdir(self.downloads_dir):
                file_path = os.path.join(self.downloads_dir, filename)
                
                if not os.path.isfile(file_path):
                    continue
                
                # 跳过用户已保存的文件
                if filename in protected_files:
                    logger.debug(f"跳过用户保存的文件: {filename}")
                    continue
                
                # 检查文件修改时间
                modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                if modified_time < cutoff_time:
                    file_size = os.path.getsize(file_path)
                    os.remove(file_path)
                    result['count'] += 1
                    result['size'] += file_size
                    logger.info(f"清理系统文件: {filename}, 大小: {file_size} bytes")
            
            return result
            
        except Exception as e:
            logger.error(f"清理系统文件失败: {e}")
            return result
    
    def _cleanup_orphaned_user_files(self) -> Dict[str, int]:
        """
        清理孤立的用户文件记录（文件不存在但数据库记录存在）
        
        Returns:
            清理结果
        """
        result = {'count': 0}
        
        try:
            with get_db() as db:
                user_files = db.query(UserFile).all()
                
                for user_file in user_files:
                    if not os.path.exists(user_file.file_path):
                        logger.info(f"清理孤立记录: {user_file.original_filename}")
                        db.delete(user_file)
                        result['count'] += 1
                
                db.commit()
            
            return result
            
        except Exception as e:
            logger.error(f"清理孤立文件记录失败: {e}")
            return result
    
    def get_cleanup_stats(self) -> Dict[str, any]:
        """
        获取清理统计信息
        
        Returns:
            统计信息
        """
        stats = {
            'system_files': {'count': 0, 'total_size': 0},
            'user_files': {'count': 0, 'total_size': 0},
            'can_cleanup': {'count': 0, 'total_size': 0}
        }
        
        try:
            cutoff_time = datetime.now() - timedelta(days=30)
            
            # 统计系统文件
            if os.path.exists(self.downloads_dir):
                with get_db() as db:
                    user_files = db.query(UserFile).filter(
                        UserFile.source_type == 'download'
                    ).all()
                    protected_files = {uf.original_filename for uf in user_files}
                
                for filename in os.listdir(self.downloads_dir):
                    file_path = os.path.join(self.downloads_dir, filename)
                    if os.path.isfile(file_path):
                        file_size = os.path.getsize(file_path)
                        stats['system_files']['count'] += 1
                        stats['system_files']['total_size'] += file_size
                        
                        # 检查是否可以清理
                        if filename not in protected_files:
                            modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                            if modified_time < cutoff_time:
                                stats['can_cleanup']['count'] += 1
                                stats['can_cleanup']['total_size'] += file_size
            
            # 统计用户文件
            with get_db() as db:
                user_files = db.query(UserFile).all()
                for user_file in user_files:
                    stats['user_files']['count'] += 1
                    stats['user_files']['total_size'] += user_file.file_size or 0
            
            return stats
            
        except Exception as e:
            logger.error(f"获取清理统计失败: {e}")
            return stats
    
    def schedule_cleanup(self) -> bool:
        """
        执行定期清理
        
        Returns:
            是否成功
        """
        try:
            logger.info("开始执行定期文件清理")
            result = self.cleanup_old_files(retention_days=30)
            
            if result['system_files_deleted'] > 0 or result['orphaned_user_files_deleted'] > 0:
                logger.info(f"定期清理完成: 删除系统文件 {result['system_files_deleted']} 个, "
                           f"清理孤立记录 {result['orphaned_user_files_deleted']} 个, "
                           f"释放空间 {result['total_size_freed']} bytes")
            else:
                logger.info("定期清理完成: 无需清理的文件")
            
            return True
            
        except Exception as e:
            logger.error(f"定期清理失败: {e}")
            return False 