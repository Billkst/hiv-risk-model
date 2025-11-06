#!/usr/bin/env python3
"""
领域知识引导的双层自适应注意力预测器
Domain-Guided Dual Adaptive Attention (DG-DAA) Predictor

创新点：
1. 融合医学专家知识（领域先验）
2. 双层注意力机制（特征级 + 样本级）
3. 疫情阶段自适应（低/中/高风险区不同策略）
"""

import numpy as np
import joblib
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.domain_priors import DomainKnowledgePriors


class EnhancedPredictor:
    """
    增强预测器 - 基于DG-DAA架构
    
    在原有Gradient Boosting模型基础上，添加注意力机制
    """
    
    def __init__(self, model_path='saved_models/final_model_3to5.pkl', 
                 enable_attention=True, attention_strength=0.3):
        """
        初始化增强预测器
        
        Args:
            model_path: 原模型路径
            enable_attention: 是否启用注意力机制
            attention_strength: 注意力强度（0-1），控制先验影响程度
        """
        print(f"加载增强预测器...")
        print(f"  模型路径: {model_path}")
        print(f"  注意力机制: {'启用' if enable_attention else '禁用'}")
        print(f"  注意力强度: {attention_strength}")
        
        # 加载原模型
        model_info = joblib.load(model_path)
        self.base_model = model_info['model']
        self.feature_columns = model_info['feature_columns']
        self.model_name = model_info.get('model_name', 'Unknown')
        self.n_features = len(self.feature_columns)
        
        # 注意力配置
        self.enable_attention = enable_attention
        self.attention_strength = attention_strength
        
        # 初始化领域知识先验
        if self.enable_attention:
            self.domain_priors = DomainKnowledgePriors(self.feature_columns)
            self.prior_weights = self.domain_priors.get_priors()
        else:
            self.prior_weights = np.ones(self.n_features, dtype=np.float32)
        
        # 获取模型内置特征重要性（用于特征级注意力）
        if hasattr(self.base_model, 'feature_importances_'):
            self.feature_importances = self.base_model.feature_importances_
        else:
            self.feature_importances = np.ones(self.n_features) / self.n_features
        
        # 初始化特征贡献度分析器
        self.contribution_analyzer = None
        try:
            from models.feature_contribution_fast import FastFeatureContributionAnalyzer
            self.contribution_analyzer = FastFeatureContributionAnalyzer(
                self.base_model, 
                self.feature_columns,
                X_train=None
            )
            print(f"✓ 特征贡献度分析器已启用")
        except Exception as e:
            print(f"⚠️  特征贡献度分析器初始化失败: {e}")
        
        print(f"✓ 增强预测器加载完成")
        print(f"  基础模型: {self.model_name}")
        print(f"  特征数: {self.n_features}")
        print(f"  先验权重范围: [{self.prior_weights.min():.2f}, {self.prior_weights.max():.2f}]")
    
    def _compute_feature_attention(self, X):
        """
        计算特征级注意力权重
        
        融合：
        1. 领域知识先验
        2. 模型特征重要性
        
        Args:
            X: 输入特征 (n_samples, n_features)
        
        Returns:
            np.ndarray: 特征注意力权重 (n_features,)
        """
        # 归一化特征重要性
        importance_normalized = self.feature_importances / self.feature_importances.sum()
        
        # 融合先验和重要性
        # attention = prior^alpha * importance^(1-alpha)
        alpha = self.attention_strength
        feature_attention = (self.prior_weights ** alpha) * (importance_normalized ** (1 - alpha))
        
        # 归一化到合理范围 [0.5, 1.5]
        feature_attention = feature_attention / feature_attention.mean()
        feature_attention = np.clip(feature_attention, 0.5, 1.5)
        
        return feature_attention
    
    def _compute_sample_attention(self, X, base_prediction):
        """
        计算样本级注意力权重
        
        根据样本的风险阶段动态调整特征权重：
        - 低风险区（预测<2）：增强预防性指标（筛查、干预）
        - 中风险区（预测2-3）：平衡关注
        - 高风险区（预测>3）：增强控制性指标（治疗、抑制）
        
        Args:
            X: 输入特征 (n_samples, n_features)
            base_prediction: 基础预测值 (n_samples,)
        
        Returns:
            np.ndarray: 样本级注意力权重 (n_samples, n_features)
        """
        n_samples = X.shape[0]
        sample_attention = np.ones((n_samples, self.n_features), dtype=np.float32)
        
        # 定义不同阶段关注的特征
        prevention_features = ['筛查人数', '筛查覆盖率', '按人数筛查覆盖率',
                              '暗娼_月均干预人数', 'MSM_月均干预人数', '吸毒者_月均干预人数']
        control_features = ['治疗覆盖率', '病毒抑制比例', '30天治疗比例']
        
        for i in range(n_samples):
            pred = base_prediction[i]
            
            if pred < 2:  # 低风险区
                # 增强预防性指标
                for feature in prevention_features:
                    if feature in self.feature_columns:
                        idx = self.feature_columns.index(feature)
                        sample_attention[i, idx] *= 1.2
            
            elif pred > 3:  # 高风险区
                # 增强控制性指标
                for feature in control_features:
                    if feature in self.feature_columns:
                        idx = self.feature_columns.index(feature)
                        sample_attention[i, idx] *= 1.2
        
        return sample_attention
    
    def _apply_attention(self, X):
        """
        应用双层注意力机制
        
        Args:
            X: 输入特征 (n_samples, n_features)
        
        Returns:
            tuple: (加权后的特征, 特征注意力, 样本注意力)
        """
        if not self.enable_attention:
            return X, None, None
        
        # 1. 先用原始特征做一次预测（获取风险阶段）
        base_prediction = self.base_model.predict(X)
        
        # 2. 计算特征级注意力
        feature_attention = self._compute_feature_attention(X)
        
        # 3. 计算样本级注意力
        sample_attention = self._compute_sample_attention(X, base_prediction)
        
        # 4. 组合两层注意力
        # 广播feature_attention到每个样本
        combined_attention = sample_attention * feature_attention[np.newaxis, :]
        
        # 5. 应用注意力权重
        X_weighted = X * combined_attention
        
        return X_weighted, feature_attention, sample_attention
    
    def predict_single(self, features_dict, return_attention=False, include_contributions=False):
        """
        预测单个样本
        
        Args:
            features_dict: 特征字典
            return_attention: 是否返回注意力权重
            include_contributions: 是否包含特征贡献度（为了API兼容性，暂不实现）
        
        Returns:
            dict: 预测结果
        """
        # 构建特征向量
        X = np.zeros((1, self.n_features))
        for i, col in enumerate(self.feature_columns):
            X[0, i] = features_dict.get(col, 0)
        
        # 应用注意力
        X_weighted, feature_attention, sample_attention = self._apply_attention(X)
        
        # 预测
        prediction = self.base_model.predict(X_weighted)[0]
        
        # 构建结果
        result = {
            'risk_level_5': int(prediction),
            'risk_score': float(prediction) * 20,  # 转换为0-100分
            'confidence': 0.85,  # 默认置信度
            'confidence_percent': '85.00%',  # 默认置信度百分比
            'model_version': 'v1.1_enhanced' if self.enable_attention else 'v1.0_original',
            'attention_enabled': self.enable_attention
        }
        
        # 添加风险描述
        risk_descriptions = {
            1: '极低风险',
            2: '低风险',
            3: '中等风险',
            4: '高风险',
            5: '极高风险'
        }
        result['risk_description'] = risk_descriptions.get(result['risk_level_5'], '未知')
        
        # 如果需要，返回注意力权重
        if return_attention and self.enable_attention:
            # 构建完整的特征注意力权重列表（带特征名）
            all_feature_attention = [
                {
                    'feature': self.feature_columns[i],
                    'weight': float(feature_attention[i]) if feature_attention is not None else 0.0
                }
                for i in range(self.n_features)
            ] if feature_attention is not None else []
            
            result['attention_weights'] = {
                'top_10_features': self._get_top_attended_features(feature_attention, top_k=10),
                'all_features': all_feature_attention,  # 所有特征的权重（带名称）
                'feature_attention_array': feature_attention.tolist() if feature_attention is not None else None,  # 原始数组（向后兼容）
                'sample_attention': sample_attention[0].tolist() if sample_attention is not None else None
            }
        
        # 如果需要特征贡献度
        if include_contributions and self.contribution_analyzer:
            try:
                contrib_result = self.contribution_analyzer.explain_single(X, top_k=10)
                result['feature_contributions'] = self.contribution_analyzer.format_for_api(
                    contrib_result, 
                    top_k=5
                )
            except Exception as e:
                print(f"⚠️  特征贡献度计算失败: {e}")
                result['feature_contributions'] = None
        elif include_contributions:
            result['feature_contributions'] = None
        
        return result
    
    def _get_top_attended_features(self, feature_attention, top_k=10):
        """
        获取注意力权重最高的Top K特征
        
        Args:
            feature_attention: 特征注意力权重
            top_k: 返回Top K个
        
        Returns:
            list: Top K特征列表
        """
        if feature_attention is None:
            return []
        
        # 获取Top K索引
        top_indices = np.argsort(feature_attention)[-top_k:][::-1]
        
        top_features = []
        for idx in top_indices:
            top_features.append({
                'feature': self.feature_columns[idx],
                'weight': float(feature_attention[idx]),  # 改名为weight，更简洁
                'prior_weight': float(self.prior_weights[idx])
            })
        
        return top_features
    
    def predict_batch(self, X):
        """
        批量预测
        
        Args:
            X: 特征矩阵 (n_samples, n_features)
        
        Returns:
            np.ndarray: 预测结果 (n_samples,)
        """
        # 应用注意力
        X_weighted, _, _ = self._apply_attention(X)
        
        # 预测
        predictions = self.base_model.predict(X_weighted)
        
        return predictions
    
    def compare_with_original(self, features_dict):
        """
        对比原模型和增强模型的预测结果
        
        Args:
            features_dict: 特征字典
        
        Returns:
            dict: 对比结果
        """
        # 构建特征向量
        X = np.zeros((1, self.n_features))
        for i, col in enumerate(self.feature_columns):
            X[0, i] = features_dict.get(col, 0)
        
        # 原模型预测
        original_pred = self.base_model.predict(X)[0]
        
        # 增强模型预测
        if self.enable_attention:
            X_weighted, _, _ = self._apply_attention(X)
            enhanced_pred = self.base_model.predict(X_weighted)[0]
        else:
            enhanced_pred = original_pred
        
        return {
            'original_prediction': int(original_pred),
            'enhanced_prediction': int(enhanced_pred),
            'difference': int(enhanced_pred - original_pred),
            'attention_effect': 'increased' if enhanced_pred > original_pred else 
                              ('decreased' if enhanced_pred < original_pred else 'no_change')
        }


