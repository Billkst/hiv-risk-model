"""
快速特征贡献度分析器
使用模型内置的feature_importances_和近似SHAP方法
适用于生产环境的快速响应
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FastFeatureContributionAnalyzer:
    """
    快速特征贡献度分析器
    
    使用模型内置的特征重要性和近似方法
    响应速度快，适合生产环境
    """
    
    def __init__(self, model, feature_names: List[str], X_train: Optional[np.ndarray] = None):
        """
        初始化分析器
        
        Args:
            model: 训练好的模型（需要有feature_importances_属性）
            feature_names: 特征名称列表
            X_train: 训练数据（用于计算base value）
        """
        self.model = model
        self.feature_names = feature_names
        self.n_features = len(feature_names)
        
        # 获取模型内置的特征重要性
        if hasattr(model, 'feature_importances_'):
            self.feature_importances = model.feature_importances_
            logger.info(f"✓ Using model's built-in feature importances")
        else:
            logger.warning("Model doesn't have feature_importances_, using uniform weights")
            self.feature_importances = np.ones(self.n_features) / self.n_features
        
        # 计算base value（训练集的平均预测）
        if X_train is not None and hasattr(model, 'predict'):
            predictions = model.predict(X_train)
            self.base_value = float(predictions.mean())
        else:
            self.base_value = 0.0
        
        logger.info(f"✓ Fast analyzer initialized")
        logger.info(f"  Features: {self.n_features}")
        logger.info(f"  Base value: {self.base_value:.4f}")
    
    def explain_single(self, X_single: np.ndarray, top_k: int = 10) -> Dict:
        """
        快速解释单个样本
        
        使用近似方法：特征值 × 特征重要性
        
        Args:
            X_single: 单个样本特征 (1, n_features)
            top_k: 返回Top K个贡献最大的特征
            
        Returns:
            包含贡献度的字典
        """
        if X_single.ndim == 1:
            X_single = X_single.reshape(1, -1)
        
        feature_values = X_single.flatten()
        
        # 近似SHAP值：特征值 × 特征重要性
        # 这是一个简化的方法，不如真实SHAP准确，但速度快
        approximate_shap = feature_values * self.feature_importances
        
        # 归一化，使总和接近预测值与base value的差
        if hasattr(self.model, 'predict'):
            prediction = float(self.model.predict(X_single)[0])
        else:
            prediction = self.base_value
        
        prediction_diff = prediction - self.base_value
        shap_sum = approximate_shap.sum()
        
        if abs(shap_sum) > 1e-6:
            # 缩放SHAP值使其总和等于预测差异
            approximate_shap = approximate_shap * (prediction_diff / shap_sum)
        
        # 创建特征-贡献对
        feature_contributions = [
            {
                'feature': self.feature_names[i],
                'value': float(feature_values[i]),
                'contribution': float(approximate_shap[i]),
                'importance': float(self.feature_importances[i])
            }
            for i in range(self.n_features)
        ]
        
        # 按贡献度绝对值排序
        sorted_contributions = sorted(feature_contributions,
                                     key=lambda x: abs(x['contribution']),
                                     reverse=True)
        
        # 分离正负贡献
        positive_contributions = [c for c in sorted_contributions if c['contribution'] > 0]
        negative_contributions = [c for c in sorted_contributions if c['contribution'] < 0]
        
        # 取Top K
        top_positive = positive_contributions[:top_k]
        top_negative = negative_contributions[:top_k]
        
        result = {
            'base_value': self.base_value,
            'prediction': prediction,
            'contribution_sum': float(approximate_shap.sum()),
            'top_positive_features': top_positive,
            'top_negative_features': top_negative,
            'all_contributions': approximate_shap.tolist(),
            'feature_names': self.feature_names,
            'method': 'fast_approximate'
        }
        
        return result
    
    def get_global_importance(self) -> List[Dict]:
        """
        获取全局特征重要性
        
        直接使用模型的feature_importances_
        
        Returns:
            特征重要性列表（按重要性降序排列）
        """
        # 按重要性排序
        sorted_indices = np.argsort(self.feature_importances)[::-1]
        
        feature_importance = [
            {
                'rank': i + 1,
                'feature': self.feature_names[idx],
                'importance': float(self.feature_importances[idx]),
                'importance_normalized': float(self.feature_importances[idx] / self.feature_importances.sum() * 100)
            }
            for i, idx in enumerate(sorted_indices)
        ]
        
        return feature_importance
    
    def format_for_api(self, result: Dict, top_k: int = 5) -> Dict:
        """
        格式化结果用于API响应
        
        Args:
            result: explain_single()的返回结果
            top_k: 返回Top K个特征
            
        Returns:
            API友好的格式
        """
        return {
            'base_value': result['base_value'],
            'prediction': result['prediction'],
            'method': result['method'],
            'top_positive': [
                {
                    'feature': f['feature'],
                    'value': f['value'],
                    'contribution': f['contribution']
                }
                for f in result['top_positive_features'][:top_k]
            ],
            'top_negative': [
                {
                    'feature': f['feature'],
                    'value': f['value'],
                    'contribution': f['contribution']
                }
                for f in result['top_negative_features'][:top_k]
            ],
            'all_contributions': result['all_contributions'],
            'feature_names': self.feature_names  # 添加特征名称列表
        }


def demo():
    """演示快速特征贡献度分析"""
    import joblib
    
    print("\n" + "="*80)
    print("Fast Feature Contribution Analyzer Demo")
    print("="*80)
    
    # 加载模型
    print("\n1. Loading model...")
    # 支持从不同目录运行
    import os
    if os.path.exists('saved_models/final_model_3to5.pkl'):
        model_path = 'saved_models/final_model_3to5.pkl'
    else:
        model_path = 'hiv_project/hiv_risk_model/saved_models/final_model_3to5.pkl'
    model_info = joblib.load(model_path)
    
    model = model_info['model']
    feature_names = model_info['feature_columns']
    
    print(f"✓ Model loaded: {model_info['model_name']}")
    print(f"  Features: {len(feature_names)}")
    
    # 加载数据
    print("\n2. Loading data...")
    if os.path.exists('data/processed/hiv_data_processed.csv'):
        data_path = 'data/processed/hiv_data_processed.csv'
    else:
        data_path = 'hiv_project/hiv_risk_model/data/processed/hiv_data_processed.csv'
    df = pd.read_csv(data_path)
    
    X = df[feature_names].values
    print(f"✓ Data loaded: {len(X)} samples")
    
    # 初始化快速分析器
    print("\n3. Initializing fast analyzer...")
    analyzer = FastFeatureContributionAnalyzer(model, feature_names, X)
    
    # 解释单个样本
    print("\n4. Explaining single sample...")
    import time
    start_time = time.time()
    
    X_single = X[0:1]
    result = analyzer.explain_single(X_single, top_k=5)
    
    elapsed_ms = (time.time() - start_time) * 1000
    
    print(f"\n⚡ Analysis completed in {elapsed_ms:.2f} ms")
    print(f"\nBase value: {result['base_value']:.4f}")
    print(f"Prediction: {result['prediction']:.4f}")
    print(f"Contribution sum: {result['contribution_sum']:.4f}")
    print(f"Method: {result['method']}")
    
    print(f"\nTop 5 Positive Contributors:")
    for f in result['top_positive_features']:
        print(f"  {f['feature']:30s}: {f['value']:8.2f} → +{f['contribution']:7.4f}")
    
    print(f"\nTop 5 Negative Contributors:")
    for f in result['top_negative_features']:
        print(f"  {f['feature']:30s}: {f['value']:8.2f} → {f['contribution']:7.4f}")
    
    # 全局特征重要性
    print("\n5. Getting global feature importance...")
    importance = analyzer.get_global_importance()
    
    print(f"\nTop 10 Most Important Features:")
    for f in importance[:10]:
        print(f"  {f['rank']:2d}. {f['feature']:30s}: {f['importance']:7.4f} ({f['importance_normalized']:5.2f}%)")
    
    # API格式
    print("\n6. API format example...")
    api_result = analyzer.format_for_api(result, top_k=3)
    print(f"\nAPI Response (Top 3):")
    print(f"  Base: {api_result['base_value']:.4f}")
    print(f"  Prediction: {api_result['prediction']:.4f}")
    print(f"  Top positive: {len(api_result['top_positive'])} features")
    print(f"  Top negative: {len(api_result['top_negative'])} features")
    
    print("\n" + "="*80)
    print("✓ Demo completed")
    print(f"✓ Fast method is suitable for production (< 1ms per sample)")
    print(f"✓ Run from: {os.getcwd()}")
    print("="*80)


if __name__ == '__main__':
    demo()
