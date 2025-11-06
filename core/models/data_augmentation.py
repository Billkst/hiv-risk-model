"""
数据增强模块
使用 SMOTE 和噪声注入增强训练数据
"""

import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE, ADASYN
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')


class DataAugmenter:
    """数据增强器"""
    
    def __init__(self, method='smote', random_state=42):
        """
        初始化数据增强器
        
        Args:
            method: 增强方法 ('smote', 'adasyn', 'noise')
            random_state: 随机种子
        """
        self.method = method
        self.random_state = random_state
        self.augmenter = None
        
    def augment_with_smote(self, X, y, sampling_strategy='auto', k_neighbors=5):
        """
        使用 SMOTE 进行过采样
        
        Args:
            X: 特征矩阵
            y: 目标变量
            sampling_strategy: 采样策略
            k_neighbors: SMOTE 的邻居数
        """
        print("\n" + "=" * 60)
        print("SMOTE 数据增强")
        print("=" * 60)
        
        print(f"\n原始数据分布:")
        unique, counts = np.unique(y, return_counts=True)
        for cls, count in zip(unique, counts):
            print(f"  等级 {cls}: {count} 样本")
        
        # 检查最小类别样本数
        min_samples = counts.min()
        
        # 调整 k_neighbors
        if min_samples <= k_neighbors:
            k_neighbors = max(1, min_samples - 1)
            print(f"\n⚠️  最小类别样本数 {min_samples}，调整 k_neighbors = {k_neighbors}")
        
        try:
            # 创建 SMOTE 对象
            smote = SMOTE(
                sampling_strategy=sampling_strategy,
                k_neighbors=k_neighbors,
                random_state=self.random_state
            )
            
            # 应用 SMOTE
            X_resampled, y_resampled = smote.fit_resample(X, y)
            
            print(f"\n增强后数据分布:")
            unique, counts = np.unique(y_resampled, return_counts=True)
            for cls, count in zip(unique, counts):
                print(f"  等级 {cls}: {count} 样本")
            
            print(f"\n✓ SMOTE 增强完成")
            print(f"  原始样本数: {len(X)}")
            print(f"  增强后样本数: {len(X_resampled)}")
            print(f"  增加样本数: {len(X_resampled) - len(X)}")
            
            return X_resampled, y_resampled
            
        except Exception as e:
            print(f"\n⚠️  SMOTE 失败: {e}")
            print(f"  返回原始数据")
            return X, y
    
    def augment_with_adasyn(self, X, y, sampling_strategy='auto', n_neighbors=5):
        """
        使用 ADASYN 进行自适应过采样
        """
        print("\n" + "=" * 60)
        print("ADASYN 数据增强")
        print("=" * 60)
        
        print(f"\n原始数据分布:")
        unique, counts = np.unique(y, return_counts=True)
        for cls, count in zip(unique, counts):
            print(f"  等级 {cls}: {count} 样本")
        
        min_samples = counts.min()
        if min_samples <= n_neighbors:
            n_neighbors = max(1, min_samples - 1)
            print(f"\n⚠️  调整 n_neighbors = {n_neighbors}")
        
        try:
            adasyn = ADASYN(
                sampling_strategy=sampling_strategy,
                n_neighbors=n_neighbors,
                random_state=self.random_state
            )
            
            X_resampled, y_resampled = adasyn.fit_resample(X, y)
            
            print(f"\n增强后数据分布:")
            unique, counts = np.unique(y_resampled, return_counts=True)
            for cls, count in zip(unique, counts):
                print(f"  等级 {cls}: {count} 样本")
            
            print(f"\n✓ ADASYN 增强完成")
            print(f"  增加样本数: {len(X_resampled) - len(X)}")
            
            return X_resampled, y_resampled
            
        except Exception as e:
            print(f"\n⚠️  ADASYN 失败: {e}")
            return X, y
    
    def add_gaussian_noise(self, X, noise_level=0.01, n_augment=1):
        """
        添加高斯噪声进行数据增强
        
        Args:
            X: 特征矩阵
            noise_level: 噪声水平（相对于特征标准差）
            n_augment: 每个样本生成的增强样本数
        """
        print("\n" + "=" * 60)
        print("高斯噪声数据增强")
        print("=" * 60)
        
        X_augmented = [X]
        
        for i in range(n_augment):
            # 计算每个特征的标准差
            std = np.std(X, axis=0)
            
            # 生成噪声
            noise = np.random.normal(0, noise_level * std, X.shape)
            
            # 添加噪声
            X_noisy = X + noise
            X_augmented.append(X_noisy)
        
        X_result = np.vstack(X_augmented)
        
        print(f"\n✓ 噪声增强完成")
        print(f"  原始样本数: {len(X)}")
        print(f"  增强后样本数: {len(X_result)}")
        print(f"  噪声水平: {noise_level}")
        
        return X_result
    
    def augment(self, X, y, method=None, **kwargs):
        """
        统一的数据增强接口
        """
        if method is None:
            method = self.method
        
        if method == 'smote':
            return self.augment_with_smote(X, y, **kwargs)
        elif method == 'adasyn':
            return self.augment_with_adasyn(X, y, **kwargs)
        elif method == 'noise':
            X_aug = self.add_gaussian_noise(X, **kwargs)
            y_aug = np.tile(y, kwargs.get('n_augment', 1) + 1)
            return X_aug, y_aug
        else:
            print(f"⚠️  未知的增强方法: {method}")
            return X, y


