#!/usr/bin/env python3
"""
增强版最小后端 - 支持更多API接口
"""
import os
import sys
import json
import time
import uuid
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import subprocess

class WebMonitorAPIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # 健康检查
        if path == '/api/health':
            self.send_json_response({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0-enhanced'
            })
            
        # 根路径
        elif path == '/':
            self.send_json_response({
                'name': '网址监控系统',
                'version': '1.0.0-enhanced',
                'status': 'running'
            })
            
        # 获取分组列表
        elif path == '/api/groups/':
            self.send_json_response({
                'success': True,
                'data': [
                    {
                        'id': 1,
                        'name': '默认分组',
                        'description': '系统默认分组',
                        'website_count': 0,
                        'created_at': datetime.now().isoformat()
                    }
                ],
                'total': 1,
                'message': '获取分组列表成功'
            })
            
        # 获取网站列表
        elif path == '/api/websites/':
            self.send_json_response({
                'success': True,
                'data': [],
                'total': 0,
                'message': '获取网站列表成功'
            })
            
        # 获取任务列表
        elif path == '/api/tasks/':
            self.send_json_response({
                'success': True,
                'data': [],
                'total': 0,
                'message': '获取任务列表成功'
            })
            
        # 获取检测结果
        elif path == '/api/results/':
            self.send_json_response({
                'success': True,
                'data': [],
                'total': 0,
                'message': '获取检测结果成功'
            })
            
        # 获取文件列表
        elif path == '/api/files/':
            self.send_json_response({
                'success': True,
                'data': [],
                'total': 0,
                'message': '获取文件列表成功'
            })
            
        # 获取用户信息
        elif path == '/api/auth/me':
            self.send_json_response({
                'success': True,
                'data': {
                    'id': 1,
                    'username': 'admin',
                    'nickname': '管理员',
                    'role': 'admin',
                    'email': 'admin@example.com',
                    'created_at': datetime.now().isoformat()
                },
                'message': '获取用户信息成功'
            })
            
        # 获取用户列表
        elif path == '/api/auth/users':
            self.send_json_response({
                'success': True,
                'data': [
                    {
                        'id': 1,
                        'username': 'admin',
                        'nickname': '管理员',
                        'role': 'admin',
                        'email': 'admin@example.com',
                        'created_at': datetime.now().isoformat()
                    }
                ],
                'total': 1,
                'message': '获取用户列表成功'
            })
            
        # 获取系统设置
        elif path == '/api/settings/system':
            self.send_json_response({
                'success': True,
                'data': {
                    'system_name': '网址监控系统',
                    'version': '1.0.0',
                    'maintenance_mode': False,
                    'max_concurrent_tasks': 10,
                    'default_check_interval': 300
                },
                'message': '获取系统设置成功'
            })
            
        # 获取邮件设置
        elif path == '/api/settings/email':
            self.send_json_response({
                'success': True,
                'data': {
                    'smtp_server': '',
                    'smtp_port': 587,
                    'smtp_user': '',
                    'smtp_password': '',
                    'use_tls': True,
                    'enabled': False
                },
                'message': '获取邮件设置成功'
            })
            
        else:
            self.send_error(404, 'API endpoint not found')
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # 登录接口
        if path == '/api/auth/login':
            try:
                data = json.loads(post_data.decode())
                if data.get('username') == 'admin' and data.get('password') == 'admin123':
                    self.send_json_response({
                        'success': True,
                        'message': '登录成功',
                        'token': 'enhanced-token-' + str(int(time.time())),
                        'data': {
                            'user': {
                                'id': 1,
                                'username': 'admin',
                                'nickname': '管理员',
                                'role': 'admin',
                                'email': 'admin@example.com'
                            }
                        }
                    })
                else:
                    self.send_json_response({
                        'success': False,
                        'message': '用户名或密码错误'
                    }, status_code=401)
            except:
                self.send_error(400, 'Invalid JSON data')
                
        # 创建分组
        elif path == '/api/groups/':
            try:
                data = json.loads(post_data.decode())
                self.send_json_response({
                    'success': True,
                    'data': {
                        'id': int(time.time()),
                        'name': data.get('name', '新分组'),
                        'description': data.get('description', ''),
                        'website_count': 0,
                        'created_at': datetime.now().isoformat()
                    },
                    'message': '创建分组成功'
                })
            except:
                self.send_error(400, 'Invalid JSON data')
                
        # 创建网站
        elif path == '/api/websites/':
            try:
                data = json.loads(post_data.decode())
                self.send_json_response({
                    'success': True,
                    'data': {
                        'id': int(time.time()),
                        'name': data.get('name', '新网站'),
                        'url': data.get('url', ''),
                        'status': 'pending',
                        'group_id': data.get('group_id', 1),
                        'created_at': datetime.now().isoformat()
                    },
                    'message': '创建网站成功'
                })
            except:
                self.send_error(400, 'Invalid JSON data')
                
        # 创建任务
        elif path == '/api/tasks/':
            try:
                data = json.loads(post_data.decode())
                self.send_json_response({
                    'success': True,
                    'data': {
                        'id': int(time.time()),
                        'name': data.get('name', '新任务'),
                        'description': data.get('description', ''),
                        'status': 'created',
                        'created_at': datetime.now().isoformat()
                    },
                    'message': '创建任务成功'
                })
            except:
                self.send_error(400, 'Invalid JSON data')
                
        # 登出接口
        elif path == '/api/auth/logout':
            self.send_json_response({
                'success': True,
                'message': '登出成功'
            })
            
        # 测试邮件连接
        elif path == '/api/settings/email/test-connection':
            self.send_json_response({
                'success': True,
                'message': '邮件连接测试成功（模拟）'
            })
            
        # 保存系统设置
        elif path == '/api/settings/system':
            try:
                data = json.loads(post_data.decode())
                self.send_json_response({
                    'success': True,
                    'message': '系统设置保存成功'
                })
            except:
                self.send_error(400, 'Invalid JSON data')
                
        # 保存邮件设置
        elif path == '/api/settings/email':
            try:
                data = json.loads(post_data.decode())
                self.send_json_response({
                    'success': True,
                    'message': '邮件设置保存成功'
                })
            except:
                self.send_error(400, 'Invalid JSON data')
        
        else:
            self.send_error(404, 'API endpoint not found')
    
    def do_PUT(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # 更新分组
        if path.startswith('/api/groups/') and path.endswith('/'):
            try:
                data = json.loads(post_data.decode())
                group_id = path.split('/')[-2]
                self.send_json_response({
                    'success': True,
                    'data': {
                        'id': int(group_id),
                        'name': data.get('name', '更新分组'),
                        'description': data.get('description', ''),
                        'website_count': 0,
                        'updated_at': datetime.now().isoformat()
                    },
                    'message': '更新分组成功'
                })
            except:
                self.send_error(400, 'Invalid JSON data')
                
        # 更新网站
        elif path.startswith('/api/websites/'):
            try:
                data = json.loads(post_data.decode())
                website_id = path.split('/')[-1]
                self.send_json_response({
                    'success': True,
                    'data': {
                        'id': int(website_id),
                        'name': data.get('name', '更新网站'),
                        'url': data.get('url', ''),
                        'status': 'updated',
                        'updated_at': datetime.now().isoformat()
                    },
                    'message': '更新网站成功'
                })
            except:
                self.send_error(400, 'Invalid JSON data')
        
        else:
            self.send_error(404, 'API endpoint not found')
    
    def do_DELETE(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # 删除分组
        if path.startswith('/api/groups/'):
            group_id = path.split('/')[-1]
            self.send_json_response({
                'success': True,
                'message': f'删除分组 {group_id} 成功'
            })
            
        # 删除网站
        elif path.startswith('/api/websites/'):
            website_id = path.split('/')[-1]
            self.send_json_response({
                'success': True,
                'message': f'删除网站 {website_id} 成功'
            })
            
        # 删除任务
        elif path.startswith('/api/tasks/'):
            task_id = path.split('/')[-1]
            self.send_json_response({
                'success': True,
                'message': f'删除任务 {task_id} 成功'
            })
        
        else:
            self.send_error(404, 'API endpoint not found')
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')
        self.send_header('Access-Control-Max-Age', '86400')
        self.end_headers()
    
    def send_json_response(self, data, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def send_error(self, code, message=None):
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        error_data = {
            'success': False,
            'error': {
                'code': code,
                'message': message or f'HTTP {code} Error'
            }
        }
        self.wfile.write(json.dumps(error_data, ensure_ascii=False).encode('utf-8'))
    
    def log_message(self, format, *args):
        # 自定义日志格式
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {format % args}")

def run_server(port=5011):
    try:
        server_address = ('', port)
        httpd = HTTPServer(server_address, WebMonitorAPIHandler)
        print(f"启动增强版后端服务器在端口 {port}")
        print(f"服务器时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"访问地址: http://localhost:{port}")
        print(f"健康检查: http://localhost:{port}/api/health")
        print("-" * 50)
        
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n正在关闭服务器...")
        httpd.shutdown()
        print("服务器已关闭")
    except Exception as e:
        print(f"服务器启动失败: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5011))
    run_server(port)