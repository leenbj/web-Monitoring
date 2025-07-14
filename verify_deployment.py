#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署验证脚本
全面检查系统部署状态和功能
"""

import os
import sys
import time
import json
import requests
import logging
from urllib.parse import urljoin

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DeploymentVerifier:
    """部署验证器"""
    
    def __init__(self, frontend_url="http://localhost:8080", backend_url="http://localhost:5012"):
        self.frontend_url = frontend_url
        self.backend_url = backend_url
        self.auth_token = None
        self.session = requests.Session()
        self.session.timeout = 10
        
    def verify_frontend_health(self):
        """验证前端健康状态"""
        logger.info("🔍 检查前端健康状态...")
        try:
            response = self.session.get(urljoin(self.frontend_url, "/health"))
            if response.status_code == 200:
                logger.info("✅ 前端健康检查通过")
                return True
            else:
                logger.error(f"❌ 前端健康检查失败: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ 前端健康检查失败: {e}")
            return False
    
    def verify_backend_health(self):
        """验证后端健康状态"""
        logger.info("🔍 检查后端健康状态...")
        try:
            response = self.session.get(urljoin(self.backend_url, "/api/health"))
            if response.status_code == 200:
                logger.info("✅ 后端健康检查通过")
                return True
            else:
                logger.error(f"❌ 后端健康检查失败: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ 后端健康检查失败: {e}")
            return False
    
    def verify_login(self):
        """验证登录功能"""
        logger.info("🔍 测试登录功能...")
        try:
            login_data = {
                "username": "admin",
                "password": "admin123"
            }
            
            response = self.session.post(
                urljoin(self.backend_url, "/api/auth/login"),
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 200 and data.get("data", {}).get("access_token"):
                    self.auth_token = data["data"]["access_token"]
                    logger.info("✅ 登录功能正常")
                    return True
                else:
                    logger.error(f"❌ 登录响应格式错误: {data}")
                    return False
            else:
                logger.error(f"❌ 登录失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ 登录测试失败: {e}")
            return False
    
    def verify_authenticated_request(self, endpoint, description):
        """验证需要认证的请求"""
        logger.info(f"🔍 测试{description}...")
        try:
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            response = self.session.get(
                urljoin(self.backend_url, endpoint),
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 200:
                    logger.info(f"✅ {description}正常")
                    return True, data
                else:
                    logger.error(f"❌ {description}响应错误: {data}")
                    return False, None
            else:
                logger.error(f"❌ {description}失败: {response.status_code} - {response.text}")
                return False, None
        except Exception as e:
            logger.error(f"❌ {description}测试失败: {e}")
            return False, None
    
    def verify_website_management(self):
        """验证网站管理功能"""
        logger.info("🔍 测试网站管理功能...")
        
        # 测试网站列表
        success, data = self.verify_authenticated_request("/api/websites/", "网站列表")
        if not success:
            return False
        
        websites = data.get("data", {}).get("websites", [])
        logger.info(f"📊 当前有 {len(websites)} 个网站")
        
        # 测试创建网站
        logger.info("🔍 测试创建网站...")
        try:
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            website_data = {
                "name": "测试网站",
                "url": "https://www.example.com",
                "description": "自动化测试创建的网站"
            }
            
            response = self.session.post(
                urljoin(self.backend_url, "/api/websites/"),
                json=website_data,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 200:
                    logger.info("✅ 网站创建功能正常")
                    
                    # 清理测试数据
                    website_id = data.get("data", {}).get("id")
                    if website_id:
                        self.session.delete(
                            urljoin(self.backend_url, f"/api/websites/{website_id}"),
                            headers=headers
                        )
                    
                    return True
                else:
                    logger.error(f"❌ 网站创建失败: {data}")
                    return False
            else:
                logger.error(f"❌ 网站创建失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ 网站创建测试失败: {e}")
            return False
    
    def verify_group_management(self):
        """验证分组管理功能"""
        success, data = self.verify_authenticated_request("/api/groups/", "分组管理")
        if success:
            groups = data.get("data", {}).get("groups", [])
            logger.info(f"📊 当前有 {len(groups)} 个分组")
            return True
        return False
    
    def verify_task_management(self):
        """验证任务管理功能"""
        success, data = self.verify_authenticated_request("/api/tasks/", "任务管理")
        if success:
            tasks = data.get("data", {}).get("tasks", [])
            logger.info(f"📊 当前有 {len(tasks)} 个任务")
            return True
        return False
    
    def verify_frontend_accessibility(self):
        """验证前端页面可访问性"""
        logger.info("🔍 测试前端页面可访问性...")
        
        # 测试主页
        try:
            response = self.session.get(self.frontend_url)
            if response.status_code == 200:
                logger.info("✅ 前端主页可访问")
                return True
            else:
                logger.error(f"❌ 前端主页不可访问: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ 前端主页访问失败: {e}")
            return False
    
    def run_full_verification(self):
        """运行完整验证"""
        logger.info("🚀 开始全面部署验证...")
        logger.info("=" * 50)
        
        results = {}
        
        # 1. 基础健康检查
        results["frontend_health"] = self.verify_frontend_health()
        results["backend_health"] = self.verify_backend_health()
        
        # 2. 前端页面可访问性
        results["frontend_accessibility"] = self.verify_frontend_accessibility()
        
        # 3. 登录功能
        results["login"] = self.verify_login()
        
        if results["login"]:
            # 4. 核心功能验证
            results["website_management"] = self.verify_website_management()
            results["group_management"] = self.verify_group_management()
            results["task_management"] = self.verify_task_management()
        else:
            logger.warning("⚠️ 登录失败，跳过功能验证")
            results["website_management"] = False
            results["group_management"] = False
            results["task_management"] = False
        
        # 5. 生成报告
        self.generate_report(results)
        
        return results
    
    def generate_report(self, results):
        """生成验证报告"""
        logger.info("=" * 50)
        logger.info("📊 部署验证报告")
        logger.info("=" * 50)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ 通过" if result else "❌ 失败"
            logger.info(f"{test_name.replace('_', ' ').title()}: {status}")
            if result:
                passed += 1
        
        logger.info("=" * 50)
        logger.info(f"总计: {passed}/{total} 测试通过")
        
        if passed == total:
            logger.info("🎉 所有测试通过，系统部署成功！")
            logger.info("🌐 访问地址:")
            logger.info(f"  - 前端: {self.frontend_url}")
            logger.info(f"  - 后端API: {self.backend_url}")
            logger.info("🔑 默认登录信息:")
            logger.info("  - 用户名: admin")
            logger.info("  - 密码: admin123")
            return True
        else:
            logger.error("❌ 部分测试失败，请检查系统配置")
            return False

def main():
    """主函数"""
    # 命令行参数处理
    frontend_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
    backend_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:5012"
    
    logger.info(f"🎯 目标系统:")
    logger.info(f"  - 前端: {frontend_url}")
    logger.info(f"  - 后端: {backend_url}")
    
    # 等待服务启动
    logger.info("⏳ 等待服务启动...")
    time.sleep(5)
    
    # 创建验证器并运行
    verifier = DeploymentVerifier(frontend_url, backend_url)
    success = verifier.run_full_verification()
    
    if success:
        logger.info("✅ 部署验证完成，系统运行正常！")
        sys.exit(0)
    else:
        logger.error("❌ 部署验证失败，请检查系统状态！")
        sys.exit(1)

if __name__ == "__main__":
    main()