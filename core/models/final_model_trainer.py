"""
最终模型训练脚本
使用原始3级标签 + 数据增强 + 5级映射输出
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_validate, KFold
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE
import joblib
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.evaluator import ModelEvaluator


class FinalHIVRiskModel:
    """最终 HIV 风险评估模型"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = None
        self.model_name = None
        
    def load_and_prepare_data(self, csv_path):
        """加载并准备数据"""
        print("\n" + "=" * 80)
        print("数据加载与准备")
        print("=" * 80)
        
        # 加载数据
        df = pd.read_csv(csv_path)
        print(f"✓ 数据加载成功: {df.shape}")
        
        # 使用原始的"按方案评定级别"作为目标
        exclude_columns = ['区县', '按方案评定级别', 'risk_level']
        self.feature_columns = [col for col in df.columns if col not in exclude_columns]
        
        X = df[self.feature_columns].values
        y = df['按方案评定级别'].values
        
        # 保存感染率列索引（用于后续5级映射）
        if '感染率' in self.feature_columns:
            self.infection_rate_idx = self.feature_columns.index('感染率')
        else:
            self.infection_rate_idx = None
        
        print(f"\n数据信息:")
        print(f"  特征数: {len(self.feature_columns)}")
        print(f"  样本数: {len(X)}")
        
        print(f"\n目标变量分布 (原始3级):")
        unique, counts = np.unique(y, return_counts=True)
        for cls, count in zip(unique, counts):
            print(f"  等级 {int(cls)}: {count} 样本 ({count/len(y)*100:.1f}%)")
        
        return X, y, df
    
    def augment_data(self, X, y, method='smote'):
        """数据增强"""
        print("\n" + "=" * 80)
        print("数据增强")
        print("=" * 80)
        
        print(f"使用方法: {method.upper()}")
        
        # 检查最小类别样本数
        unique, counts = np.unique(y, return_counts=True)
        min_samples = counts.min()
        k_neighbors = min(5, max(1, min_samples - 1))
        
        print(f"SMOTE 参数: k_neighbors={k_neighbors}")
        
        try:
            smote = SMOTE(
                sampling_strategy='auto',
                k_neighbors=k_neighbors,
                random_state=42
            )
            
            X_resampled, y_resampled = smote.fit_resample(X, y)
            
            print(f"\n增强后数据分布:")
            unique, counts = np.unique(y_resampled, return_counts=True)
            for cls, count in zip(unique, counts):
                print(f"  等级 {int(cls)}: {count} 样本")
            
            print(f"\n✓ 数据增强完成")
            print(f"  原始: {len(X)} 样本")
            print(f"  增强后: {len(X_resampled)} 样本")
            print(f"  增加: {len(X_resampled) - len(X)} 样本 (+{(len(X_resampled)-len(X))/len(X)*100:.1f}%)")
            
            return X_resampled, y_resampled
            
        except Exception as e:
            print(f"⚠️  数据增强失败: {e}")
            print(f"  使用原始数据")
            return X, y
    
    def train_with_cross_validation(self, X, y):
        """使用交叉验证训练模型"""
        print("\n" + "=" * 80)
        print("模型训练（交叉验证）")
        print("=" * 80)
        
        # 定义候选模型
        models = {
            'Gradient Boosting': GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            ),
            'Random Forest': RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                class_weight='balanced',
                random_state=42,
                n_jobs=-1
            ),
            'Logistic Regression': LogisticRegression(
                max_iter=1000,
                class_weight='balanced',
                random_state=42
            )
        }
        
        # 交叉验证评估
        best_score = 0
        best_model_name = None
        results = {}
        
        for name, model in models.items():
            print(f"\n{'='*60}")
            print(f"评估模型: {name}")
            print(f"{'='*60}")
            
            cv = KFold(n_splits=5, shuffle=True, random_state=42)
            
            cv_results = cross_validate(
                model, X, y,
                cv=cv,
                scoring=['accuracy', 'f1_weighted'],
                return_train_score=True,
                n_jobs=-1
            )
            
            test_f1 = cv_results['test_f1_weighted'].mean()
            test_f1_std = cv_results['test_f1_weighted'].std()
            
            results[name] = {
                'f1_mean': test_f1,
                'f1_std': test_f1_std,
                'model': model
            }
            
            print(f"F1分数: {test_f1:.4f} ±{test_f1_std:.4f}")
            
            if test_f1 > best_score:
                best_score = test_f1
                best_model_name = name
        
        # 选择最佳模型
        print(f"\n{'='*60}")
        print(f"🏆 最佳模型: {best_model_name}")
        print(f"   F1分数: {results[best_model_name]['f1_mean']:.4f} ±{results[best_model_name]['f1_std']:.4f}")
        print(f"{'='*60}")
        
        self.model_name = best_model_name
        self.model = results[best_model_name]['model']
        
        # 在全部数据上训练最佳模型
        print(f"\n在全部增强数据上训练最佳模型...")
        self.model.fit(X, y)
        print(f"✓ 训练完成")
        
        return results
    
    def map_3_to_5_levels(self, y_pred_3level, y_proba, X_original=None):
        """
        将3级预测映射到5级输出
        
        策略：结合预测概率和感染率
        - 等级1 (低风险) → 根据置信度细分为 1级(极低) 或 2级(低)
        - 等级2 (中风险) → 3级(中)
        - 等级3 (高风险) → 根据置信度和感染率细分为 4级(高) 或 5级(极高)
        """
        n_samples = len(y_pred_3level)
        y_pred_5level = np.zeros(n_samples, dtype=int)
        confidence = np.zeros(n_samples)
        
        for i in range(n_samples):
            pred_class = int(y_pred_3level[i])
            prob = y_proba[i]
            max_prob = prob[pred_class - 1]  # 预测类别的概率
            
            # 获取感染率（如果可用）
            infection_rate = None
            if X_original is not None and self.infection_rate_idx is not None:
                infection_rate = X_original[i, self.infection_rate_idx]
            
            # 映射逻辑
            if pred_class == 1:  # 低风险
                if max_prob > 0.8:
                    y_pred_5level[i] = 1  # 极低风险
                else:
                    y_pred_5level[i] = 2  # 低风险
                confidence[i] = max_prob
                
            elif pred_class == 2:  # 中风险
                y_pred_5level[i] = 3  # 中风险
                confidence[i] = max_prob
                
            elif pred_class == 3:  # 高风险
                # 结合感染率和置信度
                if infection_rate is not None:
                    if infection_rate >= 1.0 or max_prob > 0.9:
                        y_pred_5level[i] = 5  # 极高风险
                    else:
                        y_pred_5level[i] = 4  # 高风险
                else:
                    if max_prob > 0.8:
                        y_pred_5level[i] = 5  # 极高风险
                    else:
                        y_pred_5level[i] = 4  # 高风险
                confidence[i] = max_prob
        
        return y_pred_5level, confidence
    
    def predict_with_5_levels(self, X):
        """预测并输出5级结果"""
        # 标准化
        X_scaled = self.scaler.transform(X)
        
        # 3级预测
        y_pred_3 = self.model.predict(X_scaled)
        y_proba = self.model.predict_proba(X_scaled)
        
        # 映射到5级
        y_pred_5, confidence = self.map_3_to_5_levels(y_pred_3, y_proba, X)
        
        return y_pred_5, confidence, y_pred_3, y_proba
    
    def save_model(self, save_dir='saved_models'):
        """保存模型"""
        os.makedirs(save_dir, exist_ok=True)
        
        model_info = {
            'model': self.model,
            'scaler': self.scaler,
            'model_name': self.model_name,
            'feature_columns': self.feature_columns,
            'infection_rate_idx': self.infection_rate_idx
        }
        
        model_path = os.path.join(save_dir, 'final_model_3to5.pkl')
        joblib.dump(model_info, model_path)
        
        print(f"\n✓ 模型已保存: {model_path}")
        return model_path


