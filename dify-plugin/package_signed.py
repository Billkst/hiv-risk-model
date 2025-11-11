#!/usr/bin/env python3
"""
Dify 插件打包工具（带签名）
"""
import os
import sys
import zipfile
import hashlib
import json
from pathlib import Path

def calculate_file_hash(filepath):
    """计算文件的 SHA256 哈希"""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def should_exclude(path):
    """判断文件是否应该被排除"""
    exclude_patterns = [
        '__pycache__',
        '.pyc',
        '.pyo',
        '.pyd',
        'venv',
        'venv_py312',
        '.env',
        'working',
        '.sh',
        'test_local.py',
        'test_upload_data.csv',
        'test_data.csv',
        '远程调试指南.md',
        '.git',
        'package.py',
        'package_signed.py',
        'package.sh',
        '.difpkg',
        '.difypkg'
    ]
    
    path_str = str(path)
    return any(pattern in path_str for pattern in exclude_patterns)

def create_manifest_signature(manifest_path):
    """创建 manifest 签名文件"""
    manifest_hash = calculate_file_hash(manifest_path)
    
    signature = {
        "version": "1.0",
        "manifest_hash": manifest_hash,
        "algorithm": "sha256"
    }
    
    return signature

def main():
    print("=" * 50)
    print("Dify 插件打包工具（带签名）")
    print("=" * 50)
    print()
    
    # 检查 manifest.yaml
    if not os.path.exists('manifest.yaml'):
        print("❌ 找不到 manifest.yaml")
        return False
    
    # 读取版本信息
    import yaml
    with open('manifest.yaml', 'r', encoding='utf-8') as f:
        manifest = yaml.safe_load(f)
    
    version = manifest['version']
    plugin_name = manifest['name']
    package_name = f"{plugin_name}-{version}.difypkg"
    
    print(f"插件名称: {plugin_name}")
    print(f"版本号: {version}")
    print(f"包文件名: {package_name}")
    print()
    
    # 创建签名
    print("创建签名...")
    signature = create_manifest_signature('manifest.yaml')
    
    # 保存签名文件
    signature_file = '.signature.json'
    with open(signature_file, 'w', encoding='utf-8') as f:
        json.dump(signature, f, indent=2)
    print(f"✓ 签名文件已创建: {signature_file}")
    print()
    
    # 创建 ZIP 包
    print("打包中...")
    file_list = []
    with zipfile.ZipFile(package_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk('.'):
            # 过滤目录
            dirs[:] = [d for d in dirs if not should_exclude(Path(root) / d)]
            
            for file in files:
                file_path = Path(root) / file
                if not should_exclude(file_path):
                    arcname = str(file_path.relative_to('.'))
                    zipf.write(file_path, arcname)
                    file_list.append(arcname)
                    print(f"  添加: {arcname}")
    
    # 删除临时签名文件
    if os.path.exists(signature_file):
        os.remove(signature_file)
    
    # 获取文件大小
    size_bytes = os.path.getsize(package_name)
    size_mb = size_bytes / (1024 * 1024)
    
    print()
    print("=" * 50)
    print("✓ 打包成功！")
    print("=" * 50)
    print()
    print(f"包文件: {package_name}")
    print(f"文件大小: {size_mb:.2f} MB")
    print(f"包含文件数: {len(file_list)}")
    print()
    
    return True

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ 打包失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
