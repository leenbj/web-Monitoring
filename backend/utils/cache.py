"""
简单缓存工具
用于减少重复API查询和数据库负载
"""

import time
import hashlib
import json
from typing import Any, Optional, Dict
import logging

logger = logging.getLogger(__name__)


class SimpleCache:
    """简单内存缓存实现"""
    
    def __init__(self, default_ttl: int = 300, max_size: int = 100):
        """
        初始化缓存
        
        Args:
            default_ttl: 默认过期时间（秒）
            max_size: 最大缓存条目数
        """
        self.cache: Dict[str, Dict] = {}
        self.default_ttl = default_ttl
        self.max_size = max_size
    
    def _generate_key(self, key: str, **kwargs) -> str:
        """生成缓存键"""
        if kwargs:
            # 将参数排序后生成hash
            params_str = json.dumps(kwargs, sort_keys=True)
            hash_suffix = hashlib.md5(params_str.encode()).hexdigest()[:8]
            return f"{key}_{hash_suffix}"
        return key
    
    def get(self, key: str, **kwargs) -> Optional[Any]:
        """获取缓存值"""
        cache_key = self._generate_key(key, **kwargs)
        
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            
            # 检查是否过期
            if time.time() < entry['expires_at']:
                logger.debug(f"缓存命中: {cache_key}")
                return entry['value']
            else:
                # 删除过期条目
                del self.cache[cache_key]
                logger.debug(f"缓存过期: {cache_key}")
        
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, **kwargs):
        """设置缓存值"""
        cache_key = self._generate_key(key, **kwargs)
        
        # 检查缓存大小限制
        if len(self.cache) >= self.max_size:
            self._evict_oldest()
        
        ttl = ttl or self.default_ttl
        expires_at = time.time() + ttl
        
        self.cache[cache_key] = {
            'value': value,
            'expires_at': expires_at,
            'created_at': time.time()
        }
        
        logger.debug(f"缓存设置: {cache_key}, TTL: {ttl}s")
    
    def delete(self, key: str, **kwargs):
        """删除缓存值"""
        cache_key = self._generate_key(key, **kwargs)
        if cache_key in self.cache:
            del self.cache[cache_key]
            logger.debug(f"缓存删除: {cache_key}")
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
        logger.info("缓存已清空")
    
    def _evict_oldest(self):
        """删除最旧的缓存条目"""
        if not self.cache:
            return
        
        oldest_key = min(self.cache.keys(), 
                        key=lambda k: self.cache[k]['created_at'])
        del self.cache[oldest_key]
        logger.debug(f"淘汰最旧缓存: {oldest_key}")
    
    def cleanup_expired(self):
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time >= entry['expires_at']
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.debug(f"清理 {len(expired_keys)} 个过期缓存条目")
    
    def get_stats(self) -> Dict:
        """获取缓存统计信息"""
        current_time = time.time()
        active_count = sum(
            1 for entry in self.cache.values()
            if current_time < entry['expires_at']
        )
        
        return {
            'total_entries': len(self.cache),
            'active_entries': active_count,
            'expired_entries': len(self.cache) - active_count,
            'max_size': self.max_size,
            'hit_rate': getattr(self, '_hit_rate', 0.0)
        }


# 全局缓存实例
app_cache = SimpleCache(default_ttl=300, max_size=50)  # 5分钟默认TTL，最多50个条目


def cached(key: str, ttl: int = 300):
    """缓存装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 生成缓存键（包含函数参数）
            cache_key = f"{key}_{func.__name__}"
            
            # 尝试从缓存获取
            cached_result = app_cache.get(cache_key, **kwargs)
            if cached_result is not None:
                return cached_result
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            app_cache.set(cache_key, result, ttl, **kwargs)
            
            return result
        return wrapper
    return decorator