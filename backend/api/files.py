"""
文件管理API
提供文件上传、下载、删除等功能
"""

import os
import logging
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from datetime import datetime

from ..database import get_db
from ..models import UploadRecord, UserFile
from ..services.export_service import ExportService
from ..services.file_cleanup_service import FileCleanupService
from ..utils.helpers import get_beijing_time

logger = logging.getLogger(__name__)

bp = Blueprint('files', __name__, url_prefix='/api/files')

# 配置 - 使用绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
UPLOAD_FOLDER = os.path.join(project_root, 'uploads')
USER_FILES_FOLDER = os.path.join(project_root, 'user_files')
DOWNLOAD_FOLDER = os.path.join(project_root, 'downloads')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'xlsx', 'xls', 'csv'}

# 确保目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(USER_FILES_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route('/', methods=['GET'])
def get_file_list():
    """
    获取用户文件列表（只显示用户上传和手动下载的文件）
    """
    try:
        with get_db() as db:
            # 获取所有用户文件记录
            user_files = db.query(UserFile).order_by(UserFile.created_at.desc()).all()
            
            files_data = []
            for user_file in user_files:
                # 检查文件是否还存在
                if os.path.exists(user_file.file_path):
                    files_data.append({
                        'id': user_file.id,
                        'filename': user_file.original_filename,
                        'size': user_file.file_size,
                        'created_at': user_file.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'type': 'upload' if user_file.source_type == 'upload' else 'download',
                        'download_count': user_file.download_count if user_file.source_type == 'download' else 0,
                        'last_download_at': user_file.last_download_at.strftime('%Y-%m-%d %H:%M:%S') if user_file.last_download_at else None
                    })
                else:
                    # 文件不存在，删除数据库记录
                    logger.warning(f"文件不存在，删除记录: {user_file.original_filename}")
                    db.delete(user_file)
            
            db.commit()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'files': files_data,
                'total': len(files_data)
            }
        })
        
    except Exception as e:
        logger.error(f"获取文件列表失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'获取文件列表失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/upload', methods=['POST'])
def upload_file():
    """
    上传文件
    """
    try:
        if 'file' not in request.files:
            return jsonify({
                'code': 400,
                'message': '没有上传文件',
                'data': None
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'code': 400,
                'message': '文件名不能为空',
                'data': None
            }), 400
        
        if file and allowed_file(file.filename):
            # 生成安全的文件名
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            name, ext = os.path.splitext(filename)
            safe_filename = f"{name}_{timestamp}{ext}"
            
            # 保存文件到用户文件目录
            file_path = os.path.join(USER_FILES_FOLDER, safe_filename)
            file.save(file_path)
            
            file_size = os.path.getsize(file_path)
            
            # 记录到数据库
            with get_db() as db:
                # 保留原有的上传记录
                upload_record = UploadRecord(
                    filename=safe_filename,
                    original_filename=filename,
                    file_path=file_path,
                    file_size=file_size,
                    file_type=ext.lower(),
                    status='completed',
                    uploaded_at=get_beijing_time()
                )
                db.add(upload_record)
                
                # 添加用户文件记录
                user_file = UserFile(
                    filename=safe_filename,
                    original_filename=filename,
                    file_path=file_path,
                    file_size=file_size,
                    file_type=ext.lower(),
                    source_type='upload',
                    created_at=get_beijing_time()
                )
                db.add(user_file)
                db.commit()
            
            logger.info(f"文件上传成功: {safe_filename}")
            
            return jsonify({
                'code': 200,
                'message': '文件上传成功',
                'data': {
                    'filename': safe_filename,
                    'original_filename': filename,
                    'file_size': file_size
                }
            })
        else:
            return jsonify({
                'code': 400,
                'message': '文件格式不支持',
                'data': None
            }), 400
            
    except Exception as e:
        logger.error(f"文件上传失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'文件上传失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/download/<path:filename>', methods=['GET'])
def download_file(filename):
    """
    下载文件
    """
    try:
        # URL解码文件名以支持中文
        import urllib.parse
        original_filename = urllib.parse.unquote(filename)
        
        # 对于路径遍历的安全检查
        if '..' in original_filename or '/' in original_filename or '\\' in original_filename:
            return jsonify({
                'code': 400,
                'message': '文件名包含非法字符',
                'data': None
            }), 400
        
        logger.info(f"下载文件请求: 文件名={original_filename}")
        logger.info(f"下载目录: {DOWNLOAD_FOLDER}")
        logger.info(f"上传目录: {UPLOAD_FOLDER}")
        
        # 首先从用户文件数据库中查找
        with get_db() as db:
            user_file = db.query(UserFile).filter(UserFile.original_filename == original_filename).first()
            
            if user_file and os.path.exists(user_file.file_path):
                logger.info(f"从用户文件发送: {user_file.file_path}")
                
                # 如果是下载类型文件，更新下载统计
                if user_file.source_type == 'download':
                    user_file.download_count += 1
                    user_file.last_download_at = get_beijing_time()
                    db.commit()
                
                return send_file(user_file.file_path, as_attachment=True, download_name=original_filename)
        
        # 如果不是用户文件，检查是否为系统导出文件（临时下载）
        download_path = os.path.join(DOWNLOAD_FOLDER, original_filename)
        logger.info(f"检查系统导出路径: {download_path}, 存在: {os.path.exists(download_path)}")
        
        if os.path.exists(download_path):
            logger.info(f"从系统导出目录发送文件: {download_path}")
            return send_file(download_path, as_attachment=True, download_name=original_filename)
        
        # 如果都找不到，列出目录内容进行调试
        logger.warning(f"文件不存在，目录内容:")
        if os.path.exists(DOWNLOAD_FOLDER):
            logger.warning(f"下载目录内容: {os.listdir(DOWNLOAD_FOLDER)}")
        if os.path.exists(UPLOAD_FOLDER):
            logger.warning(f"上传目录内容: {os.listdir(UPLOAD_FOLDER)}")
        
        return jsonify({
            'code': 404,
            'message': '文件不存在',
            'data': None
        }), 404
        
    except Exception as e:
        logger.error(f"下载文件失败: {filename}, 错误: {e}")
        return jsonify({
            'code': 500,
            'message': f'下载文件失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/<path:filename>', methods=['DELETE'])
def delete_file(filename):
    """
    删除文件
    """
    try:
        # URL解码文件名以支持中文
        import urllib.parse
        original_filename = urllib.parse.unquote(filename)
        
        # 对于路径遍历的安全检查
        if '..' in original_filename or '/' in original_filename or '\\' in original_filename:
            return jsonify({
                'code': 400,
                'message': '文件名包含非法字符',
                'data': None
            }), 400
            
        deleted = False
        
        # 从用户文件数据库中查找并删除
        with get_db() as db:
            user_file = db.query(UserFile).filter(UserFile.original_filename == original_filename).first()
            
            if user_file:
                # 删除物理文件
                if os.path.exists(user_file.file_path):
                    os.remove(user_file.file_path)
                    logger.info(f"删除用户文件: {user_file.file_path}")
                
                # 删除数据库记录
                db.delete(user_file)
                
                # 如果是上传文件，也删除上传记录
                if user_file.source_type == 'upload':
                    upload_record = db.query(UploadRecord).filter(UploadRecord.filename == user_file.filename).first()
                    if upload_record:
                        db.delete(upload_record)
                
                db.commit()
                deleted = True
                logger.info(f"删除用户文件记录: {original_filename}")
        
        if deleted:
            return jsonify({
                'code': 200,
                'message': '文件删除成功',
                'data': None
            })
        else:
            return jsonify({
                'code': 404,
                'message': '文件不存在',
                'data': None
            }), 404
            
    except Exception as e:
        logger.error(f"删除文件失败: {filename}, 错误: {e}")
        return jsonify({
            'code': 500,
            'message': f'删除文件失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/cleanup', methods=['POST'])
def cleanup_files():
    """
    清理旧的系统文件
    """
    try:
        data = request.get_json() or {}
        retention_days = data.get('retention_days', 30)
        
        cleanup_service = FileCleanupService()
        result = cleanup_service.cleanup_old_files(retention_days)
        
        logger.info(f"文件清理完成: {result}")
        
        return jsonify({
            'code': 200,
            'message': f'清理完成',
            'data': result
        })
        
    except Exception as e:
        logger.error(f"文件清理失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'文件清理失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/cleanup/stats', methods=['GET'])
def get_cleanup_stats():
    """
    获取清理统计信息
    """
    try:
        cleanup_service = FileCleanupService()
        stats = cleanup_service.get_cleanup_stats()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': stats
        })
        
    except Exception as e:
        logger.error(f"获取清理统计失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'获取清理统计失败: {str(e)}',
            'data': None
        }), 500 