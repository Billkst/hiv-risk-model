#!/usr/bin/env python3
"""
领域知识先验定义
基于医学专家知识和Phase 2相关性分析结果
"""

import numpy as np


class DomainKnowledgePriors:
    """
    领域知识先验管理器
    
    定义已知的正负相关特征，并为每个特征分配先验权重
    """
    
    def __init__(self, feature_names):
        """
        初始化领域知识先验
        
        Args:
            feature_names: 模型特征名称列表（110个）
        """
        self.feature_names = feature_names
        self.n_features = len(feature_names)
        
        # 定义已知正相关特征（增加风险）
        self.positive_features = {
            '感染率': 1.3,          # 强正相关 (r=+0.746)
            '存活数': 1.3,          # 强正相关 (r=+0.656)
            '新报告': 1.2,          # 强正相关 (r=+0.406)
            '注射吸毒者规模': 1.3,   # 强正相关 (r=+0.616)
            '既往阳性嫖客数': 1.1,   # 中等正相关 (r=+0.201)
            '嫖客HIV检测阳性率': 1.2, # 强正相关 (r=+0.311)
            '既往阳性暗娼数': 1.1,   # 中等正相关 (r=+0.279)
            '暗娼HIV检测阳性率': 1.2, # 强正相关 (r=+0.433)
            # 新发现的显著特征
            '存活_注射毒品': 1.3,    # 强正相关 (r=+0.642)
            '新报告_5-': 1.2,       # 强正相关 (r=+0.636)
            '病载小于50占现存活比例': 1.1, # 中等正相关 (r=+0.361)
        }
        
        # 定义已知负相关特征（降低风险）
        # 注意：Phase 2发现这些特征实际为正相关，但我们保留医学理论预期
        # 在实际应用中可以选择使用或不使用这些先验
        self.negative_features = {
            # 暂时不使用负相关先验，因为Phase 2验证失败
            # 如果需要，可以取消注释：
            # '治疗覆盖率': 0.9,
            # '病毒抑制比例': 0.9,
        }
        
        # 初始化先验权重
        self.priors = self._init_priors()
        
        print(f"✓ 领域知识先验初始化完成")
        print(f"  特征总数: {self.n_features}")
        print(f"  正相关先验: {len(self.positive_features)}个")
        print(f"  负相关先验: {len(self.negative_features)}个")
        print(f"  中性特征: {self.n_features - len(self.positive_features) - len(self.negative_features)}个")
    
    def _init_priors(self):
        """
        初始化先验权重向量
        
        Returns:
            np.ndarray: 先验权重向量 (n_features,)
        """
        # 默认所有特征权重为1.0（中性）
        priors = np.ones(self.n_features, dtype=np.float32)
        
        # 应用正相关先验
        for feature_name, weight in self.positive_features.items():
            if feature_name in self.feature_names:
                idx = self.feature_names.index(feature_name)
                priors[idx] = weight
        
        # 应用负相关先验
        for feature_name, weight in self.negative_features.items():
            if feature_name in self.feature_names:
                idx = self.feature_names.index(feature_name)
                priors[idx] = weight
        
        return priors
    
    def get_priors(self):
        """
        获取先验权重向量
        
        Returns:
            np.ndarray: 先验权重向量 (n_features,)
        """
        return self.priors.copy()
    
    def get_feature_prior(self, feature_name):
        """
        获取单个特征的先验权重
        
        Args:
            feature_name: 特征名称
        
        Returns:
            float: 先验权重
        """
        if feature_name in self.feature_names:
            idx = self.feature_names.index(feature_name)
            return float(self.priors[idx])
        return 1.0
    
    def get_prior_statistics(self):
        """
        获取先验权重统计信息
        
        Returns:
            dict: 统计信息
        """
        stats = {
            'total_features': self.n_features,
            'positive_priors': len(self.positive_features),
            'negative_priors': len(self.negative_features),
            'neutral_features': self.n_features - len(self.positive_features) - len(self.negative_features),
            'prior_range': (float(self.priors.min()), float(self.priors.max())),
            'prior_mean': float(self.priors.mean()),
            'prior_std': float(self.priors.std())
        }
        return stats
    
    def visualize_priors(self):
        """
        可视化先验权重分布
        """
        print("\n" + "="*60)
        print("  领域知识先验权重分布")
        print("="*60)
        
        # 统计不同权重的特征数量
        unique_weights = np.unique(self.priors)
        print(f"\n权重类别:")
        for weight in sorted(unique_weights, reverse=True):
            count = np.sum(self.priors == weight)
            percentage = count / self.n_features * 100
            
            if weight > 1.0:
                category = "正相关（增加风险）"
            elif weight < 1.0:
                category = "负相关（降低风险）"
            else:
                category = "中性（未知）"
            
            print(f"  权重 {weight:.1f} ({category}): {count}个特征 ({percentage:.1f}%)")
        
        # 显示具体的正相关特征
        print(f"\n正相关特征详情:")
        for feature_name, weight in sorted(self.positive_features.items(), 
                                          key=lambda x: x[1], reverse=True):
            if feature_name in self.feature_names:
                print(f"  {feature_name:30s} → 权重 {weight:.1f}")
        
        # 显示具体的负相关特征（如果有）
        if self.negative_features:
            print(f"\n负相关特征详情:")
            for feature_name, weight in sorted(self.negative_features.items(), 
                                              key=lambda x: x[1]):
                if feature_name in self.feature_names:
                    print(f"  {feature_name:30s} → 权重 {weight:.1f}")
        
        print("\n" + "="*60)


def load_domain_priors(feature_names):
    """
    加载领域知识先验
    
    Args:
        feature_names: 特征名称列表
    
    Returns:
        DomainKnowledgePriors: 先验管理器实例
    """
    return DomainKnowledgePriors(feature_names)


def main():
    """
    演示领域知识先验的使用
    """
    print("="*80)
    print("  领域知识先验演示")
    print("="*80)
    
    # 模拟加载特征名称（实际使用时从模型加载）
    import joblib
    model_info = joblib.load('saved_models/final_model_3to5.pkl')
    feature_names = model_info['feature_columns']
    
    print(f"\n加载模型特征: {len(feature_names)}个")
    
    # 初始化先验
    priors_manager = DomainKnowledgePriors(feature_names)
    
    # 可视化先验分布
    priors_manager.visualize_priors()
    
    # 获取先验权重向量
    priors = priors_manager.get_priors()
    print(f"\n先验权重向量形状: {priors.shape}")
    print(f"先验权重范围: [{priors.min():.2f}, {priors.max():.2f}]")
    
    # 获取统计信息
    stats = priors_manager.get_prior_statistics()
    print(f"\n统计信息:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # 查询特定特征的先验
    print(f"\n特定特征先验查询:")
    test_features = ['感染率', '存活数', '治疗覆盖率', '人口数']
    for feature in test_features:
        prior = priors_manager.get_feature_prior(feature)
        print(f"  {feature:20s}: {prior:.2f}")
    
    print("\n" + "="*80)
    print("✓ 演示完成")
    print("="*80)


if __name__ == '__main__':
    main()
