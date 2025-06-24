#!/usr/bin/env python3
"""
资源监控脚本
监控后端服务的CPU、内存、数据库连接等资源使用情况
"""

import psutil
import time
import json
import sqlite3
import requests
from datetime import datetime
from pathlib import Path


class ResourceMonitor:
    """资源监控器"""
    
    def __init__(self):
        self.backend_url = "http://localhost:5001"
        self.db_path = Path(__file__).parent / "database" / "website_monitor.db"
        self.monitor_data = []
        
    def get_system_resources(self):
        """获取系统资源使用情况"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': cpu_percent,
                'memory': {
                    'total_mb': round(memory.total / 1024 / 1024, 2),
                    'used_mb': round(memory.used / 1024 / 1024, 2),
                    'available_mb': round(memory.available / 1024 / 1024, 2),
                    'percent': memory.percent
                },
                'disk': {
                    'total_gb': round(disk.total / 1024 / 1024 / 1024, 2),
                    'used_gb': round(disk.used / 1024 / 1024 / 1024, 2),
                    'free_gb': round(disk.free / 1024 / 1024 / 1024, 2),
                    'percent': round((disk.used / disk.total) * 100, 2)
                }
            }
        except Exception as e:
            return {'error': f"获取系统资源失败: {e}"}
    
    def get_backend_process_info(self):
        """获取后端进程信息"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
                try:
                    if 'python' in proc.info['name'].lower():
                        cmdline = proc.cmdline()
                        if any('run_backend.py' in cmd or 'app.py' in cmd for cmd in cmdline):
                            return {
                                'pid': proc.info['pid'],
                                'memory_mb': round(proc.info['memory_info'].rss / 1024 / 1024, 2),
                                'cpu_percent': proc.info['cpu_percent'],
                                'threads': proc.num_threads(),
                                'connections': len(proc.connections()),
                                'status': proc.status()
                            }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return None
        except Exception as e:
            return {'error': f"获取进程信息失败: {e}"}
    
    def get_database_info(self):
        """获取数据库信息"""
        try:
            if not self.db_path.exists():
                return {'error': '数据库文件不存在'}
            
            # 数据库文件大小
            db_size_mb = round(self.db_path.stat().st_size / 1024 / 1024, 2)
            
            # 连接数据库获取表信息
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # 获取各表记录数
            tables_info = {}
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                tables_info[table_name] = count
            
            conn.close()
            
            return {
                'db_size_mb': db_size_mb,
                'tables': tables_info,
                'total_records': sum(tables_info.values())
            }
        except Exception as e:
            return {'error': f"获取数据库信息失败: {e}"}
    
    def get_backend_api_status(self):
        """获取后端API状态"""
        try:
            # 检查API响应
            response = requests.get(f"{self.backend_url}/api/health", timeout=5)
            api_status = response.status_code == 200
            
            # 获取性能统计
            try:
                perf_response = requests.get(f"{self.backend_url}/api/performance/stats", timeout=5)
                performance_stats = perf_response.json() if perf_response.status_code == 200 else None
            except:
                performance_stats = None
            
            return {
                'api_available': api_status,
                'response_time_ms': round(response.elapsed.total_seconds() * 1000, 2),
                'performance_stats': performance_stats
            }
        except Exception as e:
            return {
                'api_available': False,
                'error': f"API检查失败: {e}"
            }
    
    def monitor_once(self):
        """执行一次监控"""
        monitor_result = {
            'timestamp': datetime.now().isoformat(),
            'system': self.get_system_resources(),
            'backend_process': self.get_backend_process_info(),
            'database': self.get_database_info(),
            'api': self.get_backend_api_status()
        }
        
        return monitor_result
    
    def print_monitor_result(self, result):
        """打印监控结果"""
        print(f"\n{'='*60}")
        print(f"资源监控报告 - {result['timestamp']}")
        print(f"{'='*60}")
        
        # 系统资源
        system = result['system']
        if 'error' not in system:
            print(f"📊 系统资源:")
            print(f"  CPU使用率: {system['cpu_percent']:.1f}%")
            print(f"  内存使用: {system['memory']['used_mb']:.1f}MB / {system['memory']['total_mb']:.1f}MB ({system['memory']['percent']:.1f}%)")
            print(f"  磁盘使用: {system['disk']['used_gb']:.1f}GB / {system['disk']['total_gb']:.1f}GB ({system['disk']['percent']:.1f}%)")
        
        # 后端进程
        process = result['backend_process']
        if process and 'error' not in process:
            print(f"\n🐍 后端进程 (PID: {process['pid']}):")
            print(f"  内存使用: {process['memory_mb']:.1f}MB")
            print(f"  CPU使用率: {process['cpu_percent']:.1f}%")
            print(f"  线程数: {process['threads']}")
            print(f"  连接数: {process['connections']}")
            print(f"  状态: {process['status']}")
        elif process and 'error' in process:
            print(f"\n🐍 后端进程: {process['error']}")
        else:
            print(f"\n🐍 后端进程: 未找到运行的后端进程")
        
        # 数据库
        database = result['database']
        if 'error' not in database:
            print(f"\n💾 数据库:")
            print(f"  文件大小: {database['db_size_mb']:.1f}MB")
            print(f"  总记录数: {database['total_records']:,}")
            print(f"  表详情:")
            for table, count in database['tables'].items():
                print(f"    {table}: {count:,} 条")
        else:
            print(f"\n💾 数据库: {database['error']}")
        
        # API状态
        api = result['api']
        print(f"\n🌐 API状态:")
        print(f"  可用性: {'✅' if api['api_available'] else '❌'}")
        if api['api_available']:
            print(f"  响应时间: {api['response_time_ms']:.1f}ms")
        if 'error' in api:
            print(f"  错误: {api['error']}")
    
    def continuous_monitor(self, interval=60, duration=3600):
        """持续监控"""
        print(f"开始持续监控，间隔 {interval} 秒，持续 {duration} 秒...")
        
        start_time = time.time()
        while time.time() - start_time < duration:
            result = self.monitor_once()
            self.monitor_data.append(result)
            self.print_monitor_result(result)
            
            # 检查资源警告
            self.check_resource_warnings(result)
            
            time.sleep(interval)
    
    def check_resource_warnings(self, result):
        """检查资源警告"""
        warnings = []
        
        # 检查系统资源
        system = result['system']
        if 'error' not in system:
            if system['cpu_percent'] > 80:
                warnings.append(f"⚠️  CPU使用率过高: {system['cpu_percent']:.1f}%")
            if system['memory']['percent'] > 80:
                warnings.append(f"⚠️  内存使用率过高: {system['memory']['percent']:.1f}%")
            if system['disk']['percent'] > 90:
                warnings.append(f"⚠️  磁盘使用率过高: {system['disk']['percent']:.1f}%")
        
        # 检查后端进程
        process = result['backend_process']
        if process and 'error' not in process:
            if process['memory_mb'] > 500:
                warnings.append(f"⚠️  后端进程内存使用过高: {process['memory_mb']:.1f}MB")
            if process['cpu_percent'] > 50:
                warnings.append(f"⚠️  后端进程CPU使用率过高: {process['cpu_percent']:.1f}%")
            if process['threads'] > 20:
                warnings.append(f"⚠️  后端进程线程数过多: {process['threads']}")
        
        # 检查数据库
        database = result['database']
        if 'error' not in database:
            if database['db_size_mb'] > 500:
                warnings.append(f"⚠️  数据库文件过大: {database['db_size_mb']:.1f}MB")
        
        # 输出警告
        if warnings:
            print(f"\n{'🚨 资源警告 🚨':^60}")
            for warning in warnings:
                print(f"  {warning}")
    
    def save_report(self, filename=None):
        """保存监控报告"""
        if not self.monitor_data:
            print("没有监控数据可保存")
            return
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"resource_monitor_report_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.monitor_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n监控报告已保存到: {filename}")


def main():
    """主函数"""
    monitor = ResourceMonitor()
    
    print("网址监控项目 - 资源监控工具")
    print("1. 单次监控")
    print("2. 持续监控 (10分钟)")
    print("3. 长期监控 (1小时)")
    
    choice = input("\n请选择监控模式 (1-3): ").strip()
    
    if choice == "1":
        result = monitor.monitor_once()
        monitor.print_monitor_result(result)
    
    elif choice == "2":
        monitor.continuous_monitor(interval=30, duration=600)  # 10分钟
        monitor.save_report()
    
    elif choice == "3":
        monitor.continuous_monitor(interval=60, duration=3600)  # 1小时
        monitor.save_report()
    
    else:
        print("无效选择")


if __name__ == "__main__":
    main()