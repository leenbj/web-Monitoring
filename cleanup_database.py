#!/usr/bin/env python3
"""
数据库清理脚本
用于清理旧的检测记录，减少数据库大小和查询负载
"""

import sys
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.database import get_db
from backend.models import DetectionRecord, UploadRecord, UserFile


class DatabaseCleaner:
    """数据库清理器"""
    
    def __init__(self):
        self.db_path = Path(__file__).parent / "database" / "website_monitor.db"
        self.stats = {
            'deleted_records': 0,
            'deleted_uploads': 0,
            'deleted_files': 0,
            'space_saved_mb': 0
        }
    
    def get_database_size(self):
        """获取数据库文件大小"""
        if self.db_path.exists():
            return self.db_path.stat().st_size / 1024 / 1024  # MB
        return 0
    
    def clean_old_detection_records(self, days=30):
        """清理旧的检测记录"""
        print(f"正在清理 {days} 天前的检测记录...")
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        try:
            with get_db() as db:
                # 查询要删除的记录数
                old_records = db.query(DetectionRecord).filter(
                    DetectionRecord.detected_at < cutoff_date
                ).all()
                
                count = len(old_records)
                if count == 0:
                    print("  没有需要清理的检测记录")
                    return
                
                # 删除记录
                db.query(DetectionRecord).filter(
                    DetectionRecord.detected_at < cutoff_date
                ).delete()
                
                db.commit()
                self.stats['deleted_records'] = count
                print(f"  已删除 {count} 条检测记录")
                
        except Exception as e:
            print(f"  清理检测记录失败: {e}")
    
    def clean_old_upload_records(self, days=7):
        """清理旧的上传记录"""
        print(f"正在清理 {days} 天前的上传记录...")
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        try:
            with get_db() as db:
                # 查询要删除的记录数
                old_uploads = db.query(UploadRecord).filter(
                    UploadRecord.uploaded_at < cutoff_date
                ).all()
                
                count = len(old_uploads)
                if count == 0:
                    print("  没有需要清理的上传记录")
                    return
                
                # 删除相关文件
                uploads_dir = Path(__file__).parent / "uploads"
                for record in old_uploads:
                    if record.file_path:
                        file_path = Path(record.file_path)
                        if file_path.exists():
                            try:
                                file_path.unlink()
                                print(f"    删除文件: {file_path.name}")
                            except Exception as e:
                                print(f"    删除文件失败 {file_path.name}: {e}")
                
                # 删除数据库记录
                db.query(UploadRecord).filter(
                    UploadRecord.uploaded_at < cutoff_date
                ).delete()
                
                db.commit()
                self.stats['deleted_uploads'] = count
                print(f"  已删除 {count} 条上传记录")
                
        except Exception as e:
            print(f"  清理上传记录失败: {e}")
    
    def clean_old_user_files(self, days=7):
        """清理旧的用户文件"""
        print(f"正在清理 {days} 天前的用户文件...")
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        try:
            with get_db() as db:
                # 查询要删除的文件记录
                old_files = db.query(UserFile).filter(
                    UserFile.created_at < cutoff_date
                ).all()
                
                count = len(old_files)
                if count == 0:
                    print("  没有需要清理的用户文件")
                    return
                
                # 删除相关文件
                for record in old_files:
                    if record.file_path:
                        file_path = Path(record.file_path)
                        if file_path.exists():
                            try:
                                file_path.unlink()
                                print(f"    删除文件: {file_path.name}")
                            except Exception as e:
                                print(f"    删除文件失败 {file_path.name}: {e}")
                
                # 删除数据库记录
                db.query(UserFile).filter(
                    UserFile.created_at < cutoff_date
                ).delete()
                
                db.commit()
                self.stats['deleted_files'] = count
                print(f"  已删除 {count} 条用户文件记录")
                
        except Exception as e:
            print(f"  清理用户文件失败: {e}")
    
    def vacuum_database(self):
        """压缩数据库"""
        print("正在压缩数据库...")
        
        try:
            # 直接使用sqlite3连接进行VACUUM操作
            conn = sqlite3.connect(str(self.db_path))
            conn.execute("VACUUM")
            conn.close()
            print("  数据库压缩完成")
        except Exception as e:
            print(f"  数据库压缩失败: {e}")
    
    def analyze_tables(self):
        """分析表统计信息"""
        print("正在分析表统计信息...")
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # 获取所有表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            print("\n  表统计信息:")
            total_records = 0
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                total_records += count
                print(f"    {table}: {count:,} 条记录")
            
            print(f"  总记录数: {total_records:,}")
            conn.close()
            
        except Exception as e:
            print(f"  分析表统计信息失败: {e}")
    
    def full_cleanup(self):
        """执行完整清理"""
        print("开始执行完整数据库清理...")
        print("="*50)
        
        # 记录清理前的数据库大小
        initial_size = self.get_database_size()
        print(f"清理前数据库大小: {initial_size:.2f} MB")
        print()
        
        # 执行各种清理操作
        self.clean_old_detection_records(days=30)  # 清理30天前的检测记录
        self.clean_old_upload_records(days=7)      # 清理7天前的上传记录
        self.clean_old_user_files(days=7)          # 清理7天前的用户文件
        
        # 压缩数据库
        self.vacuum_database()
        
        # 分析表统计信息
        self.analyze_tables()
        
        # 计算清理后的数据库大小
        final_size = self.get_database_size()
        self.stats['space_saved_mb'] = initial_size - final_size
        
        # 输出清理报告
        print("\n" + "="*50)
        print("清理完成！")
        print(f"清理后数据库大小: {final_size:.2f} MB")
        print(f"节省空间: {self.stats['space_saved_mb']:.2f} MB")
        print(f"删除检测记录: {self.stats['deleted_records']} 条")
        print(f"删除上传记录: {self.stats['deleted_uploads']} 条")
        print(f"删除用户文件: {self.stats['deleted_files']} 条")


def main():
    """主函数"""
    cleaner = DatabaseCleaner()
    
    print("数据库清理工具")
    print("1. 完整清理 (推荐)")
    print("2. 只清理检测记录")
    print("3. 只清理上传文件")
    print("4. 只压缩数据库")
    print("5. 只分析统计信息")
    
    choice = input("\n请选择操作 (1-5): ").strip()
    
    if choice == "1":
        confirm = input("确定要执行完整清理吗？这将删除旧数据 (y/N): ").strip().lower()
        if confirm == 'y':
            cleaner.full_cleanup()
        else:
            print("已取消")
    
    elif choice == "2":
        days = input("请输入要保留的天数 (默认30): ").strip()
        days = int(days) if days.isdigit() else 30
        cleaner.clean_old_detection_records(days)
        cleaner.vacuum_database()
    
    elif choice == "3":
        days = input("请输入要保留的天数 (默认7): ").strip()
        days = int(days) if days.isdigit() else 7
        cleaner.clean_old_upload_records(days)
        cleaner.clean_old_user_files(days)
        cleaner.vacuum_database()
    
    elif choice == "4":
        cleaner.vacuum_database()
    
    elif choice == "5":
        cleaner.analyze_tables()
    
    else:
        print("无效选择")


if __name__ == "__main__":
    main()