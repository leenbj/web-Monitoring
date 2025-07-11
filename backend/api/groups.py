"""
网站分组管理API
提供分组的增删改查功能
"""

import logging
from flask import Blueprint, request, jsonify

from ..database import get_db
from ..models import WebsiteGroup, Website
from ..utils.helpers import get_beijing_time

logger = logging.getLogger(__name__)

bp = Blueprint('groups', __name__, url_prefix='/api/groups')


@bp.route('/', methods=['GET'])
def get_groups():
    """
    获取分组列表
    """
    try:
        with get_db() as db:
            # 获取查询参数
            include_stats = request.args.get('include_stats', 'false').lower() == 'true'
            
            groups = db.query(WebsiteGroup).order_by(
                WebsiteGroup.is_default.desc(),
                WebsiteGroup.created_at.asc()
            ).all()
            
            groups_data = []
            for group in groups:
                group_dict = group.to_dict()
                
                if include_stats:
                    # 获取分组统计信息
                    website_count = db.query(Website).filter(Website.group_id == group.id).count()
                    active_count = db.query(Website).filter(
                        Website.group_id == group.id,
                        Website.is_active == True
                    ).count()
                    
                    group_dict.update({
                        'website_count': website_count,
                        'active_count': active_count
                    })
                
                groups_data.append(group_dict)
            
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': {
                    'groups': groups_data,
                    'total': len(groups_data)
                }
            })
        
    except Exception as e:
        logger.error(f"获取分组列表失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'获取分组列表失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/', methods=['POST'])
def create_group():
    """
    创建新分组
    """
    try:
        data = request.get_json()
        
        # 验证必填字段
        if not data or not data.get('name'):
            return jsonify({
                'code': 400,
                'message': '分组名称不能为空',
                'data': None
            }), 400
        
        with get_db() as db:
            # 检查分组名称是否已存在
            existing = db.query(WebsiteGroup).filter(WebsiteGroup.name == data['name']).first()
            if existing:
                return jsonify({
                    'code': 400,
                    'message': '分组名称已存在',
                    'data': None
                }), 400
            
            # 创建新分组
            group = WebsiteGroup(
                name=data['name'],
                description=data.get('description', ''),
                color=data.get('color', '#409EFF')
            )
            
            db.add(group)
            db.commit()
            db.refresh(group)
            
            logger.info(f"创建分组成功: {group.name}")
            
            return jsonify({
                'code': 200,
                'message': '创建分组成功',
                'data': group.to_dict()
            })
        
    except Exception as e:
        logger.error(f"创建分组失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'创建分组失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/<int:group_id>', methods=['GET'])
def get_group(group_id: int):
    """
    获取分组详情
    """
    try:
        with get_db() as db:
            group = db.query(WebsiteGroup).filter(WebsiteGroup.id == group_id).first()
            
            if not group:
                return jsonify({
                    'code': 404,
                    'message': '分组不存在',
                    'data': None
                }), 404
            
            # 获取分组下的网站列表
            websites = db.query(Website).filter(Website.group_id == group_id).all()
            websites_data = [website.to_dict() for website in websites]
            
            group_data = group.to_dict()
            group_data['websites'] = websites_data
            
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': group_data
            })
        
    except Exception as e:
        logger.error(f"获取分组详情失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'获取分组详情失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/<int:group_id>', methods=['PUT'])
def update_group(group_id: int):
    """
    更新分组信息
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'code': 400,
                'message': '请求数据不能为空',
                'data': None
            }), 400
        
        with get_db() as db:
            group = db.query(WebsiteGroup).filter(WebsiteGroup.id == group_id).first()
            
            if not group:
                return jsonify({
                    'code': 404,
                    'message': '分组不存在',
                    'data': None
                }), 404
            
            # 检查是否为默认分组
            if group.is_default and 'name' in data:
                return jsonify({
                    'code': 400,
                    'message': '默认分组名称不能修改',
                    'data': None
                }), 400
            
            # 检查分组名称是否已存在
            if 'name' in data and data['name'] != group.name:
                existing = db.query(WebsiteGroup).filter(
                    WebsiteGroup.name == data['name'],
                    WebsiteGroup.id != group_id
                ).first()
                if existing:
                    return jsonify({
                        'code': 400,
                        'message': '分组名称已存在',
                        'data': None
                    }), 400
            
            # 更新分组信息
            if 'name' in data:
                group.name = data['name']
            if 'description' in data:
                group.description = data['description']
            if 'color' in data:
                group.color = data['color']
            
            group.updated_at = get_beijing_time()
            
            db.commit()
            db.refresh(group)
            
            logger.info(f"更新分组成功: {group.name}")
            
            return jsonify({
                'code': 200,
                'message': '更新分组成功',
                'data': group.to_dict()
            })
        
    except Exception as e:
        logger.error(f"更新分组失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'更新分组失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/<int:group_id>', methods=['DELETE'])
def delete_group(group_id: int):
    """
    删除分组
    """
    try:
        with get_db() as db:
            group = db.query(WebsiteGroup).filter(WebsiteGroup.id == group_id).first()
            
            if not group:
                return jsonify({
                    'code': 404,
                    'message': '分组不存在',
                    'data': None
                }), 404
            
            # 检查是否为默认分组
            if group.is_default:
                return jsonify({
                    'code': 400,
                    'message': '默认分组不能删除',
                    'data': None
                }), 400
            
            # 获取默认分组
            default_group = db.query(WebsiteGroup).filter(WebsiteGroup.is_default == True).first()
            if not default_group:
                return jsonify({
                    'code': 500,
                    'message': '系统错误：未找到默认分组',
                    'data': None
                }), 500
            
            # 将该分组下的网站移动到默认分组
            websites = db.query(Website).filter(Website.group_id == group_id).all()
            moved_count = 0
            for website in websites:
                website.group_id = default_group.id
                moved_count += 1
            
            # 删除分组
            db.delete(group)
            db.commit()
            
            logger.info(f"删除分组成功: {group.name}, 移动网站: {moved_count} 个")
            
            return jsonify({
                'code': 200,
                'message': f'删除分组成功，{moved_count} 个网站已移动到默认分组',
                'data': {
                    'moved_count': moved_count,
                    'default_group_id': default_group.id
                }
            })
        
    except Exception as e:
        logger.error(f"删除分组失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'删除分组失败: {str(e)}',
            'data': None
        }), 500


@bp.route('/<int:group_id>/websites', methods=['POST'])
def assign_websites_to_group(group_id: int):
    """
    将网站分配到分组
    """
    try:
        data = request.get_json()
        
        if not data or 'website_ids' not in data:
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
        
        with get_db() as db:
            # 检查分组是否存在
            group = db.query(WebsiteGroup).filter(WebsiteGroup.id == group_id).first()
            if not group:
                return jsonify({
                    'code': 404,
                    'message': '分组不存在',
                    'data': None
                }), 404
            
            # 更新网站分组
            websites = db.query(Website).filter(Website.id.in_(website_ids)).all()
            updated_count = 0
            
            for website in websites:
                website.group_id = group_id
                website.updated_at = get_beijing_time()
                updated_count += 1
            
            db.commit()
            
            logger.info(f"分配网站到分组成功: {group.name}, 网站数量: {updated_count}")
            
            return jsonify({
                'code': 200,
                'message': f'成功将 {updated_count} 个网站分配到分组 {group.name}',
                'data': {
                    'group_id': group_id,
                    'updated_count': updated_count
                }
            })
        
    except Exception as e:
        logger.error(f"分配网站到分组失败: {e}")
        return jsonify({
            'code': 500,
            'message': f'分配网站到分组失败: {str(e)}',
            'data': None
        }), 500 