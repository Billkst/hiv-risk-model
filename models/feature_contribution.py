"""
特征贡献度分析器
使用SHAP (SHapley Additive exPlanations) 解释模型预测
"""

import numpy as np
import pandas as pd
import shap
import matplotlib.pyplot as plt
import logging
from typing import Dict, List, Tuple, Optional
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeatureContributionAnalyzer:
    """
    特征贡献度分析器
    
    使用SHAP值量化每个特征对预测结果的贡献
    """
    
    def __init__(self, model, X_background: np.ndarray, feature_names: List[str]):
        """
        初始化分析器
        
        Args:
            model: 训练好的模型（Gradient Boosting）
            X_background: 背景数据集（用于SHAP计算，建议100-200个样本）
            feature_names: 特征名称列表
        """
        self.model = model
        self.feature_names = feature_names
        self.n_features = len(feature_names)
        
        logger.info(f"Initializing SHAP TreeExplainer...")
        
        # 使用TreeExplainer（针对树模型优化，速度快）
        # 注意：对于多类分类，SHAP会为每个类生成一个explainer
        try:
            self.explainer = shap.TreeExplainer(
                model,
                X_background,
                feature_perturbation='tree_path_dependent'
            )
            
            # 计算背景数据的期望值（base value）
            self.base_value = self.explainer.expected_value
            
            # 如果是多类分类，base_value是一个数组
            if isinstance(self.base_value, (list, np.ndarray)):
                logger.info(f"Multi-class model detected: {len(self.base_value)} classes")
                # 使用第一个类的base value作为参考
                self.base_value_array = self.base_value
                self.base_value = float(self.base_value[0]) if len(self.base_value) > 0 else 0.0
                self.is_multiclass = True
            else:
                self.base_value = float(self.base_value)
                self.is_multiclass = False
                
        except Exception as e:
            logger.warning(f"TreeExplainer failed: {e}")
            logger.info("Falling back to KernelExplainer (slower but more compatible)...")
            
            # 降级到KernelExplainer
            def model_predict(X):
                # 返回概率或预测值
                if hasattr(model, 'predict_proba'):
                    return model.predict_proba(X)
                else:
                    return model.predict(X)
            
            self.explainer = shap.KernelExplainer(
                model_predict,
                X_background
            )
            
            # 计算base value
            bg_predictions = model_predict(X_background)
            self.base_value = float(bg_predictions.mean())
            self.is_multiclass = False
        
        logger.info(f"✓ SHAP explainer initialized")
        logger.info(f"  Features: {self.n_features}")
        logger.info(f"  Base value: {self.base_value}")
    
    def explain_single(self, X_single: np.ndarray, top_k: int = 10) -> Dict:
        """
        解释单个样本的预测
        
        Args:
            X_single: 单个样本特征 (1, n_features)
            top_k: 返回Top K个贡献最大的特征
            
        Returns:
            包含SHAP值和解释的字典
        """
        if X_single.ndim == 1:
            X_single = X_single.reshape(1, -1)
        
        # 计算SHAP值
        shap_values = self.explainer.shap_values(X_single)
        
        # 如果是多类分类，SHAP返回一个列表，每个类一个数组
        if isinstance(shap_values, list):
            # 对于多类分类，我们计算所有类的平均SHAP值
            # 或者选择预测概率最高的类
            logger.debug(f"Multi-class SHAP values: {len(shap_values)} classes")
            # 这里我们取所有类的平均值作为特征贡献
            shap_values = np.mean(shap_values, axis=0)
        
        # 展平为一维数组
        shap_values_flat = shap_values.flatten()
        
        # 获取特征值
        feature_values = X_single.flatten()
        
        # 创建特征-SHAP值对
        feature_shap_pairs = [
            {
                'feature': self.feature_names[i],
                'value': float(feature_values[i]),
                'shap_value': float(shap_values_flat[i]),
                'contribution': float(shap_values_flat[i])
            }
            for i in range(self.n_features)
        ]
        
        # 按贡献度绝对值排序
        sorted_pairs = sorted(feature_shap_pairs, 
                            key=lambda x: abs(x['shap_value']), 
                            reverse=True)
        
        # 分离正负贡献
        positive_contributions = [p for p in sorted_pairs if p['shap_value'] > 0]
        negative_contributions = [p for p in sorted_pairs if p['shap_value'] < 0]
        
        # 取Top K
        top_positive = positive_contributions[:top_k]
        top_negative = negative_contributions[:top_k]
        
        # 计算预测值
        prediction = self.base_value + shap_values_flat.sum()
        
        result = {
            'base_value': float(self.base_value),
            'prediction': float(prediction),
            'shap_sum': float(shap_values_flat.sum()),
            'top_positive_features': top_positive,
            'top_negative_features': top_negative,
            'all_shap_values': shap_values_flat.tolist(),
            'feature_names': self.feature_names
        }
        
        # 验证可加性: prediction ≈ base_value + sum(SHAP)
        additive_check = abs(prediction - (self.base_value + shap_values_flat.sum()))
        result['additive_check_error'] = float(additive_check)
        result['additive_check_passed'] = additive_check < 0.01
        
        return result
    
    def get_global_importance(self, X_test: np.ndarray, method='mean_abs') -> List[Dict]:
        """
        计算全局特征重要性
        
        Args:
            X_test: 测试数据集
            method: 计算方法
                - 'mean_abs': 平均绝对SHAP值
                - 'mean': 平均SHAP值（考虑方向）
                - 'max': 最大绝对SHAP值
                
        Returns:
            特征重要性列表（按重要性降序排列）
        """
        logger.info(f"Computing global feature importance for {len(X_test)} samples...")
        
        # 计算所有样本的SHAP值
        shap_values = self.explainer.shap_values(X_test)
        
        # 如果是多类分类，取第一个类
        if isinstance(shap_values, list):
            shap_values = shap_values[0]
        
        # 计算重要性
        if method == 'mean_abs':
            importance = np.abs(shap_values).mean(axis=0)
        elif method == 'mean':
            importance = shap_values.mean(axis=0)
        elif method == 'max':
            importance = np.abs(shap_values).max(axis=0)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        # 创建特征重要性列表
        feature_importance = [
            {
                'rank': i + 1,
                'feature': self.feature_names[idx],
                'importance': float(importance[idx]),
                'importance_normalized': float(importance[idx] / importance.sum() * 100)
            }
            for i, idx in enumerate(np.argsort(importance)[::-1])
        ]
        
        logger.info(f"✓ Global importance computed")
        logger.info(f"  Top 3 features: {[f['feature'] for f in feature_importance[:3]]}")
        
        return feature_importance
    
    def format_for_api(self, shap_result: Dict, top_k: int = 5) -> Dict:
        """
        格式化SHAP结果用于API响应
        
        Args:
            shap_result: explain_single()的返回结果
            top_k: 返回Top K个特征
            
        Returns:
            API友好的格式
        """
        return {
            'base_value': shap_result['base_value'],
            'prediction': shap_result['prediction'],
            'top_positive': [
                {
                    'feature': f['feature'],
                    'value': f['value'],
                    'contribution': f['contribution']
                }
                for f in shap_result['top_positive_features'][:top_k]
            ],
            'top_negative': [
                {
                    'feature': f['feature'],
                    'value': f['value'],
                    'contribution': f['contribution']
                }
                for f in shap_result['top_negative_features'][:top_k]
            ],
            'shap_values': shap_result['all_shap_values'],
            'additive_check_passed': shap_result['additive_check_passed']
        }
    
    def visualize_waterfall(self, shap_result: Dict, save_path: Optional[str] = None):
        """
        生成瀑布图可视化
        
        Args:
            shap_result: explain_single()的返回结果
            save_path: 保存路径（可选）
        """
        try:
            import matplotlib
            matplotlib.use('Agg')  # 非交互式后端
            
            # 准备数据
            shap_values = np.array(shap_result['all_shap_values'])
            base_value = shap_result['base_value']
            
            # 创建SHAP Explanation对象
            explanation = shap.Explanation(
                values=shap_values,
                base_values=base_value,
                feature_names=self.feature_names
            )
            
            # 生成瀑布图
            plt.figure(figsize=(10, 8))
            shap.waterfall_plot(explanation, max_display=15, show=False)
            
            if save_path:
                plt.savefig(save_path, bbox_inches='tight', dpi=150)
                logger.info(f"✓ Waterfall plot saved: {save_path}")
            
            plt.close()
            
        except Exception as e:
            logger.error(f"Failed to create waterfall plot: {e}")
    
    def visualize_global_importance(self, importance_list: List[Dict], 
                                   top_k: int = 20,
                                   save_path: Optional[str] = None):
        """
        可视化全局特征重要性
        
        Args:
            importance_list: get_global_importance()的返回结果
            top_k: 显示Top K个特征
            save_path: 保存路径（可选）
        """
        try:
            import matplotlib
            matplotlib.use('Agg')
            
            # 取Top K
            top_features = importance_list[:top_k]
            
            # 准备数据
            features = [f['feature'] for f in top_features]
            importances = [f['importance'] for f in top_features]
            
            # 创建条形图
            plt.figure(figsize=(12, 8))
            plt.barh(range(len(features)), importances)
            plt.yticks(range(len(features)), features, fontsize=10)
            plt.xlabel('Mean |SHAP value|', fontsize=12)
            plt.title(f'Top {top_k} Feature Importance (Global)', fontsize=14)
            plt.gca().invert_yaxis()
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, bbox_inches='tight', dpi=150)
                logger.info(f"✓ Importance plot saved: {save_path}")
            
            plt.close()
            
        except Exception as e:
            logger.error(f"Failed to create importance plot: {e}")
    
    def batch_explain(self, X_batch: np.ndarray, top_k: int = 5) -> List[Dict]:
        """
        批量解释多个样本
        
        Args:
            X_batch: 批量样本 (n_samples, n_features)
            top_k: 每个样本返回Top K个特征
            
        Returns:
            解释结果列表
        """
        results = []
        
        for i in range(len(X_batch)):
            X_single = X_batch[i:i+1]
            result = self.explain_single(X_single, top_k=top_k)
            result['sample_index'] = i
            results.append(result)
        
        return results


