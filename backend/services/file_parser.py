"""
网址监控工具 - 文件解析服务
解析Excel和CSV文件，提取网址数据
"""

import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import pandas as pd
import logging

logger = logging.getLogger(__name__)

from ..utils.helpers import normalize_url, detect_file_encoding
from ..utils.validators import validate_excel_file, validate_csv_file, is_valid_url


class ParseResult:
    """文件解析结果类"""
    
    def __init__(self):
        self.success: bool = False
        self.total_rows: int = 0
        self.valid_urls: List[str] = []
        self.invalid_urls: List[str] = []
        self.error_message: str = ""
        self.file_info: Dict = {}
        
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'success': self.success,
            'total_rows': self.total_rows,
            'valid_count': len(self.valid_urls),
            'invalid_count': len(self.invalid_urls),
            'valid_urls': self.valid_urls,
            'invalid_urls': self.invalid_urls,
            'error_message': self.error_message,
            'file_info': self.file_info
        }


class FileParser:
    """文件解析器"""
    
    def __init__(self):
        """初始化文件解析器"""
        self.supported_extensions = ['xlsx', 'xls', 'csv']
        self.url_column_names = ['网址', 'domain', 'url', 'website', 'link', '域名', '网站']
        logger.info("文件解析器初始化完成")
    
    def parse_file(self, file_path: str) -> ParseResult:
        """
        解析文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            解析结果
        """
        result = ParseResult()
        
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                result.error_message = "文件不存在"
                return result
            
            # 获取文件信息
            result.file_info = self._get_file_info(file_path)
            
            # 根据文件扩展名选择解析方法
            file_ext = os.path.splitext(file_path)[1].lower().lstrip('.')
            
            if file_ext in ['xlsx', 'xls']:
                result = self._parse_excel_file(file_path, result)
            elif file_ext == 'csv':
                result = self._parse_csv_file(file_path, result)
            else:
                result.error_message = f"不支持的文件格式: {file_ext}"
                return result
            
            logger.info(f"文件解析完成: {file_path}, 有效URL: {len(result.valid_urls)}, 无效URL: {len(result.invalid_urls)}")
            
        except Exception as e:
            logger.error(f"文件解析异常: {file_path}, 错误: {e}")
            result.error_message = f"文件解析异常: {str(e)}"
        
        return result
    
    def _get_file_info(self, file_path: str) -> Dict:
        """获取文件基本信息"""
        try:
            stat = os.stat(file_path)
            return {
                'filename': os.path.basename(file_path),
                'file_size': stat.st_size,
                'file_ext': os.path.splitext(file_path)[1].lower().lstrip('.'),
                'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'encoding': detect_file_encoding(file_path) if file_path.endswith('.csv') else 'utf-8'
            }
        except Exception as e:
            logger.warning(f"获取文件信息失败: {file_path}, 错误: {e}")
            return {}
    
    def _parse_excel_file(self, file_path: str, result: ParseResult) -> ParseResult:
        """解析Excel文件"""
        logger.info(f"开始解析Excel文件: {file_path}")
        
        # 验证Excel文件
        is_valid, error_msg = validate_excel_file(file_path)
        if not is_valid:
            result.error_message = error_msg
            return result
        
        # 读取Excel文件
        try:
            import pandas as pd
            df = pd.read_excel(file_path)
            
            # 解析数据
            return self._parse_dataframe(df, result)
        except Exception as e:
            result.error_message = f"读取Excel文件失败: {str(e)}"
            return result
    
    def _parse_csv_file(self, file_path: str, result: ParseResult) -> ParseResult:
        """解析CSV文件"""
        logger.info(f"开始解析CSV文件: {file_path}")
        
        # 验证CSV文件
        is_valid, error_msg = validate_csv_file(file_path)
        if not is_valid:
            result.error_message = error_msg
            return result
        
        # 读取CSV文件
        try:
            import pandas as pd
            df = pd.read_csv(file_path, encoding='utf-8')
            
            # 解析数据
            return self._parse_dataframe(df, result)
        except UnicodeDecodeError:
            try:
                # 尝试其他编码
                df = pd.read_csv(file_path, encoding='gbk')
                return self._parse_dataframe(df, result)
            except Exception as e:
                result.error_message = f"读取CSV文件失败（编码问题）: {str(e)}"
                return result
        except Exception as e:
            result.error_message = f"读取CSV文件失败: {str(e)}"
            return result
    
    def _parse_dataframe(self, df: pd.DataFrame, result: ParseResult) -> ParseResult:
        """解析DataFrame数据"""
        result.total_rows = len(df)
        
        # 查找URL列
        url_column = self._find_url_column(df.columns)
        if not url_column:
            result.error_message = f"未找到URL列，支持的列名: {', '.join(self.url_column_names)}"
            return result
        
        logger.info(f"找到URL列: {url_column}")
        
        # 提取和验证URL
        urls = df[url_column].dropna().astype(str).tolist()
        
        for url in urls:
            url = url.strip()
            if not url or url.lower() in ['nan', 'null', '']:
                continue
            
            # 标准化URL
            normalized_url = normalize_url(url)
            
            # 验证URL
            if is_valid_url(normalized_url):
                result.valid_urls.append(normalized_url)
            else:
                result.invalid_urls.append(url)
        
        # 去重
        result.valid_urls = list(set(result.valid_urls))
        result.invalid_urls = list(set(result.invalid_urls))
        
        result.success = True
        
        logger.info(f"数据解析完成，总行数: {result.total_rows}, 有效URL: {len(result.valid_urls)}, 无效URL: {len(result.invalid_urls)}")
        
        return result
    
    def _find_url_column(self, columns: List[str]) -> Optional[str]:
        """查找URL列"""
        # 将列名转换为小写进行匹配
        columns_lower = [col.lower() for col in columns]
        
        for url_name in self.url_column_names:
            url_name_lower = url_name.lower()
            if url_name_lower in columns_lower:
                # 返回原始列名
                index = columns_lower.index(url_name_lower)
                return columns[index]
        
        return None
    
    def parse_batch_files(self, file_paths: List[str]) -> List[ParseResult]:
        """
        批量解析文件
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            解析结果列表
        """
        logger.info(f"开始批量解析 {len(file_paths)} 个文件")
        results = []
        
        for file_path in file_paths:
            try:
                result = self.parse_file(file_path)
                results.append(result)
            except Exception as e:
                logger.error(f"批量解析文件异常: {file_path}, 错误: {e}")
                error_result = ParseResult()
                error_result.error_message = f"解析异常: {str(e)}"
                error_result.file_info = {'filename': os.path.basename(file_path)}
                results.append(error_result)
        
        # 统计批量解析结果
        self._log_batch_statistics(results)
        
        return results
    
    def _log_batch_statistics(self, results: List[ParseResult]):
        """记录批量解析统计信息"""
        total_files = len(results)
        success_files = sum(1 for r in results if r.success)
        total_urls = sum(len(r.valid_urls) for r in results)
        total_invalid = sum(len(r.invalid_urls) for r in results)
        
        logger.info(f"批量解析统计:")
        logger.info(f"  文件总数: {total_files}")
        logger.info(f"  成功解析: {success_files} ({success_files/total_files*100:.1f}%)")
        logger.info(f"  有效URL: {total_urls}")
        logger.info(f"  无效URL: {total_invalid}")
    
    def merge_parse_results(self, results: List[ParseResult]) -> ParseResult:
        """
        合并多个解析结果
        
        Args:
            results: 解析结果列表
            
        Returns:
            合并后的解析结果
        """
        merged_result = ParseResult()
        
        all_valid_urls = []
        all_invalid_urls = []
        total_rows = 0
        error_messages = []
        
        for result in results:
            if result.success:
                all_valid_urls.extend(result.valid_urls)
                all_invalid_urls.extend(result.invalid_urls)
                total_rows += result.total_rows
            else:
                error_messages.append(f"{result.file_info.get('filename', 'unknown')}: {result.error_message}")
        
        # 去重
        merged_result.valid_urls = list(set(all_valid_urls))
        merged_result.invalid_urls = list(set(all_invalid_urls))
        merged_result.total_rows = total_rows
        
        # 判断整体成功状态
        merged_result.success = len(merged_result.valid_urls) > 0
        
        if error_messages:
            merged_result.error_message = "; ".join(error_messages)
        
        logger.info(f"合并解析结果: 有效URL {len(merged_result.valid_urls)}, 无效URL {len(merged_result.invalid_urls)}")
        
        return merged_result
    
    def export_urls_to_file(self, urls: List[str], output_path: str, file_format: str = 'csv') -> bool:
        """
        导出URL列表到文件
        
        Args:
            urls: URL列表
            output_path: 输出文件路径
            file_format: 文件格式 ('csv' 或 'xlsx')
            
        Returns:
            是否导出成功
        """
        try:
            # 创建DataFrame
            df = pd.DataFrame({'网址': urls})
            
            # 根据格式导出
            if file_format.lower() == 'csv':
                df.to_csv(output_path, index=False, encoding='utf-8-sig')
            elif file_format.lower() in ['xlsx', 'excel']:
                df.to_excel(output_path, index=False)
            else:
                logger.error(f"不支持的导出格式: {file_format}")
                return False
            
            logger.info(f"URL列表导出成功: {output_path}, 数量: {len(urls)}")
            return True
            
        except Exception as e:
            logger.error(f"URL列表导出失败: {output_path}, 错误: {e}")
            return False
    
    def validate_file_format(self, file_path: str) -> Tuple[bool, str]:
        """
        验证文件格式是否支持
        
        Args:
            file_path: 文件路径
            
        Returns:
            (是否支持, 错误信息)
        """
        if not os.path.exists(file_path):
            return False, "文件不存在"
        
        file_ext = os.path.splitext(file_path)[1].lower().lstrip('.')
        
        if file_ext not in self.supported_extensions:
            return False, f"不支持的文件格式: {file_ext}, 支持的格式: {', '.join(self.supported_extensions)}"
        
        return True, "" 