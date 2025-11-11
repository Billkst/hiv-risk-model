#!/usr/bin/env python3
"""
HIV 风险预测插件 - 签名和打包工具
"""
import os
import zipfile
import yaml
import hashlib
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

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
        'sign_and_package.py',
        'package.sh',
        '.difpkg',
        '.sig',
        'signature'
    ]
    
    path_str = str(path)
    return any(pattern in path_str for pattern in exclude_patterns)

def create_unsigned_package(package_name):
    """创建未签名的插件包"""
    print("创建未签名的插件包...")
    with zipfile.ZipFile(package_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk('.'):
            # 过滤目录
            dirs[:] = [d for d in dirs if not should_exclude(Path(root) / d)]
            
            for file in files:
                file_path = Path(root) / file
                if not should_exclude(file_path):
                    arcname = str(file_path.relative_to('.'))
                    zipf.write(file_path, arcname)
                    print(f"  添加: {arcname}")
    print(f"✓ 未签名包创建完成: {package_name}")

def sign_package(package_path, private_key_path):
    """对插件包进行签名"""
    print(f"\n对插件包进行签名...")
    
    # 读取私钥
    with open(private_key_path, 'rb') as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )
    
    # 计算包文件的哈希
    sha256_hash = hashlib.sha256()
    with open(package_path, 'rb') as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    package_hash = sha256_hash.digest()
    print(f"  包文件哈希: {package_hash.hex()}")
    
    # 使用私钥签名
    signature = private_key.sign(
        package_hash,
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    
    # 保存签名文件
    signature_path = package_path + '.sig'
    with open(signature_path, 'wb') as sig_file:
        sig_file.write(signature)
    
    print(f"✓ 签名文件创建完成: {signature_path}")
    return signature_path

def main():
    print("=" * 50)
    print("HIV 风险预测插件 - 签名和打包工具")
    print("=" * 50)
    print()
    
    # 读取版本信息
    with open('manifest.yaml', 'r', encoding='utf-8') as f:
        manifest = yaml.safe_load(f)
    
    version = manifest['version']
    plugin_name = manifest['name']
    package_name = f"{plugin_name}.difypkg"
    
    print(f"插件名称: {plugin_name}")
    print(f"版本号: {version}")
    print(f"包文件名: {package_name}")
    print()
    
    # 检查必要文件
    print("检查必要文件...")
    required_files = ['manifest.yaml', 'README.md', 'PRIVACY.md', 'requirements.txt', 'main.py']
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ 缺少必要文件: {file}")
            return False
        print(f"✓ {file}")
    
    # 检查私钥文件
    private_key_path = '../hiv_plugin_key.private.pem'
    if not os.path.exists(private_key_path):
        print(f"❌ 缺少私钥文件: {private_key_path}")
        print("请先生成密钥对！")
        return False
    print(f"✓ 私钥文件: {private_key_path}")
    print()
    
    # 创建未签名的包
    create_unsigned_package(package_name)
    
    # 对包进行签名
    signature_path = sign_package(package_name, private_key_path)
    
    # 获取文件大小
    size_bytes = os.path.getsize(package_name)
    size_mb = size_bytes / (1024 * 1024)
    
    print()
    print("=" * 50)
    print("✓ 打包和签名成功！")
    print("=" * 50)
    print()
    print(f"包文件: {package_name}")
    print(f"签名文件: {signature_path}")
    print(f"文件大小: {size_mb:.2f} MB")
    print()
    print("下一步操作：")
    print("1. 上传这两个文件到 Dify:")
    print(f"   - {package_name}")
    print(f"   - {signature_path}")
    print()
    
    return True

if __name__ == '__main__':
    try:
        success = main()
        exit(0 if success else 1)
    except Exception as e:
        print(f"❌ 打包失败: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