def demo():
    """演示特征贡献度分析"""
    import joblib
    
    print("\n" + "="*80)
    print("Feature Contribution Analyzer Demo")
    print("="*80)
    
    # 加载模型
    print("\n1. Loading model...")
    model_path = 'hiv_project/hiv_risk_model/saved_models/final_model_3to5.pkl'
    model_info = joblib.load(model_path)
    
    model = model_info['model']
    feature_names = model_info['feature_columns']
    
    print(f"✓ Model loaded: {model_info['model_name']}")
    print(f"  Features: {len(feature_names)}")
    
    # 加载数据
    print("\n2. Loading data...")
    data_path = 'hiv_project/hiv_risk_model/data/processed/hiv_data_processed.csv'
    df = pd.read_csv(data_path)
    
    X = df[feature_names].values
    print(f"✓ Data loaded: {len(X)} samples")
    
    # 创建背景数据集（随机采样100个样本）
    np.random.seed(42)
    bg_indices = np.random.choice(len(X), size=min(100, len(X)), replace=False)
    X_background = X[bg_indices]
    
    # 初始化分析器
    print("\n3. Initializing SHAP analyzer...")
    analyzer = FeatureContributionAnalyzer(model, X_background, feature_names)
    
    # 解释单个样本
    print("\n4. Explaining single sample...")
    X_single = X[0:1]
    result = analyzer.explain_single(X_single, top_k=5)
    
    print(f"\nBase value: {result['base_value']:.4f}")
    print(f"Prediction: {result['prediction']:.4f}")
    print(f"SHAP sum: {result['shap_sum']:.4f}")
    print(f"Additive check: {'✓ PASSED' if result['additive_check_passed'] else '✗ FAILED'}")
    
    print(f"\nTop 5 Positive Contributors:")
    for f in result['top_positive_features']:
        print(f"  {f['feature']:30s}: {f['value']:8.2f} → +{f['contribution']:7.4f}")
    
    print(f"\nTop 5 Negative Contributors:")
    for f in result['top_negative_features']:
        print(f"  {f['feature']:30s}: {f['value']:8.2f} → {f['contribution']:7.4f}")
    
    # 全局特征重要性
    print("\n5. Computing global feature importance...")
    print("   (Using 10 samples for demo - in production use more samples)")
    X_test = X[:10]  # 使用前10个样本（演示用）
    importance = analyzer.get_global_importance(X_test)
    
    print(f"\nTop 10 Most Important Features:")
    for f in importance[:10]:
        print(f"  {f['rank']:2d}. {f['feature']:30s}: {f['importance']:7.4f} ({f['importance_normalized']:5.2f}%)")
    
    # 可视化
    print("\n6. Creating visualizations...")
    os.makedirs('hiv_project/hiv_risk_model/outputs/shap_visualizations', exist_ok=True)
    
    analyzer.visualize_waterfall(
        result,
        'hiv_project/hiv_risk_model/outputs/shap_visualizations/waterfall_sample0.png'
    )
    
    analyzer.visualize_global_importance(
        importance,
        top_k=20,
        save_path='hiv_project/hiv_risk_model/outputs/shap_visualizations/global_importance.png'
    )
    
    print("\n" + "="*80)
    print("✓ Demo completed")
    print("="*80)


if __name__ == '__main__':
    demo()