def main():
    """主训练流程"""
    print("\n" + "=" * 80)
    print("最终 HIV 风险评估模型训练")
    print("使用原始3级标签 + 数据增强 + 5级映射输出")
    print("=" * 80)
    
    # 初始化模型
    model = FinalHIVRiskModel()
    
    # 步骤1: 加载数据
    print("\n【步骤 1/6】加载数据")
    X, y, df = model.load_and_prepare_data('data/processed/hiv_data_processed.csv')
    
    # 步骤2: 特征标准化
    print("\n【步骤 2/6】特征标准化")
    X_scaled = model.scaler.fit_transform(X)
    print("✓ 标准化完成")
    
    # 步骤3: 数据增强
    print("\n【步骤 3/6】数据增强")
    X_augmented, y_augmented = model.augment_data(X_scaled, y)
    
    # 步骤4: 训练模型
    print("\n【步骤 4/6】模型训练")
    results = model.train_with_cross_validation(X_augmented, y_augmented)
    
    # 步骤5: 测试5级映射
    print("\n【步骤 5/6】测试5级映射")
    print("=" * 80)
    
    # 在原始数据上测试
    y_pred_5, confidence, y_pred_3, y_proba = model.predict_with_5_levels(X)
    
    print(f"\n5级预测结果分布:")
    unique, counts = np.unique(y_pred_5, return_counts=True)
    for cls, count in zip(unique, counts):
        print(f"  等级 {cls}: {count} 样本 ({count/len(y_pred_5)*100:.1f}%)")
    
    print(f"\n平均置信度: {confidence.mean():.4f}")
    
    # 显示示例
    print(f"\n预测示例 (前10个样本):")
    print(f"{'3级预测':<10} {'5级预测':<10} {'置信度':<10} {'概率分布'}")
    print("-" * 60)
    for i in range(min(10, len(y_pred_3))):
        probs = ', '.join([f'{p:.3f}' for p in y_proba[i]])
        print(f"{int(y_pred_3[i]):<10} {y_pred_5[i]:<10} {confidence[i]:.4f}    [{probs}]")
    
    # 步骤6: 保存模型
    print("\n【步骤 6/6】保存模型")
    model_path = model.save_model()
    
    print("\n" + "=" * 80)
    print("✓ 训练流程完成！")
    print("=" * 80)
    
    print(f"\n模型信息:")
    print(f"  模型类型: {model.model_name}")
    print(f"  训练样本数: {len(X_augmented)}")
    print(f"  特征数: {len(model.feature_columns)}")
    print(f"  输入: 3级标签")
    print(f"  输出: 5级风险评估 + 置信度")
    
    print(f"\n生成的文件:")
    print(f"  - {model_path}")
    
    return model, results


if __name__ == '__main__':
    model, results = main()
