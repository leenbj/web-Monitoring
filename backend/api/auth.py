"""
用户认证API
处理用户登录、注册、权限管理等功能
"""

from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from datetime import datetime, timedelta
import logging

from ..database import get_db
from ..models import User

logger = logging.getLogger(__name__)

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# JWT黑名单 (简单实现，生产环境建议使用Redis)
blacklisted_tokens = set()


@bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({
                'code': 400,
                'message': '用户名和密码不能为空',
                'data': None
            }), 400
        
        with get_db() as db:
            user = db.query(User).filter(User.username == username).first()
            
            if not user:
                return jsonify({
                    'code': 401,
                    'message': '用户名或密码错误',
                    'data': None
                }), 401
            
            if user.status != 'active':
                return jsonify({
                    'code': 401,
                    'message': '账户已被禁用',
                    'data': None
                }), 401
            
            if not user.check_password(password):
                return jsonify({
                    'code': 401,
                    'message': '用户名或密码错误',
                    'data': None
                }), 401
            
            # 更新最后登录时间
            user.last_login_at = datetime.now()
            db.commit()
            
            # 生成JWT token
            additional_claims = {
                'role': user.role,
                'username': user.username
            }
            
            access_token = create_access_token(
                identity=str(user.id),
                additional_claims=additional_claims,
                expires_delta=timedelta(hours=24)
            )
            
            refresh_token = create_refresh_token(
                identity=str(user.id),
                expires_delta=timedelta(days=7)
            )
            
            return jsonify({
                'code': 200,
                'message': '登录成功',
                'data': {
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'expires_in': 86400,  # 24小时
                    'user': user.to_dict()
                }
            })
    
    except Exception as e:
        logger.error(f"登录失败: {e}")
        return jsonify({
            'code': 500,
            'message': '登录失败',
            'data': None
        }), 500


@bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """用户登出"""
    try:
        jti = get_jwt()['jti']
        blacklisted_tokens.add(jti)
        
        return jsonify({
            'code': 200,
            'message': '登出成功',
            'data': None
        })
    
    except Exception as e:
        logger.error(f"登出失败: {e}")
        return jsonify({
            'code': 500,
            'message': '登出失败',
            'data': None
        }), 500


@bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """获取当前用户信息"""
    try:
        user_id = get_jwt_identity()
        
        with get_db() as db:
            user = db.query(User).filter(User.id == int(user_id)).first()
            
            if not user:
                return jsonify({
                    'code': 404,
                    'message': '用户不存在',
                    'data': None
                }), 404
            
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': user.to_dict()
            })
    
    except Exception as e:
        logger.error(f"获取用户信息失败: {e}")
        return jsonify({
            'code': 500,
            'message': '获取用户信息失败',
            'data': None
        }), 500


@bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """刷新访问令牌"""
    try:
        user_id = get_jwt_identity()
        
        with get_db() as db:
            user = db.query(User).filter(User.id == int(user_id)).first()
            
            if not user or user.status != 'active':
                return jsonify({
                    'code': 401,
                    'message': '用户不存在或已被禁用',
                    'data': None
                }), 401
            
            additional_claims = {
                'role': user.role,
                'username': user.username
            }
            
            new_access_token = create_access_token(
                identity=str(user.id),
                additional_claims=additional_claims,
                expires_delta=timedelta(hours=24)
            )
            
            return jsonify({
                'code': 200,
                'message': 'Token刷新成功',
                'data': {
                    'access_token': new_access_token,
                    'expires_in': 86400
                }
            })
    
    except Exception as e:
        logger.error(f"刷新token失败: {e}")
        return jsonify({
            'code': 500,
            'message': '刷新token失败',
            'data': None
        }), 500


# 用户管理相关API (需要管理员权限)

@bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    """获取用户列表"""
    try:
        # 检查管理员权限
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({
                'code': 403,
                'message': '权限不足',
                'data': None
            }), 403
        
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        with get_db() as db:
            query = db.query(User)
            
            total = query.count()
            users = query.order_by(User.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
            
            users_data = [user.to_dict() for user in users]
            
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': {
                    'users': users_data,
                    'pagination': {
                        'page': page,
                        'per_page': per_page,
                        'total': total,
                        'pages': (total + per_page - 1) // per_page
                    }
                }
            })
    
    except Exception as e:
        logger.error(f"获取用户列表失败: {e}")
        return jsonify({
            'code': 500,
            'message': '获取用户列表失败',
            'data': None
        }), 500


