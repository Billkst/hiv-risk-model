#!/usr/bin/env python3
"""
批量修复 dev/scripts/ 和 dev/tests/ 中的导入问题
"""

import os
import re
from pathlib import Path

def fix_script(filepath):
    """修复单个脚本的导入问题"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已经有 sys.path 设置
    if 'sys.path.insert' in content or 'sys.path.append' in content:
        print(f"跳过（已有路径设置）: {filepath}")
        return False
    
    # 检查是否需要修复（是否导入了 models 或 utils）
    if not re.search(r'^(from|import)\s+(models|utils|api)', content, re.MULTILINE):
        print(f"跳过（无需修复）: {filepath}")
        return False
    
    # 找到第一个 import 语句的位置
    lines = content.split('\n')
    insert_pos = 0
    
    for i, line in enumerate(lines):
        if line.strip().startswith('"""') or line.strip().startswith("'''"):
            continue
        if line.strip().startswith('import ') or line.strip().startswith('from '):
            insert_pos = i
            break
    
    # 插入 sys.path 设置
    path_setup = """import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

"""
    
    lines.insert(insert_pos, path_setup)
    
    # 写回文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"✅ 已修复: {filepath}")
    return True

def main():
    """修复所有脚本"""
    project_root = Path(__file__).parent
    
    # 修复 dev/scripts/ 下的脚本
    scripts_dir = project_root / 'dev' / 'scripts'
    if scripts_dir.exists():
        print("\n=== 修复 dev/scripts/ ===")
        for py_file in scripts_dir.glob('*.py'):
            fix_script(py_file)
    
    # 修复 dev/tests/ 下的测试
    tests_dir = project_root / 'dev' / 'tests'
    if tests_dir.exists():
        print("\n=== 修复 dev/tests/ ===")
        for py_file in tests_dir.glob('test_*.py'):
            if py_file.name not in ['test_contributions.py', 'test_attention.py']:  # 已经修复过的
                fix_script(py_file)
    
    print("\n✅ 所有脚本修复完成！")

if __name__ == '__main__':
    main()
