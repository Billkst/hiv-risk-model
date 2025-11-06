"""
模型版本管理器
用于备份、恢复和管理模型版本
"""

import os
import json
import shutil
import joblib
import logging
from datetime import datetime
from typing import Dict, Optional, List
import numpy as np
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelVersionManager:
    """
    模型版本管理器
    
    功能：
    - 自动备份模型
    - 版本注册和追踪
    - 性能对比
    - 一键回滚
    """
    
    def __init__(self, models_dir='saved_models'):
        """
        初始化版本管理器
        
        Args:
            models_dir: 模型保存目录
        """
        self.models_dir = models_dir
        self.registry_path = os.path.join(models_dir, 'model_registry.json')
        
        # 确保目录存在
        os.makedirs(models_dir, exist_ok=True)
        
        # 加载或创建版本注册表
        self.registry = self._load_registry()
        
        logger.info(f"ModelVersionManager initialized. Models dir: {models_dir}")
    
    def _load_registry(self) -> Dict:
        """加载版本注册表"""
        if os.path.exists(self.registry_path):
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 创建新的注册表
            return {
                'versions': [],
                'current_production': None
            }
    
    def _save_registry(self):
        """保存版本注册表"""
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump(self.registry, f, indent=2, ensure_ascii=False)
        logger.info(f"Registry saved to {self.registry_path}")
    
    def backup_current_model(self, model_path='saved_models/final_model_3to5.pkl',
                            version='1.0', description='Original model backup') -> str:
        """
        备份当前生产模型
        
        Args:
            model_path: 当前模型路径
            version: 版本号
            description: 版本描述
            
        Returns:
            备份文件路径
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        # 生成备份文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"final_model_3to5_v{version}_backup_{timestamp}.pkl"
        backup_path = os.path.join(self.models_dir, backup_filename)
        
        # 复制模型文件
        shutil.copy(model_path, backup_path)
        logger.info(f"✓ Model backed up: {backup_path}")
        
        # 评估模型性能（如果有测试数据）
        performance = self._evaluate_model(model_path)
        
        # 注册版本
        self.register_version({
            'version': f'{version}_backup',
            'type': 'backup',
            'path': backup_path,
            'timestamp': timestamp,
            'datetime': datetime.now().isoformat(),
            'performance': performance,
            'status': 'archived',
            'description': description
        })
        
        return backup_path
    
    def register_version(self, version_info: Dict):
        """
        注册新版本到注册表
        
        Args:
            version_info: 版本信息字典
        """
        # 检查版本是否已存在
        existing = [v for v in self.registry['versions'] 
                   if v['version'] == version_info['version']]
        
        if existing:
            logger.warning(f"Version {version_info['version']} already exists, updating...")
            # 更新现有版本
            for i, v in enumerate(self.registry['versions']):
                if v['version'] == version_info['version']:
                    self.registry['versions'][i] = version_info
                    break
        else:
            # 添加新版本
            self.registry['versions'].append(version_info)
        
        self._save_registry()
        logger.info(f"✓ Version {version_info['version']} registered")
    
    def get_version_info(self, version: str) -> Optional[Dict]:
        """
        获取指定版本的信息
        
        Args:
            version: 版本号
            
        Returns:
            版本信息字典，如果不存在返回None
        """
        for v in self.registry['versions']:
            if v['version'] == version:
                return v
        return None
    
    def list_versions(self) -> List[Dict]:
        """
        列出所有版本
        
        Returns:
            版本列表
        """
        return self.registry['versions']
    
    def rollback_to_version(self, version: str, 
                           production_path='saved_models/final_model_3to5.pkl') -> Dict:
        """
        回滚到指定版本
        
        Args:
            version: 目标版本号
            production_path: 生产模型路径
            
        Returns:
            回滚后的版本信息
        """
        version_info = self.get_version_info(version)
        if not version_info:
            raise ValueError(f"Version {version} not found in registry")
        
        if not os.path.exists(version_info['path']):
            raise FileNotFoundError(f"Version file not found: {version_info['path']}")
        
        # 先备份当前生产模型（以防回滚失败）
        if os.path.exists(production_path):
            logger.info("Backing up current production model before rollback...")
            self.backup_current_model(
                production_path,
                version='pre_rollback',
                description=f'Backup before rollback to {version}'
            )
        
        # 复制目标版本到生产路径
        shutil.copy(version_info['path'], production_path)
        logger.info(f"✓ Rolled back to version {version}")
        
        # 更新当前生产版本
        self.registry['current_production'] = version
        self._save_registry()
        
        return version_info
    
    def compare_versions(self, version1: str, version2: str) -> Dict:
        """
        对比两个版本的性能
        
        Args:
            version1: 版本1
            version2: 版本2
            
        Returns:
            对比结果字典
        """
        v1_info = self.get_version_info(version1)
        v2_info = self.get_version_info(version2)
        
        if not v1_info or not v2_info:
            raise ValueError("One or both versions not found")
        
        v1_perf = v1_info.get('performance', {})
        v2_perf = v2_info.get('performance', {})
        
        comparison = {
            'version1': version1,
            'version2': version2,
            'v1_performance': v1_perf,
            'v2_performance': v2_perf,
            'differences': {}
        }
        
        # 计算差异
        for metric in ['f1', 'accuracy', 'avg_time_ms']:
            if metric in v1_perf and metric in v2_perf:
                diff = v2_perf[metric] - v1_perf[metric]
                comparison['differences'][metric] = {
                    'absolute': diff,
                    'relative_pct': (diff / v1_perf[metric] * 100) if v1_perf[metric] != 0 else 0
                }
        
        return comparison
    
    def _evaluate_model(self, model_path: str) -> Dict:
        """
        评估模型性能
        
        Args:
            model_path: 模型文件路径
            
        Returns:
            性能指标字典
        """
        try:
            # 加载模型
            model_info = joblib.load(model_path)
            
            # 基本信息
            performance = {
                'model_type': model_info.get('model_name', 'unknown'),
                'feature_count': len(model_info.get('feature_columns', [])),
                'model_size_mb': os.path.getsize(model_path) / (1024 * 1024)
            }
            
            # 如果有测试数据，可以计算F1等指标
            # 这里先返回基本信息
            logger.info(f"Model evaluated: {performance}")
            
            return performance
            
        except Exception as e:
            logger.error(f"Failed to evaluate model: {e}")
            return {'error': str(e)}
    
    def validate_enhanced_model(self, enhanced_model_path: str,
                               original_version='1.0',
                               min_f1=0.85,
                               max_time_increase_ms=50) -> Dict:
        """
        验证增强模型是否满足上线标准
        
        Args:
            enhanced_model_path: 增强模型路径
            original_version: 原始版本号
            min_f1: 最小F1分数要求
            max_time_increase_ms: 最大响应时间增加（毫秒）
            
        Returns:
            验证结果字典
        """
        if not os.path.exists(enhanced_model_path):
            return {
                'passed': False,
                'error': f'Enhanced model not found: {enhanced_model_path}'
            }
        
        # 获取原始版本信息
        original_info = self.get_version_info(original_version)
        if not original_info:
            return {
                'passed': False,
                'error': f'Original version {original_version} not found'
            }
        
        # 评估增强模型
        enhanced_perf = self._evaluate_model(enhanced_model_path)
        original_perf = original_info.get('performance', {})
        
        # 验证检查项
        checks = {
            'model_file_exists': os.path.exists(enhanced_model_path),
            'model_loadable': 'error' not in enhanced_perf,
            'feature_count_match': (
                enhanced_perf.get('feature_count') == original_perf.get('feature_count')
                if 'feature_count' in enhanced_perf and 'feature_count' in original_perf
                else True
            )
        }
        
        # 如果有性能指标，进行对比
        if 'f1' in enhanced_perf and 'f1' in original_perf:
            checks['f1_not_decreased'] = enhanced_perf['f1'] >= original_perf['f1'] - 0.01
            checks['f1_meets_threshold'] = enhanced_perf['f1'] >= min_f1
        
        if 'avg_time_ms' in enhanced_perf and 'avg_time_ms' in original_perf:
            time_increase = enhanced_perf['avg_time_ms'] - original_perf['avg_time_ms']
            checks['response_time_acceptable'] = time_increase <= max_time_increase_ms
        
        all_passed = all(checks.values())
        
        result = {
            'passed': all_passed,
            'checks': checks,
            'enhanced_performance': enhanced_perf,
            'original_performance': original_perf,
            'recommendation': 'APPROVE' if all_passed else 'REJECT'
        }
        
        logger.info(f"Validation result: {'PASSED' if all_passed else 'FAILED'}")
        
        return result
    
    def save_enhanced_model(self, model, version='1.1',
                           description='Enhanced model with new features') -> tuple:
        """
        保存增强模型（不覆盖原模型）
        
        Args:
            model: 模型对象或模型信息字典
            version: 版本号
            description: 版本描述
            
        Returns:
            (模型路径, 性能信息)
        """
        # 生成增强模型文件名
        enhanced_filename = f"final_model_3to5_v{version}_enhanced.pkl"
        enhanced_path = os.path.join(self.models_dir, enhanced_filename)
        
        # 保存模型
        joblib.dump(model, enhanced_path)
        logger.info(f"✓ Enhanced model saved: {enhanced_path}")
        
        # 评估性能
        performance = self._evaluate_model(enhanced_path)
        
        # 注册版本
        self.register_version({
            'version': version,
            'type': 'enhanced',
            'path': enhanced_path,
            'timestamp': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'datetime': datetime.now().isoformat(),
            'performance': performance,
            'status': 'testing',
            'description': description
        })
        
        return enhanced_path, performance
    
    def set_production_version(self, version: str):
        """
        设置生产版本
        
        Args:
            version: 版本号
        """
        version_info = self.get_version_info(version)
        if not version_info:
            raise ValueError(f"Version {version} not found")
        
        self.registry['current_production'] = version
        
        # 更新版本状态
        for v in self.registry['versions']:
            if v['version'] == version:
                v['status'] = 'production'
            elif v.get('status') == 'production':
                v['status'] = 'archived'
        
        self._save_registry()
        logger.info(f"✓ Production version set to: {version}")
    
    def print_registry(self):
        """打印版本注册表"""
        print("\n" + "="*80)
        print("Model Version Registry")
        print("="*80)
        print(f"Current Production: {self.registry.get('current_production', 'None')}")
        print(f"Total Versions: {len(self.registry['versions'])}")
        print("\nVersions:")
        print("-"*80)
        
        for v in self.registry['versions']:
            print(f"\nVersion: {v['version']}")
            print(f"  Type: {v.get('type', 'unknown')}")
            print(f"  Status: {v.get('status', 'unknown')}")
            print(f"  Path: {v.get('path', 'N/A')}")
            print(f"  Timestamp: {v.get('datetime', v.get('timestamp', 'N/A'))}")
            print(f"  Description: {v.get('description', 'N/A')}")
            
            if 'performance' in v:
                print(f"  Performance:")
                for key, value in v['performance'].items():
                    print(f"    {key}: {value}")
        
        print("="*80 + "\n")


def demo():
    """演示版本管理功能"""
    print("\n" + "="*80)
    print("Model Version Manager Demo")
    print("="*80)
    
    # 初始化管理器
    manager = ModelVersionManager('hiv_project/hiv_risk_model/saved_models')
    
    # 备份当前模型
    print("\n1. Backing up current model...")
    try:
        backup_path = manager.backup_current_model(
            'hiv_project/hiv_risk_model/saved_models/final_model_3to5.pkl',
            version='1.0',
            description='Original Gradient Boosting model'
        )
        print(f"✓ Backup created: {backup_path}")
    except Exception as e:
        print(f"✗ Backup failed: {e}")
    
    # 打印注册表
    print("\n2. Current registry:")
    manager.print_registry()
    
    print("\n" + "="*80)
    print("✓ Demo completed")
    print("="*80)


if __name__ == '__main__':
    demo()