@bp.route('/users', methods=['POST'])
@jwt_required()
def create_user():
    """创建用户"""
    try:
        # 检查管理员权限
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({
                'code': 403,
                'message': '权限不足',
                'data': None
            }), 403
        
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        email = data.get('email', '').strip()
        real_name = data.get('real_name', '').strip()
        role = data.get('role', 'user')
        status = data.get('status', 'active')
        
        if not username or not password or not email:
            return jsonify({
                'code': 400,
                'message': '用户名、密码和邮箱不能为空',
                'data': None
            }), 400
        
        with get_db() as db:
            # 检查用户名是否已存在
            existing_user = db.query(User).filter(User.username == username).first()
            if existing_user:
                return jsonify({
                    'code': 400,
                    'message': '用户名已存在',
                    'data': None
                }), 400
            
            # 检查邮箱是否已存在
            existing_email = db.query(User).filter(User.email == email).first()
            if existing_email:
                return jsonify({
                    'code': 400,
                    'message': '邮箱已存在',
                    'data': None
                }), 400
            
            # 创建新用户
            user = User(
                username=username,
                email=email,
                real_name=real_name or username,
                role=role,
                status=status
            )
            user.set_password(password)
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            return jsonify({
                'code': 200,
                'message': '用户创建成功',
                'data': user.to_dict()
            })
    
    except Exception as e:
        logger.error(f"创建用户失败: {e}")
        return jsonify({
            'code': 500,
            'message': '创建用户失败',
            'data': None
        }), 500


@bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id: int):
    """更新用户信息"""
    try:
        # 检查管理员权限
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({
                'code': 403,
                'message': '权限不足',
                'data': None
            }), 403
        
        data = request.get_json()
        
        with get_db() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return jsonify({
                    'code': 404,
                    'message': '用户不存在',
                    'data': None
                }), 404
            
            # 更新用户信息
            if 'email' in data:
                user.email = data['email'].strip()
            if 'real_name' in data:
                user.real_name = data['real_name'].strip()
            if 'role' in data:
                user.role = data['role']
            if 'status' in data:
                user.status = data['status']
            
            user.updated_at = datetime.now()
            db.commit()
            
            return jsonify({
                'code': 200,
                'message': '用户更新成功',
                'data': user.to_dict()
            })
    
    except Exception as e:
        logger.error(f"更新用户失败: {e}")
        return jsonify({
            'code': 500,
            'message': '更新用户失败',
            'data': None
        }), 500


@bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id: int):
    """删除用户"""
    try:
        # 检查管理员权限
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({
                'code': 403,
                'message': '权限不足',
                'data': None
            }), 403
        
        # 不能删除自己
        current_user_id = int(get_jwt_identity())
        if user_id == current_user_id:
            return jsonify({
                'code': 400,
                'message': '不能删除自己',
                'data': None
            }), 400
        
        with get_db() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return jsonify({
                    'code': 404,
                    'message': '用户不存在',
                    'data': None
                }), 404
            
            db.delete(user)
            db.commit()
            
            return jsonify({
                'code': 200,
                'message': '用户删除成功',
                'data': None
            })
    
    except Exception as e:
        logger.error(f"删除用户失败: {e}")
        return jsonify({
            'code': 500,
            'message': '删除用户失败',
            'data': None
        }), 500


@bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@jwt_required()
def reset_password(user_id: int):
    """重置用户密码"""
    try:
        # 检查管理员权限
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({
                'code': 403,
                'message': '权限不足',
                'data': None
            }), 403
        
        data = request.get_json()
        new_password = data.get('password', '')
        
        if not new_password:
            return jsonify({
                'code': 400,
                'message': '新密码不能为空',
                'data': None
            }), 400
        
        with get_db() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return jsonify({
                    'code': 404,
                    'message': '用户不存在',
                    'data': None
                }), 404
            
            user.set_password(new_password)
            user.updated_at = datetime.now()
            db.commit()
            
            return jsonify({
                'code': 200,
                'message': '密码重置成功',
                'data': None
            })
    
    except Exception as e:
        logger.error(f"重置密码失败: {e}")
        return jsonify({
            'code': 500,
            'message': '重置密码失败',
            'data': None
        }), 500 