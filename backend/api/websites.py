"""
网址监控工具 - 网站管理API路由
处理网站的增删改查操作
"""

from flask import Blueprint, request, jsonify
from typing import Dict, List
import traceback

from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Website, WebsiteGroup
from ..utils.validators import validate_url
from ..services.file_parser import FileParser

import logging

logger = logging.getLogger(__name__)

bp = Blueprint('websites', __name__, url_prefix='/api/websites')


@bp.route('/', methods=['GET'])
def get_websites():
    """
    获取网站列表
    支持分页和搜索
    """
    try:
        with get_db() as db:
            # 获取查询参数
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 20, type=int), 100)
            search = request.args.get('search', '', type=str)
            group_id = request.args.get('group_id')
            is_active = request.args.get('is_active')
            
            # 构建查询
            query = db.query(Website)
            
            if search:
                query = query.filter(
                    Website.name.contains(search) | 
                    Website.url.contains(search)
                )
            
            # 分组过滤
            if group_id is not None:
                if group_id == '':  # 未分组
                    query = query.filter(Website.group_id.is_(None))
                else:
                    try:
                        group_id_int = int(group_id)
                        query = query.filter(Website.group_id == group_id_int)
                    except ValueError:
                        pass
            
            # 状态过滤
            if is_active is not None:
                is_active_bool = is_active.lower() in ('true', '1', 'yes')
                query = query.filter(Website.is_active == is_active_bool)
            
            # 分页
            total = query.count()
            websites = query.offset((page - 1) * per_page).limit(per_page).all()
            
            # 序列化数据
            websites_data = []
            for website in websites:
                websites_data.append(website.to_dict())
            
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': {
                    'websites': websites_data,
                    'pagination': {
                        'page': page,
                        'per_page': per_page,
                        'total': total,
                        'pages': (total - 1) // per_page + 1 if total > 0 else 0
                    }
                }
            })
        
    except Exception as e:
        logger.error(f"获取网站列表失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'获取网站列表失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/', methods=['POST'])
def create_website():
    """
    创建单个网站
    """
    try:
        with get_db() as db:
            data = request.get_json()
            
            # 验证必填字段
            if not data or not data.get('url'):
                return jsonify({
                    'code': 400,
                    'message': '网址不能为空',
                    'data': None
                }), 400
            
            url = data['url'].strip()
            name = data.get('name', '').strip()
            description = data.get('description', '').strip()
            group_id = data.get('group_id')
            
            # 验证URL格式
            if not validate_url(url):
                return jsonify({
                    'code': 400,
                    'message': '网址格式不正确',
                    'data': None
                }), 400
            
            # 检查是否已存在
            existing = db.query(Website).filter(Website.url == url).first()
            if existing:
                return jsonify({
                    'code': 400,
                    'message': '该网址已存在',
                    'data': None
                }), 400
            
            # 从URL中提取域名
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            domain = parsed_url.netloc or url
            
            # 创建网站
            website = Website(
                name=name or url,
                url=url,
                domain=domain,
                original_url=url,
                normalized_url=url,
                description=description,
                group_id=group_id if group_id else None
            )
            
            db.add(website)
            db.flush()  # 刷新获取ID，但不提交
            
            logger.info(f"创建网站成功: {website.name} ({website.url})")
            
            return jsonify({
                'code': 200,
                'message': '创建成功',
                'data': {
                    'id': website.id,
                    'name': website.name,
                    'url': website.url,
                    'description': website.description,
                    'is_active': website.is_active,
                    'created_at': website.created_at.isoformat()
                }
            })
        
    except Exception as e:
        logger.error(f"创建网站失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'创建网站失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/batch', methods=['POST'])
def batch_create_websites():
    """
    批量创建网站
    """
    try:
        with get_db() as db:
            data = request.get_json()
            
            if not data or not data.get('websites'):
                return jsonify({
                    'code': 400,
                    'message': '网站数据不能为空',
                    'data': None
                }), 400
            
            websites_data = data['websites']
            
            if not isinstance(websites_data, list):
                return jsonify({
                    'code': 400,
                    'message': '网站数据格式错误',
                    'data': None
                }), 400
            
            created_websites = []
            failed_urls = []
            
            for item in websites_data:
                try:
                    url = item.get('url', '').strip()
                    name = item.get('name', '').strip()
                    description = item.get('description', '').strip()
                    
                    if not url:
                        failed_urls.append({'url': url or 'empty', 'reason': '网址不能为空'})
                        continue
                    
                    # 验证URL格式
                    if not validate_url(url):
                        failed_urls.append({'url': url, 'reason': '网址格式不正确'})
                        continue
                    
                    # 检查是否已存在
                    existing = db.query(Website).filter(Website.url == url).first()
                    if existing:
                        failed_urls.append({'url': url, 'reason': '该网址已存在'})
                        continue
                    
                    # 从URL中提取域名
                    from urllib.parse import urlparse
                    parsed_url = urlparse(url)
                    domain = parsed_url.netloc or url
                    
                    # 创建网站
                    website = Website(
                        name=name or url,
                        url=url,
                        domain=domain,
                        original_url=url,
                        normalized_url=url,
                        description=description
                    )
                    
                    db.add(website)
                    created_websites.append(website)
                    
                except Exception as e:
                    failed_urls.append({'url': item.get('url', 'unknown'), 'reason': str(e)})
            
            # 批量提交（这里会自动提交，因为with语句结束时会调用commit）
            
            logger.info(f"批量创建网站完成: 成功 {len(created_websites)} 个，失败 {len(failed_urls)} 个")
            
            return jsonify({
                'code': 200,
                'message': f'批量创建完成，成功 {len(created_websites)} 个，失败 {len(failed_urls)} 个',
                'data': {
                    'created_count': len(created_websites),
                    'failed_count': len(failed_urls),
                    'failed_urls': failed_urls
                }
            })
        
    except Exception as e:
        logger.error(f"批量创建网站失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'批量创建网站失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/<int:website_id>', methods=['GET'])
def get_website(website_id: int):
    """
    获取单个网站详情
    """
    try:
        with get_db() as db:
            website = db.query(Website).filter(Website.id == website_id).first()
            
            if not website:
                return jsonify({
                    'code': 404,
                    'message': '网站不存在',
                    'data': None
                }), 404
            
            # 获取分组信息
            group_info = {}
            if website.group_id:
                group = db.query(WebsiteGroup).filter(WebsiteGroup.id == website.group_id).first()
                if group:
                    group_info = {
                        'group_id': group.id,
                        'group_name': group.name,
                        'group_color': group.color
                    }
            
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': {
                    'id': website.id,
                    'name': website.name,
                    'url': website.url,
                    'description': website.description,
                    'is_active': website.is_active,
                    'created_at': website.created_at.isoformat(),
                    'updated_at': website.updated_at.isoformat() if website.updated_at else None,
                    **group_info
                }
            })
        
    except Exception as e:
        logger.error(f"获取网站详情失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'获取网站详情失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/<int:website_id>', methods=['PUT'])
def update_website(website_id: int):
    """
    更新网站信息
    """
    try:
        with get_db() as db:
            data = request.get_json()
            
            website = db.query(Website).filter(Website.id == website_id).first()
            
            if not website:
                return jsonify({
                    'code': 404,
                    'message': '网站不存在',
                    'data': None
                }), 404
            
            # 更新字段
            if 'name' in data:
                website.name = data['name'].strip()
            
            if 'url' in data:
                new_url = data['url'].strip()
                if not validate_url(new_url):
                    return jsonify({
                        'code': 400,
                        'message': '网址格式不正确',
                        'data': None
                    }), 400
                
                # 检查新URL是否与其他网站重复
                existing = db.query(Website).filter(
                    Website.url == new_url,
                    Website.id != website_id
                ).first()
                
                if existing:
                    return jsonify({
                        'code': 400,
                        'message': '该网址已被其他网站使用',
                        'data': None
                    }), 400
                
                website.url = new_url
            
            if 'description' in data:
                website.description = data['description'].strip()
            
            if 'is_active' in data:
                website.is_active = bool(data['is_active'])
            
            if 'group_id' in data:
                group_id = data['group_id']
                if group_id is not None:
                    # 验证分组是否存在
                    group = db.query(WebsiteGroup).filter(WebsiteGroup.id == group_id).first()
                    if not group:
                        return jsonify({
                            'code': 400,
                            'message': '指定的分组不存在',
                            'data': None
                        }), 400
                website.group_id = group_id
            
            db.commit()
            db.refresh(website)
            
            logger.info(f"更新网站成功: {website.name} ({website.url})")
            
            return jsonify({
                'code': 200,
                'message': '更新成功',
                'data': {
                    'id': website.id,
                    'name': website.name,
                    'url': website.url,
                    'description': website.description,
                    'is_active': website.is_active,
                    'updated_at': website.updated_at.isoformat()
                }
            })
        
    except Exception as e:
        logger.error(f"更新网站失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'更新网站失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/<int:website_id>', methods=['DELETE'])
def delete_website(website_id: int):
    """
    删除网站
    """
    try:
        with get_db() as db:
            website = db.query(Website).filter(Website.id == website_id).first()
            
            if not website:
                return jsonify({
                    'code': 404,
                    'message': '网站不存在',
                    'data': None
                }), 404
            
            # 删除网站
            db.delete(website)
            db.commit()
            
            logger.info(f"删除网站成功: {website.name} ({website.url})")
            
            return jsonify({
                'code': 200,
                'message': '删除成功',
                'data': None
            })
        
    except Exception as e:
        logger.error(f"删除网站失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'删除网站失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/batch/delete', methods=['POST'])
def batch_delete_websites():
    """
    批量删除网站
    """
    try:
        with get_db() as db:
            data = request.get_json()
            
            if not data or not data.get('website_ids'):
                return jsonify({
                    'code': 400,
                    'message': '网站ID列表不能为空',
                    'data': None
                }), 400
            
            website_ids = data['website_ids']
            
            if not isinstance(website_ids, list):
                return jsonify({
                    'code': 400,
                    'message': '网站ID格式错误',
                    'data': None
                }), 400
            
            # 查找要删除的网站
            websites = db.query(Website).filter(Website.id.in_(website_ids)).all()
            
            if not websites:
                return jsonify({
                    'code': 404,
                    'message': '没有找到要删除的网站',
                    'data': None
                }), 404
            
            # 批量删除
            deleted_count = 0
            for website in websites:
                db.delete(website)
                deleted_count += 1
            
            db.commit()
            
            logger.info(f"批量删除网站成功: {deleted_count} 个")
            
            return jsonify({
                'code': 200,
                'message': f'批量删除成功，共删除 {deleted_count} 个网站',
                'data': {
                    'deleted_count': deleted_count
                }
            })
        
    except Exception as e:
        logger.error(f"批量删除网站失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'批量删除网站失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/toggle-status/<int:website_id>', methods=['POST'])
def toggle_website_status(website_id: int):
    """
    切换网站启用/禁用状态
    """
    try:
        with get_db() as db:
            website = db.query(Website).filter(Website.id == website_id).first()
            
            if not website:
                return jsonify({
                    'code': 404,
                    'message': '网站不存在',
                    'data': None
                }), 404
            
            # 切换状态
            website.is_active = not website.is_active
            db.commit()
            db.refresh(website)
            
            status_text = '启用' if website.is_active else '禁用'
            logger.info(f"{status_text}网站: {website.name} ({website.url})")
            
            return jsonify({
                'code': 200,
                'message': f'网站已{status_text}',
                'data': {
                    'id': website.id,
                    'is_active': website.is_active
                }
            })
        
    except Exception as e:
        logger.error(f"切换网站状态失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'切换网站状态失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/import', methods=['POST'])
def import_websites_from_file():
    """
    从文件导入网站
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
        
        # 检查文件扩展名
        allowed_extensions = {'.xlsx', '.xls', '.csv'}
        file_ext = '.' + file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        
        if file_ext not in allowed_extensions:
            return jsonify({
                'code': 400,
                'message': '文件格式不支持，请上传 Excel 或 CSV 文件',
                'data': None
            }), 400
        
        # 保存临时文件
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            file.save(tmp_file.name)
            tmp_file_path = tmp_file.name
        
        try:
            # 解析文件
            parser = FileParser()
            parse_result = parser.parse_file(tmp_file_path)
            
            if not parse_result.success:
                return jsonify({
                    'code': 400,
                    'message': f'文件解析失败: {parse_result.error_message}',
                    'data': None
                }), 400
            
            # 批量创建网站
            with get_db() as db:
                created_websites = []
                failed_urls = []
                
                for url in parse_result.valid_urls:
                    try:
                        # 检查是否已存在
                        existing = db.query(Website).filter(Website.url == url).first()
                        if existing:
                            failed_urls.append({'url': url, 'reason': '网址已存在'})
                            continue
                        
                        # 从URL中提取域名
                        from urllib.parse import urlparse
                        
                        # 初始化变量
                        normalized_url = url
                        domain = url
                        original_url = url
                        
                        try:
                            # 标准化URL
                            if not url.startswith(('http://', 'https://')):
                                normalized_url = 'http://' + url
                            
                            logger.info(f"处理URL: {url} -> {normalized_url}")
                            
                            parsed = urlparse(normalized_url)
                            if parsed.netloc:
                                domain = parsed.netloc.lower()
                            
                            logger.info(f"解析结果: domain={domain}, netloc={parsed.netloc}")
                                
                        except Exception as e:
                            logger.warning(f"域名提取失败: {url}, 使用原URL: {e}")
                        
                        # 创建网站
                        logger.info(f"创建网站对象: name={url}, url={normalized_url}, domain={domain}, original_url={original_url}")
                        
                        website = Website(
                            name=url,  # 默认使用URL作为名称
                            url=normalized_url,
                            domain=domain,
                            original_url=original_url,
                            normalized_url=normalized_url
                        )
                        
                        db.add(website)
                        created_websites.append(website)
                        
                    except Exception as e:
                        failed_urls.append({'url': url, 'reason': str(e)})
                
                # 提交事务
                if created_websites:
                    db.commit()
                    for website in created_websites:
                        db.refresh(website)
            
                logger.info(f"从文件导入网站完成: 成功 {len(created_websites)} 个，失败 {len(failed_urls)} 个")
            
                return jsonify({
                'code': 200,
                'message': f'导入完成，成功 {len(created_websites)} 个，失败 {len(failed_urls)} 个',
                'data': {
                    'total_urls': len(parse_result.valid_urls),
                    'created_count': len(created_websites),
                    'failed_count': len(failed_urls),
                    'failed_urls': failed_urls
                }
                })
            
        finally:
            # 清理临时文件
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
        
    except Exception as e:
        logger.error(f"导入网站失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'导入网站失败: {str(e)}',
            'data': None
        }), 500