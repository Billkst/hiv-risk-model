"""
模型训练主脚本
训练多个基线模型并比较性能
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
import joblib
import os
import sys

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.feature_engineer import FeatureEngineer
from models.evaluator import ModelEvaluator


class HIVRiskModelTrainer:
    """HIV 风险模型训练器"""
    
    def __init__(self):
        self.models = {}
        self.results = {}
        self.best_model = None
        self.best_model_name = None
        
    def initialize_models(self):
        """初始化多个基线模型"""
        print("\n" + "=" * 80)
        print("初始化模型")
        print("=" * 80)
        
        # 计算类别权重（处理不平衡问题）
        self.models = {
            'Logistic Regression': LogisticRegression(
                max_iter=1000,
                class_weight='balanced',  # 自动平衡类别权重
                random_state=42
            ),
            
            'Random Forest': RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                class_weight='balanced',
                random_state=42,
                n_jobs=-1
            ),
            
            'Gradient Boosting': GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            ),
            
            'SVM': SVC(
                kernel='rbf',
                class_weight='balanced',
                probability=True,  # 启用概率预测
                random_state=42
            )
        }
        
        print(f"✓ 初始化了 {len(self.models)} 个模型:")
        for i, name in enumerate(self.models.keys(), 1):
            print(f"  {i}. {name}")
    
    def train_model(self, model_name, model, X_train, y_train, X_val, y_val):
        """训练单个模型"""
        print("\n" + "=" * 80)
        print(f"训练模型: {model_name}")
        print("=" * 80)
        
        # 训练
        print(f"开始训练...")
        model.fit(X_train, y_train)
        print(f"✓ 训练完成")
        
        # 在验证集上评估
        print(f"\n在验证集上评估:")
        y_val_pred = model.predict(X_val)
        
        # 获取概率预测（如果支持）
        try:
            y_val_pred_proba = model.predict_proba(X_val)
        except:
            y_val_pred_proba = None
        
        # 评估
        evaluator = ModelEvaluator(model_name)
        metrics = evaluator.evaluate(y_val, y_val_pred, y_val_pred_proba)
        evaluator.evaluate_per_class(y_val, y_val_pred)
        
        return model, metrics
    
    def train_all_models(self, X_train, y_train, X_val, y_val):
        """训练所有模型"""
        print("\n" + "=" * 80)
        print("开始训练所有模型")
        print("=" * 80)
        
        for model_name, model in self.models.items():
            trained_model, metrics = self.train_model(
                model_name, model, X_train, y_train, X_val, y_val
            )
            
            # 保存结果
            self.results[model_name] = {
                'model': trained_model,
                'metrics': metrics
            }
        
        print("\n" + "=" * 80)
        print("✓ 所有模型训练完成")
        print("=" * 80)
    
    def compare_models(self):
        """比较所有模型的性能"""
        print("\n" + "=" * 80)
        print("模型性能对比")
        print("=" * 80)
        
        # 准备对比数据
        metrics_dict = {name: result['metrics'] for name, result in self.results.items()}
        
        evaluator = ModelEvaluator()
        comparison_df = evaluator.compare_models(metrics_dict)
        
        # 选择最佳模型（基于 F1 分数）
        best_name = max(metrics_dict.items(), key=lambda x: x[1]['f1_score'])[0]
        self.best_model_name = best_name
        self.best_model = self.results[best_name]['model']
        
        print(f"\n🏆 选择最佳模型: {best_name}")
        
        return comparison_df
    
    def evaluate_on_test(self, X_test, y_test):
        """在测试集上评估最佳模型"""
        print("\n" + "=" * 80)
        print(f"在测试集上评估最佳模型: {self.best_model_name}")
        print("=" * 80)
        
        # 预测
        y_test_pred = self.best_model.predict(X_test)
        
        try:
            y_test_pred_proba = self.best_model.predict_proba(X_test)
        except:
            y_test_pred_proba = None
        
        # 评估
        evaluator = ModelEvaluator(self.best_model_name)
        test_metrics = evaluator.evaluate(y_test, y_test_pred, y_test_pred_proba)
        evaluator.evaluate_per_class(y_test, y_test_pred)
        
        return test_metrics
    
    def save_best_model(self, save_path='saved_models/best_model.pkl'):
        """保存最佳模型"""
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        model_info = {
            'model': self.best_model,
            'model_name': self.best_model_name,
            'metrics': self.results[self.best_model_name]['metrics']
        }
        
        joblib.dump(model_info, save_path)
        print(f"\n✓ 最佳模型已保存: {save_path}")
        print(f"  模型: {self.best_model_name}")
        print(f"  F1分数: {model_info['metrics']['f1_score']:.4f}")
    
    def get_feature_importance(self, feature_columns):
        """获取特征重要性（如果模型支持）"""
        print("\n" + "=" * 80)
        print(f"特征重要性分析: {self.best_model_name}")
        print("=" * 80)
        
        try:
            if hasattr(self.best_model, 'feature_importances_'):
                # 树模型
                importances = self.best_model.feature_importances_
            elif hasattr(self.best_model, 'coef_'):
                # 线性模型
                importances = np.abs(self.best_model.coef_).mean(axis=0)
            else:
                print("⚠️  该模型不支持特征重要性分析")
                return None
            
            # 创建特征重要性 DataFrame
            feature_importance_df = pd.DataFrame({
                '特征': feature_columns,
                '重要性': importances
            }).sort_values('重要性', ascending=False)
            
            # 显示 Top 20
            print("\nTop 20 重要特征:")
            print("-" * 60)
            for idx, row in feature_importance_df.head(20).iterrows():
                print(f"{row['特征']:<40} {row['重要性']:.6f}")
            
            return feature_importance_df
            
        except Exception as e:
            print(f"⚠️  特征重要性分析失败: {e}")
            return None


def main():
    """主训练流程"""
    print("\n" + "=" * 80)
    print("HIV 风险评估模型训练")
    print("=" * 80)
    
    # 1. 特征工程
    print("\n步骤 1: 特征工程")
    engineer = FeatureEngineer()
    data = engineer.process_pipeline('data/processed/hiv_data_processed.csv')
    
    # 2. 初始化训练器
    print("\n步骤 2: 初始化训练器")
    trainer = HIVRiskModelTrainer()
    trainer.initialize_models()
    
    # 3. 训练所有模型
    print("\n步骤 3: 训练模型")
    trainer.train_all_models(
        data['X_train'], data['y_train'],
        data['X_val'], data['y_val']
    )
    
    # 4. 比较模型
    print("\n步骤 4: 比较模型性能")
    comparison_df = trainer.compare_models()
    
    # 5. 在测试集上评估
    print("\n步骤 5: 测试集评估")
    test_metrics = trainer.evaluate_on_test(data['X_test'], data['y_test'])
    
    # 6. 特征重要性
    print("\n步骤 6: 特征重要性分析")
    feature_importance = trainer.get_feature_importance(data['feature_columns'])
    
    # 7. 保存模型
    print("\n步骤 7: 保存最佳模型")
    trainer.save_best_model()
    
    print("\n" + "=" * 80)
    print("✓ 训练流程完成！")
    print("=" * 80)
    
    print("\n生成的文件:")
    print("  - saved_models/scaler.pkl (特征标准化器)")
    print("  - saved_models/best_model.pkl (最佳模型)")
    
    return trainer, data, feature_importance


if __name__ == '__main__':
    trainer, data, feature_importance = main()
