"""
交叉验证模块
使用K折交叉验证评估模型的真实性能
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import cross_validate, StratifiedKFold, KFold
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')


class CrossValidator:
    """交叉验证器"""
    
    def __init__(self, n_splits=5):
        self.n_splits = n_splits
        self.results = {}
        
    def get_models(self):
        """获取模型字典"""
        models = {
            'Logistic Regression': LogisticRegression(
                max_iter=1000,
                class_weight='balanced',
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
                random_state=42
            )
        }
        return models
    
    def run_cross_validation(self, X, y, model_name, model):
        """对单个模型运行交叉验证"""
        print(f"\n{'='*60}")
        print(f"交叉验证: {model_name}")
        print(f"{'='*60}")
        
        # 检查是否可以使用分层K折
        min_class_count = pd.Series(y).value_counts().min()
        
        if min_class_count >= self.n_splits:
            cv = StratifiedKFold(n_splits=self.n_splits, shuffle=True, random_state=42)
            print(f"使用分层 {self.n_splits} 折交叉验证")
        else:
            cv = KFold(n_splits=self.n_splits, shuffle=True, random_state=42)
            print(f"⚠️  最小类别样本数 {min_class_count} < {self.n_splits}，使用普通K折")
        
        # 定义评分指标
        scoring = {
            'accuracy': 'accuracy',
            'precision_weighted': 'precision_weighted',
            'recall_weighted': 'recall_weighted',
            'f1_weighted': 'f1_weighted'
        }
        
        # 执行交叉验证
        print(f"开始训练...")
        cv_results = cross_validate(
            model, X, y,
            cv=cv,
            scoring=scoring,
            return_train_score=True,
            n_jobs=-1
        )
        
        # 计算统计信息
        results = {}
        for metric in ['accuracy', 'precision_weighted', 'recall_weighted', 'f1_weighted']:
            test_scores = cv_results[f'test_{metric}']
            train_scores = cv_results[f'train_{metric}']
            
            results[metric] = {
                'test_mean': test_scores.mean(),
                'test_std': test_scores.std(),
                'train_mean': train_scores.mean(),
                'train_std': train_scores.std(),
                'test_scores': test_scores
            }
        
        # 打印结果
        print(f"\n交叉验证结果 ({self.n_splits}折):")
        print(f"{'指标':<20} {'训练集均值':<15} {'测试集均值':<15} {'测试集标准差':<15}")
        print("-" * 65)
        
        metric_names = {
            'accuracy': '准确率',
            'precision_weighted': '精确率',
            'recall_weighted': '召回率',
            'f1_weighted': 'F1分数'
        }
        
        for metric, name in metric_names.items():
            train_mean = results[metric]['train_mean']
            test_mean = results[metric]['test_mean']
            test_std = results[metric]['test_std']
            print(f"{name:<20} {train_mean:.4f}         {test_mean:.4f}         ±{test_std:.4f}")
        
        # 检查过拟合
        train_test_gap = results['f1_weighted']['train_mean'] - results['f1_weighted']['test_mean']
        if train_test_gap > 0.1:
            print(f"\n⚠️  可能存在过拟合 (训练-测试差距: {train_test_gap:.4f})")
        else:
            print(f"\n✓ 模型泛化良好 (训练-测试差距: {train_test_gap:.4f})")
        
        return results
    
    def compare_all_models(self, X, y):
        """比较所有模型的交叉验证结果"""
        print("\n" + "=" * 80)
        print("所有模型交叉验证对比")
        print("=" * 80)
        
        models = self.get_models()
        all_results = {}
        
        for model_name, model in models.items():
            results = self.run_cross_validation(X, y, model_name, model)
            all_results[model_name] = results
        
        # 汇总对比
        print("\n" + "=" * 80)
        print("模型性能汇总对比")
        print("=" * 80)
        
        comparison_data = []
        for model_name, results in all_results.items():
            comparison_data.append({
                '模型': model_name,
                '准确率': f"{results['accuracy']['test_mean']:.4f}±{results['accuracy']['test_std']:.4f}",
                '精确率': f"{results['precision_weighted']['test_mean']:.4f}±{results['precision_weighted']['test_std']:.4f}",
                '召回率': f"{results['recall_weighted']['test_mean']:.4f}±{results['recall_weighted']['test_std']:.4f}",
                'F1分数': f"{results['f1_weighted']['test_mean']:.4f}±{results['f1_weighted']['test_std']:.4f}"
            })
        
        df_comparison = pd.DataFrame(comparison_data)
        print(df_comparison.to_string(index=False))
        
        # 找出最佳模型
        best_model = max(all_results.items(), 
                        key=lambda x: x[1]['f1_weighted']['test_mean'])
        print(f"\n🏆 最佳模型: {best_model[0]}")
        print(f"   F1分数: {best_model[1]['f1_weighted']['test_mean']:.4f} ±{best_model[1]['f1_weighted']['test_std']:.4f}")
        
        self.results = all_results
        return all_results


def test_without_infection_rate(X, y, feature_columns):
    """测试不使用感染率特征的模型性能"""
    print("\n" + "=" * 80)
    print("实验：排除感染率特征后的模型性能")
    print("=" * 80)
    
    # 找到感染率列的索引
    if '感染率' in feature_columns:
        infection_rate_idx = feature_columns.index('感染率')
        print(f"\n排除特征: 感染率 (第 {infection_rate_idx} 列)")
        
        # 创建不包含感染率的特征矩阵
        X_no_infection = np.delete(X, infection_rate_idx, axis=1)
        remaining_features = [f for f in feature_columns if f != '感染率']
        
        print(f"剩余特征数: {len(remaining_features)}")
        
        # 使用最佳模型（Gradient Boosting）进行交叉验证
        print(f"\n使用 Gradient Boosting 模型:")
        
        model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )
        
        validator = CrossValidator(n_splits=5)
        results = validator.run_cross_validation(X_no_infection, y, 
                                                "Gradient Boosting (无感染率)", model)
        
        return results, remaining_features
    else:
        print("⚠️  未找到感染率特征")
        return None, None


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("模型交叉验证与性能分析")
    print("=" * 80)
    
    # 加载数据
    print("\n步骤 1: 加载数据")
    df = pd.read_csv('data/processed/hiv_data_processed.csv')
    print(f"✓ 数据加载成功: {df.shape}")
    
    # 准备特征和目标
    exclude_columns = ['区县', '按方案评定级别', 'risk_level']
    feature_columns = [col for col in df.columns if col not in exclude_columns]
    
    X = df[feature_columns].values
    y = df['risk_level'].values
    
    print(f"✓ 特征数: {len(feature_columns)}")
    print(f"✓ 样本数: {len(X)}")
    
    # 特征标准化
    print("\n步骤 2: 特征标准化")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    print("✓ 标准化完成")
    
    # 交叉验证所有模型
    print("\n步骤 3: 交叉验证所有模型")
    validator = CrossValidator(n_splits=5)
    all_results = validator.compare_all_models(X_scaled, y)
    
    # 测试不使用感染率的性能
    print("\n步骤 4: 测试排除感染率后的性能")
    results_no_infection, remaining_features = test_without_infection_rate(
        X_scaled, y, feature_columns
    )
    
    print("\n" + "=" * 80)
    print("✓ 交叉验证分析完成")
    print("=" * 80)
    
    return validator, all_results, results_no_infection


if __name__ == '__main__':
    validator, all_results, results_no_infection = main()
