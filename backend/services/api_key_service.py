"""
API密钥管理服务
用于管理Dify平台的API密钥，包括生成、验证、存储等功能
"""

import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class ApiKeyService:
    """API密钥管理服务"""
    
    def __init__(self):
        """初始化API密钥服务"""
        self.key_prefix = "dify_"
        self.key_length = 32
        self.logger = logger
        self.logger.info("API密钥服务初始化完成")
    
    def generate_api_key(self, name: str = "Default") -> Dict[str, Any]:
        """
        生成新的API密钥
        
        Args:
            name: 密钥名称
            
        Returns:
            包含密钥信息的字典
        """
        try:
            # 生成随机密钥
            raw_key = secrets.token_urlsafe(self.key_length)
            api_key = f"{self.key_prefix}{raw_key}"
            
            # 生成密钥哈希用于存储
            key_hash = self._hash_key(api_key)
            
            # 创建密钥信息
            key_info = {
                'name': name,
                'key_hash': key_hash,
                'created_at': datetime.now(),
                'last_used_at': None,
                'is_active': True,
                'usage_count': 0
            }
            
            logger.info(f"生成新的API密钥: {name}")
            return {
                'api_key': api_key,
                'key_info': key_info
            }
            
        except Exception as e:
            logger.error(f"生成API密钥失败: {e}")
            raise Exception(f"生成API密钥失败: {str(e)}")
    
    def _hash_key(self, api_key: str) -> str:
        """
        对API密钥进行哈希处理
        
        Args:
            api_key: 原始API密钥
            
        Returns:
            哈希后的密钥
        """
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def verify_api_key(self, api_key: str, stored_hash: str) -> bool:
        """
        验证API密钥
        
        Args:
            api_key: 待验证的API密钥
            stored_hash: 存储的密钥哈希
            
        Returns:
            验证结果
        """
        try:
            if not api_key or not stored_hash:
                return False
                
            # 计算提供密钥的哈希
            provided_hash = self._hash_key(api_key)
            
            # 使用安全比较防止时序攻击
            return hmac.compare_digest(provided_hash, stored_hash)
            
        except Exception as e:
            logger.error(f"验证API密钥失败: {e}")
            return False
    
    def save_api_key(self, db, key_info: Dict[str, Any]) -> int:
        """
        保存API密钥到数据库
        
        Args:
            db: 数据库连接
            key_info: 密钥信息
            
        Returns:
            密钥ID
        """
        try:
            from backend.models import SystemSetting

            # 转换datetime对象为字符串以便JSON序列化
            import json
            serializable_key_info = {
                'name': key_info['name'],
                'key_hash': key_info['key_hash'],
                'created_at': key_info['created_at'].isoformat(),
                'last_used_at': key_info['last_used_at'].isoformat() if key_info['last_used_at'] else None,
                'is_active': key_info['is_active'],
                'usage_count': key_info['usage_count']
            }

            # 保存密钥信息到系统设置表
            key_setting = SystemSetting(
                key=f"dify_api_key_{datetime.now().timestamp()}",
                value=json.dumps(serializable_key_info),
                description=f"Dify API密钥: {key_info['name']}",
                category="dify_api",
                data_type="json",
                is_active=True
            )
            
            db.add(key_setting)
            db.commit()
            db.refresh(key_setting)
            
            logger.info(f"API密钥保存成功: {key_info['name']}")
            return key_setting.id
            
        except Exception as e:
            logger.error(f"保存API密钥失败: {e}")
            db.rollback()
            raise Exception(f"保存API密钥失败: {str(e)}")
    
    def get_api_keys(self, db) -> list:
        """
        获取所有API密钥
        
        Args:
            db: 数据库连接
            
        Returns:
            API密钥列表
        """
        try:
            from backend.models import SystemSetting

            keys = db.query(SystemSetting).filter(
                SystemSetting.category == "dify_api",
                SystemSetting.is_active == True
            ).all()
            
            result = []
            for key in keys:
                try:
                    import json
                    from datetime import datetime
                    key_info = json.loads(key.value)
                    result.append({
                        'id': key.id,
                        'name': key_info.get('name', 'Unknown'),
                        'created_at': key_info.get('created_at'),
                        'last_used_at': key_info.get('last_used_at'),
                        'usage_count': key_info.get('usage_count', 0),
                        'is_active': key_info.get('is_active', True)
                    })
                except Exception as e:
                    self.logger.warning(f"解析API密钥信息失败: {e}")
                    continue
            
            return result
            
        except Exception as e:
            self.logger.error(f"获取API密钥列表失败: {e}")
            return []
    
    def delete_api_key(self, db, key_id: int) -> bool:
        """
        删除API密钥
        
        Args:
            db: 数据库连接
            key_id: 密钥ID
            
        Returns:
            删除结果
        """
        try:
            from backend.models import SystemSetting

            key = db.query(SystemSetting).filter(
                SystemSetting.id == key_id,
                SystemSetting.category == "dify_api"
            ).first()
            
            if key:
                key.is_active = False
                db.commit()
                self.logger.info(f"API密钥删除成功: {key_id}")
                return True
            else:
                self.logger.warning(f"API密钥不存在: {key_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"删除API密钥失败: {e}")
            db.rollback()
            return False
    
    def update_key_usage(self, db, key_hash: str):
        """
        更新密钥使用记录
        
        Args:
            db: 数据库连接
            key_hash: 密钥哈希
        """
        try:
            from backend.models import SystemSetting

            keys = db.query(SystemSetting).filter(
                SystemSetting.category == "dify_api",
                SystemSetting.is_active == True
            ).all()
            
            for key in keys:
                try:
                    import json
                    key_info = json.loads(key.value)
                    if key_info.get('key_hash') == key_hash:
                        key_info['last_used_at'] = datetime.now().isoformat()
                        key_info['usage_count'] = key_info.get('usage_count', 0) + 1
                        key.value = json.dumps(key_info)
                        db.commit()
                        break
                except Exception as e:
                    self.logger.warning(f"更新密钥使用记录失败: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"更新密钥使用记录失败: {e}")
    
    def authenticate_request(self, db, api_key: str) -> Optional[Dict[str, Any]]:
        """
        验证API请求
        
        Args:
            db: 数据库连接
            api_key: API密钥
            
        Returns:
            验证结果和密钥信息
        """
        try:
            if not api_key or not api_key.startswith(self.key_prefix):
                return None
            
            from backend.models import SystemSetting

            keys = db.query(SystemSetting).filter(
                SystemSetting.category == "dify_api",
                SystemSetting.is_active == True
            ).all()
            
            for key in keys:
                try:
                    import json
                    key_info = json.loads(key.value)
                    stored_hash = key_info.get('key_hash')

                    if self.verify_api_key(api_key, stored_hash):
                        # 更新使用记录
                        self.update_key_usage(db, stored_hash)

                        return {
                            'valid': True,
                            'key_info': key_info
                        }
                except Exception as e:
                    self.logger.warning(f"验证API密钥时解析失败: {e}")
                    continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"API请求验证失败: {e}")
            return None