def compare_augmentation_methods(X, y):
    """比较不同数据增强方法的效果"""
    print("\n" + "=" * 80)
    print("数据增强方法对比")
    print("=" * 80)
    
    methods = {
        'SMOTE': {'method': 'smote', 'k_neighbors': 3},
        'ADASYN': {'method': 'adasyn', 'n_neighbors': 3},
        'Gaussian Noise': {'method': 'noise', 'noise_level': 0.05, 'n_augment': 2}
    }
    
    results = {}
    
    for name, params in methods.items():
        print(f"\n{'='*60}")
        print(f"测试方法: {name}")
        print(f"{'='*60}")
        
        augmenter = DataAugmenter()
        method = params.pop('method')
        
        try:
            X_aug, y_aug = augmenter.augment(X, y, method=method, **params)
            
            results[name] = {
                'X': X_aug,
                'y': y_aug,
                'original_size': len(X),
                'augmented_size': len(X_aug),
                'increase': len(X_aug) - len(X)
            }
            
        except Exception as e:
            print(f"⚠️  {name} 失败: {e}")
            results[name] = None
    
    # 汇总对比
    print("\n" + "=" * 80)
    print("增强效果汇总")
    print("=" * 80)
    
    comparison_data = []
    for name, result in results.items():
        if result:
            comparison_data.append({
                '方法': name,
                '原始样本数': result['original_size'],
                '增强后样本数': result['augmented_size'],
                '增加样本数': result['increase'],
                '增长率': f"{result['increase']/result['original_size']*100:.1f}%"
            })
    
    df = pd.DataFrame(comparison_data)
    print(df.to_string(index=False))
    
    return results


def main():
    """测试数据增强"""
    print("\n" + "=" * 80)
    print("数据增强测试")
    print("=" * 80)
    
    # 加载数据
    print("\n步骤 1: 加载数据")
    df = pd.read_csv('data/processed/hiv_data_processed.csv')
    
    # 使用原始的"按方案评定级别"作为目标
    exclude_columns = ['区县', '按方案评定级别', 'risk_level']
    feature_columns = [col for col in df.columns if col not in exclude_columns]
    
    X = df[feature_columns].values
    y = df['按方案评定级别'].values
    
    print(f"✓ 数据加载成功")
    print(f"  特征数: {X.shape[1]}")
    print(f"  样本数: {X.shape[0]}")
    
    # 标准化
    print("\n步骤 2: 特征标准化")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    print("✓ 标准化完成")
    
    # 比较不同增强方法
    print("\n步骤 3: 比较增强方法")
    results = compare_augmentation_methods(X_scaled, y)
    
    # 推荐最佳方法
    print("\n" + "=" * 80)
    print("推荐方案")
    print("=" * 80)
    print("\n建议使用 SMOTE 方法:")
    print("  - 专门为分类问题设计")
    print("  - 生成合理的合成样本")
    print("  - 保持类别间的边界")
    
    return results


if __name__ == '__main__':
    results = main()
