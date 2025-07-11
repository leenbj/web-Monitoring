"""
网站检测结果模型
"""

from typing import Dict, List, Optional
from datetime import datetime

from ..utils.helpers import get_beijing_time


class DetectionResult:
    """检测结果类"""
    
    def __init__(self):
        self.status: str = 'failed'  # standard, redirect, failed
        self.original_url: str = ''
        self.final_url: str = ''
        self.response_time: float = 0.0
        self.http_status_code: Optional[int] = None
        self.error_message: str = ''
        self.failure_reason: str = ''  # 详细失败原因：ssl_error, connection_error, timeout, server_error
        self.ssl_info: Dict = {}  # SSL证书信息
        self.redirect_chain: List[str] = []
        self.page_title: str = ''
        self.page_content_length: int = 0
        self.retry_count: int = 0
        self.detection_duration: float = 0.0
        self.detected_at: datetime = get_beijing_time()
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'status': self.status,
            'original_url': self.original_url,
            'final_url': self.final_url,
            'response_time': self.response_time,
            'http_status_code': self.http_status_code,
            'error_message': self.error_message,
            'failure_reason': self.failure_reason,
            'ssl_info': self.ssl_info,
            'redirect_chain': self.redirect_chain,
            'page_title': self.page_title,
            'page_content_length': self.page_content_length,
            'retry_count': self.retry_count,
            'detection_duration': self.detection_duration,
            'detected_at': self.detected_at.isoformat()
        } 