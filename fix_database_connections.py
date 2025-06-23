#!/usr/bin/env python3
"""
修复数据库连接泄漏问题的脚本
"""

import os
import re

def fix_database_usage(file_path):
    """修复单个文件中的数据库使用方式"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找并替换 db: Session = get_db() 模式
        pattern = r'(\s*)db:\s*Session\s*=\s*get_db\(\)\s*\n'
        replacement = r'\1with get_db() as db:\n'
        content = re.sub(pattern, replacement, content)
        
        # 查找并替换 db = get_db() 模式
        pattern = r'(\s*)db\s*=\s*get_db\(\)\s*\n'
        replacement = r'\1with get_db() as db:\n'
        content = re.sub(pattern, replacement, content)
        
        # 修复缩进问题 - 将with语句后的代码块向右缩进
        lines = content.split('\n')
        new_lines = []
        in_with_block = False
        base_indent = 0
        
        for i, line in enumerate(lines):
            if 'with get_db() as db:' in line:
                new_lines.append(line)
                in_with_block = True
                base_indent = len(line) - len(line.lstrip())
                continue
            
            if in_with_block:
                # 检查是否是下一个函数或类的开始
                if line.strip() and not line.startswith(' ' * (base_indent + 4)) and not line.strip().startswith('#'):
                    if any(keyword in line for keyword in ['def ', 'class ', '@', 'except', 'finally']):
                        in_with_block = False
                
                if in_with_block and line.strip():
                    # 确保适当的缩进
                    current_indent = len(line) - len(line.lstrip())
                    if current_indent <= base_indent:
                        line = ' ' * (base_indent + 4) + line.lstrip()
            
            new_lines.append(line)
        
        new_content = '\n'.join(new_lines)
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"已修复: {file_path}")
        return True
        
    except Exception as e:
        print(f"修复失败 {file_path}: {e}")
        return False

def main():
    """主函数"""
    api_files = [
        'backend/api/tasks.py',
        'backend/api/results.py',
        'backend/api/websites.py'
    ]
    
    success_count = 0
    
    for file_path in api_files:
        if os.path.exists(file_path):
            if fix_database_usage(file_path):
                success_count += 1
        else:
            print(f"文件不存在: {file_path}")
    
    print(f"\n修复完成: {success_count}/{len(api_files)} 个文件")

if __name__ == '__main__':
    main() 