def main():
    """
    演示增强预测器的使用
    """
    print("="*80)
    print("  增强预测器演示 - DG-DAA")
    print("="*80)
    
    # 1. 加载增强预测器
    print("\n步骤1: 加载增强预测器...")
    predictor = EnhancedPredictor(
        model_path='saved_models/final_model_3to5.pkl',
        enable_attention=True,
        attention_strength=0.3
    )
    
    # 2. 准备测试样本
    print("\n步骤2: 准备测试样本...")
    sample_features = {col: 0 for col in predictor.feature_columns}
    sample_features.update({
        '存活数': 1200,
        '新报告': 80,
        '感染率': 0.12,
        '治疗覆盖率': 92.0,
        '病毒抑制比例': 88.0,
        '筛查人数': 120000,
        '注射吸毒者规模': 500,
        '城市MSM规模': 1500,
        '按人数筛查覆盖率': 25.0
    })
    
    # 3. 增强模型预测
    print("\n步骤3: 增强模型预测...")
    result = predictor.predict_single(sample_features, return_attention=True)
    
    print(f"\n预测结果:")
    print(f"  风险等级: {result['risk_level_5']} - {result['risk_description']}")
    print(f"  风险分数: {result['risk_score']:.1f}")
    print(f"  模型版本: {result['model_version']}")
    
    if 'attention_weights' in result:
        print(f"\n  Top 10 关注特征:")
        for i, item in enumerate(result['attention_weights']['top_attended_features'], 1):
            print(f"    {i}. {item['feature']:30s} 注意力={item['attention_weight']:.3f} 先验={item['prior_weight']:.2f}")
    
    # 4. 对比原模型和增强模型
    print("\n步骤4: 对比原模型 vs 增强模型...")
    comparison = predictor.compare_with_original(sample_features)
    
    print(f"\n对比结果:")
    print(f"  原模型预测: {comparison['original_prediction']}")
    print(f"  增强模型预测: {comparison['enhanced_prediction']}")
    print(f"  差异: {comparison['difference']:+d}")
    print(f"  注意力效果: {comparison['attention_effect']}")
    
    # 5. 测试不同注意力强度
    print("\n步骤5: 测试不同注意力强度...")
    for strength in [0.0, 0.3, 0.5, 0.7, 1.0]:
        predictor_test = EnhancedPredictor(
            model_path='saved_models/final_model_3to5.pkl',
            enable_attention=True,
            attention_strength=strength
        )
        result_test = predictor_test.predict_single(sample_features)
        print(f"  强度={strength:.1f}: 预测={result_test['risk_level_5']}, 分数={result_test['risk_score']:.1f}")
    
    print("\n" + "="*80)
    print("✓ 演示完成")
    print("="*80)


if __name__ == '__main__':
    main()
