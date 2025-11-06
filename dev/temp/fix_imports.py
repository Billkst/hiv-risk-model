#!/usr/bin/env python3
"""
Fix relative imports to absolute imports in all reorg_tool modules.
"""

import os
import re
from pathlib import Path

def fix_imports_in_file(filepath):
    """Fix relative imports in a single file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace relative imports with absolute imports
    # Pattern: from .module import ...
    content = re.sub(r'^from \.(\w+) import', r'from \1 import', content, flags=re.MULTILINE)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed: {filepath}")

def main():
    """Fix all Python files in reorg_tool directory."""
    reorg_dir = Path(__file__).parent
    
    for py_file in reorg_dir.glob('*.py'):
        if py_file.name != 'fix_imports.py':
            fix_imports_in_file(py_file)
    
    print("\nAll imports fixed!")

if __name__ == '__main__':
    main()
