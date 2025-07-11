"""
Dify平台API接口
提供给Dify平台调用的实时网址检测API
"""

from flask import Blueprint, request, jsonify
from functools import wraps
import logging
import time
from datetime import datetime

from backend.database import get_db
from backend.services.api_key_service import ApiKeyService
from backend.services.website_detector import WebsiteDetector

logger = logging.getLogger(__name__)

# 创建蓝图
bp = Blueprint('dify_api', __name__, url_prefix='/api/dify')

# 初始化服务
api_key_service = ApiKeyService()

def require_api_key(f):
    """API密钥验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # 从请求头获取API密钥
            api_key = request.headers.get('Authorization')
            if api_key and api_key.startswith('Bearer '):
                api_key = api_key[7:]  # 移除 "Bearer " 前缀
            
            if not api_key:
                # 也支持从查询参数获取
                api_key = request.args.get('api_key')
            
            if not api_key:
                return jsonify({
                    'success': False,
                    'error': 'API密钥缺失',
                    'message': '请在请求头Authorization中提供API密钥，格式: Bearer your_api_key'
                }), 401
            
            # 验证API密钥
            with get_db() as db:
                auth_result = api_key_service.authenticate_request(db, api_key)
                
                if not auth_result:
                    return jsonify({
                        'success': False,
                        'error': 'API密钥无效',
                        'message': '提供的API密钥无效或已过期'
                    }), 401
                
                # 将验证信息传递给视图函数
                request.api_auth = auth_result
                
        except Exception as e:
            logger.error(f"API密钥验证失败: {e}")
            return jsonify({
                'success': False,
                'error': '验证失败',
                'message': '服务器内部错误'
            }), 500
        
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/check-website', methods=['POST'])
@require_api_key
def check_website():
    """
    实时检测网址可访问性
    
    请求格式:
    {
        "url": "https://example.com",
        "timeout": 10,  // 可选，超时时间（秒）
        "retry_times": 1  // 可选，重试次数
    }
    
    响应格式:
    {
        "success": true,
        "data": {
            "url": "https://example.com",
            "status": "success",  // success, failed, timeout, error
            "status_code": 200,
            "response_time": 1.23,
            "error_message": null,
            "checked_at": "2025-06-25T12:00:00Z",
            "details": {
                "final_url": "https://example.com",
                "redirect_count": 0,
                "ssl_valid": true
            }
        }
    }
    """
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据格式错误',
                'message': '请提供JSON格式的请求数据'
            }), 400
        
        # 验证必需参数
        url = data.get('url')
        if not url:
            return jsonify({
                'success': False,
                'error': '参数缺失',
                'message': 'url参数是必需的'
            }), 400
        
        # 获取可选参数
        timeout = data.get('timeout', 10)
        retry_times = data.get('retry_times', 1)
        
        # 参数验证
        if not isinstance(timeout, (int, float)) or timeout <= 0 or timeout > 60:
            return jsonify({
                'success': False,
                'error': '参数错误',
                'message': 'timeout必须是1-60之间的数字'
            }), 400
        
        if not isinstance(retry_times, int) or retry_times < 0 or retry_times > 5:
            return jsonify({
                'success': False,
                'error': '参数错误',
                'message': 'retry_times必须是0-5之间的整数'
            }), 400
        
        # 记录请求信息
        logger.info(f"Dify API请求 - URL: {url}, 超时: {timeout}s, 重试: {retry_times}次")
        
        # 执行网址检测
        start_time = time.time()
        
        # 初始化检测器
        detector = WebsiteDetector({
            'timeout_seconds': int(timeout),
            'retry_times': retry_times,
            'max_concurrent': 1
        })
        
        # 执行检测
        result = detector.detect_single_website(url)
        
        # 计算总耗时
        total_time = time.time() - start_time
        
        # 构建响应数据
        response_data = {
            'url': url,
            'status': result.status,
            'status_code': result.http_status_code,
            'response_time': round(result.response_time, 3) if result.response_time else None,
            'error_message': result.error_message,
            'checked_at': datetime.now().isoformat(),
            'details': {
                'final_url': result.final_url or url,
                'redirect_count': len(result.redirect_chain) if result.redirect_chain else 0,
                'ssl_valid': result.ssl_info.get('valid', False) if result.ssl_info else False,
                'total_time': round(total_time, 3)
            }
        }
        
        # 记录检测结果
        logger.info(f"Dify API检测完成 - URL: {url}, 状态: {result.status}, 耗时: {total_time:.3f}s")
        
        return jsonify({
            'success': True,
            'data': response_data
        })
        
    except Exception as e:
        logger.error(f"Dify API检测失败: {e}")
        return jsonify({
            'success': False,
            'error': '检测失败',
            'message': f'服务器内部错误: {str(e)}'
        }), 500

@bp.route('/batch-check', methods=['POST'])
@require_api_key
def batch_check_websites():
    """
    批量检测网址可访问性
    
    请求格式:
    {
        "urls": ["https://example1.com", "https://example2.com"],
        "timeout": 10,
        "retry_times": 1,
        "max_concurrent": 3
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据格式错误',
                'message': '请提供JSON格式的请求数据'
            }), 400
        
        urls = data.get('urls', [])
        if not urls or not isinstance(urls, list):
            return jsonify({
                'success': False,
                'error': '参数错误',
                'message': 'urls必须是非空数组'
            }), 400
        
        if len(urls) > 50:  # 限制批量检测数量
            return jsonify({
                'success': False,
                'error': '参数错误',
                'message': '批量检测最多支持50个网址'
            }), 400
        
        timeout = data.get('timeout', 10)
        retry_times = data.get('retry_times', 1)
        max_concurrent = data.get('max_concurrent', 3)
        
        logger.info(f"Dify API批量检测 - 数量: {len(urls)}, 并发: {max_concurrent}")
        
        # 初始化检测器
        detector = WebsiteDetector({
            'timeout_seconds': int(timeout),
            'retry_times': retry_times,
            'max_concurrent': max_concurrent
        })
        
        # 执行批量检测
        start_time = time.time()
        results = detector.detect_batch_websites(urls)
        total_time = time.time() - start_time
        
        # 构建响应数据
        response_data = []
        for result in results:
            response_data.append({
                'url': result.original_url,
                'status': result.status,
                'status_code': result.http_status_code,
                'response_time': round(result.response_time, 3) if result.response_time else None,
                'error_message': result.error_message,
                'details': {
                    'final_url': result.final_url or result.original_url,
                    'redirect_count': len(result.redirect_chain) if result.redirect_chain else 0,
                    'ssl_valid': result.ssl_info.get('valid', False) if result.ssl_info else False
                }
            })
        
        logger.info(f"Dify API批量检测完成 - 数量: {len(urls)}, 总耗时: {total_time:.3f}s")
        
        return jsonify({
            'success': True,
            'data': {
                'results': response_data,
                'summary': {
                    'total_count': len(urls),
                    'success_count': len([r for r in results if r.status == 'success']),
                    'failed_count': len([r for r in results if r.status == 'failed']),
                    'total_time': round(total_time, 3)
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Dify API批量检测失败: {e}")
        return jsonify({
            'success': False,
            'error': '批量检测失败',
            'message': f'服务器内部错误: {str(e)}'
        }), 500

@bp.route('/api-info', methods=['GET'])
@require_api_key
def get_api_info():
    """
    获取API信息和使用统计
    """
    try:
        auth_info = request.api_auth
        key_info = auth_info.get('key_info', {})
        
        return jsonify({
            'success': True,
            'data': {
                'api_name': 'Website Monitor Dify API',
                'version': '1.0.0',
                'key_info': {
                    'name': key_info.get('name', 'Unknown'),
                    'created_at': key_info.get('created_at'),
                    'last_used_at': key_info.get('last_used_at'),
                    'usage_count': key_info.get('usage_count', 0)
                },
                'endpoints': {
                    'check_website': '/api/dify/check-website',
                    'batch_check': '/api/dify/batch-check',
                    'api_info': '/api/dify/api-info'
                },
                'limits': {
                    'max_timeout': 60,
                    'max_retry_times': 5,
                    'max_batch_size': 50,
                    'max_concurrent': 10
                }
            }
        })
        
    except Exception as e:
        logger.error(f"获取API信息失败: {e}")
        return jsonify({
            'success': False,
            'error': '获取信息失败',
            'message': f'服务器内部错误: {str(e)}'
        }), 500
