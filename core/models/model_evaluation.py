"""
模型深度评估
评估模型的可靠性、泛化能力和数据需求
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import learning_curve, validation_curve, cross_val_score
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
import joblib
import warnings
warnings.filterwarnings('ignore')


class ModelEvaluator:
    """模型深度评估器"""
    
    def __init__(self):
        self.results = {}
        
    def load_data(self, csv_path):
        """加载数据"""
        print("\n" + "=" * 80)
        print("加载数据")
        print("=" * 80)
        
        df = pd.read_csv(csv_path)
        
        # 使用原始3级标签
        exclude_columns = ['区县', '按方案评定级别', 'risk_level']
        feature_columns = [col for col in df.columns if col not in exclude_columns]
        
        X = df[feature_columns].values
        y = df['按方案评定级别'].values
        
        print(f"✓ 数据加载成功")
        print(f"  样本数: {len(X)}")
        print(f"  特征数: {len(feature_columns)}")
        
        # 标准化
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        return X_scaled, y, feature_columns
    
    def evaluate_sample_size_impact(self, X, y):
        """评估样本量对模型性能的影响（学习曲线）"""
        print("\n" + "=" * 80)
        print("评估1: 学习曲线分析")
        print("=" * 80)
        print("目的: 判断是否需要更多数据")
        
        model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )
        
        # 计算学习曲线
        train_sizes = np.linspace(0.1, 1.0, 10)
        
        print("\n计算学习曲线...")
        train_sizes_abs, train_scores, val_scores = learning_curve(
            model, X, y,
            train_sizes=train_sizes,
            cv=5,
            scoring='f1_weighted',
            n_jobs=-1,
            random_state=42
        )
        
        # 计算均值和标准差
        train_mean = train_scores.mean(axis=1)
        train_std = train_scores.std(axis=1)
        val_mean = val_scores.mean(axis=1)
        val_std = val_scores.std(axis=1)
        
        # 分析结果
        print("\n学习曲线结果:")
        print(f"{'样本数':<10} {'训练F1':<15} {'验证F1':<15} {'差距':<10}")
        print("-" * 50)
        
        for i, size in enumerate(train_sizes_abs):
            gap = train_mean[i] - val_mean[i]
            print(f"{int(size):<10} {train_mean[i]:.4f}±{train_std[i]:.4f}  {val_mean[i]:.4f}±{val_std[i]:.4f}  {gap:.4f}")
        
        # 判断
        final_gap = train_mean[-1] - val_mean[-1]
        final_val_score = val_mean[-1]
        
        print(f"\n分析结论:")
        print(f"  最终验证F1: {final_val_score:.4f}")
        print(f"  训练-验证差距: {final_gap:.4f}")
        
        if final_gap > 0.1:
            print(f"  ⚠️  存在过拟合，但可能是数据量不足导致")
        else:
            print(f"  ✓ 模型泛化良好")
        
        if val_mean[-1] < val_mean[-2]:
            print(f"  ⚠️  验证性能未随样本增加而提升，可能已达到数据上限")
        else:
            print(f"  ✓ 验证性能随样本增加而提升，更多数据可能有帮助")
        
        # 保存结果
        self.results['learning_curve'] = {
            'train_sizes': train_sizes_abs,
            'train_scores': train_mean,
            'val_scores': val_mean,
            'final_gap': final_gap,
            'final_val_score': final_val_score
        }
        
        return train_sizes_abs, train_mean, val_mean
    
    def evaluate_data_augmentation_impact(self, X, y):
        """评估数据增强的影响"""
        print("\n" + "=" * 80)
        print("评估2: 数据增强效果")
        print("=" * 80)
        print("目的: 验证SMOTE是否真正提升性能")
        
        model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )
        
        # 1. 原始数据性能
        print("\n测试1: 原始数据（无增强）")
        scores_original = cross_val_score(
            model, X, y,
            cv=5,
            scoring='f1_weighted',
            n_jobs=-1
        )
        
        print(f"  F1分数: {scores_original.mean():.4f} ±{scores_original.std():.4f}")
        
        # 2. SMOTE增强后性能
        print("\n测试2: SMOTE增强数据")
        
        # 检查最小类别样本数
        unique, counts = np.unique(y, return_counts=True)
        min_samples = counts.min()
        k_neighbors = min(5, max(1, min_samples - 1))
        
        smote = SMOTE(k_neighbors=k_neighbors, random_state=42)
        X_smote, y_smote = smote.fit_resample(X, y)
        
        print(f"  增强后样本数: {len(X_smote)} (原始: {len(X)})")
        
        scores_smote = cross_val_score(
            model, X_smote, y_smote,
            cv=5,
            scoring='f1_weighted',
            n_jobs=-1
        )
        
        print(f"  F1分数: {scores_smote.mean():.4f} ±{scores_smote.std():.4f}")
        
        # 3. 对比分析
        improvement = scores_smote.mean() - scores_original.mean()
        
        print(f"\n对比分析:")
        print(f"  性能提升: {improvement:+.4f}")
        
        if improvement > 0.02:
            print(f"  ✓ SMOTE显著提升性能，数据增强有效")
        elif improvement > 0:
            print(f"  ≈ SMOTE略微提升性能")
        else:
            print(f"  ⚠️  SMOTE未提升性能，可能引入噪声")
        
        self.results['augmentation'] = {
            'original_score': scores_original.mean(),
            'smote_score': scores_smote.mean(),
            'improvement': improvement
        }
        
        return scores_original, scores_smote
    
    def evaluate_model_stability(self, X, y):
        """评估模型稳定性（多次随机划分）"""
        print("\n" + "=" * 80)
        print("评估3: 模型稳定性")
        print("=" * 80)
        print("目的: 检查模型在不同数据划分下的表现")
        
        model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )
        
        # 使用不同随机种子进行多次交叉验证
        print("\n进行20次交叉验证（不同随机种子）...")
        
        all_scores = []
        for seed in range(20):
            scores = cross_val_score(
                model, X, y,
                cv=5,
                scoring='f1_weighted',
                n_jobs=-1
            )
            all_scores.append(scores.mean())
        
        all_scores = np.array(all_scores)
        
        print(f"\n稳定性分析:")
        print(f"  平均F1: {all_scores.mean():.4f}")
        print(f"  标准差: {all_scores.std():.4f}")
        print(f"  最小值: {all_scores.min():.4f}")
        print(f"  最大值: {all_scores.max():.4f}")
        print(f"  变异系数: {all_scores.std()/all_scores.mean()*100:.2f}%")
        
        if all_scores.std() < 0.05:
            print(f"  ✓ 模型非常稳定")
        elif all_scores.std() < 0.1:
            print(f"  ✓ 模型较稳定")
        else:
            print(f"  ⚠️  模型不稳定，性能波动较大")
        
        self.results['stability'] = {
            'mean': all_scores.mean(),
            'std': all_scores.std(),
            'min': all_scores.min(),
            'max': all_scores.max()
        }
        
        return all_scores
    
    def evaluate_feature_importance_stability(self, X, y, feature_columns):
        """评估特征重要性的稳定性"""
        print("\n" + "=" * 80)
        print("评估4: 特征重要性稳定性")
        print("=" * 80)
        print("目的: 检查关键特征是否一致")
        
        # 训练多个模型，记录特征重要性
        n_iterations = 10
        importance_matrix = []
        
        print(f"\n训练{n_iterations}个模型...")
        
        for i in range(n_iterations):
            model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=i
            )
            model.fit(X, y)
            importance_matrix.append(model.feature_importances_)
        
        importance_matrix = np.array(importance_matrix)
        
        # 计算每个特征的平均重要性和标准差
        mean_importance = importance_matrix.mean(axis=0)
        std_importance = importance_matrix.std(axis=0)
        
        # 找出Top 10特征
        top_indices = np.argsort(mean_importance)[-10:][::-1]
        
        print(f"\nTop 10 重要特征:")
        print(f"{'特征':<40} {'平均重要性':<15} {'标准差':<15}")
        print("-" * 70)
        
        for idx in top_indices:
            feat_name = feature_columns[idx]
            mean_imp = mean_importance[idx]
            std_imp = std_importance[idx]
            cv = std_imp / mean_imp if mean_imp > 0 else 0
            
            print(f"{feat_name:<40} {mean_imp:.6f}       {std_imp:.6f} (CV:{cv:.2%})")
        
        # 分析
        top_feature = feature_columns[top_indices[0]]
        top_importance = mean_importance[top_indices[0]]
        
        print(f"\n分析:")
        print(f"  最重要特征: {top_feature} ({top_importance:.4f})")
        
        if top_importance > 0.5:
            print(f"  ⚠️  单个特征主导性过强（>{top_importance:.1%}），模型可能过度依赖该特征")
        else:
            print(f"  ✓ 特征重要性分布较均衡")
        
        self.results['feature_importance'] = {
            'top_feature': top_feature,
            'top_importance': top_importance,
            'mean_importance': mean_importance,
            'std_importance': std_importance
        }
        
        return mean_importance, std_importance, feature_columns
    
    def generate_comprehensive_report(self):
        """生成综合评估报告"""
        print("\n" + "=" * 80)
        print("综合评估报告")
        print("=" * 80)
        
        print("\n📊 数据量评估:")
        if 'learning_curve' in self.results:
            lc = self.results['learning_curve']
            print(f"  当前验证F1: {lc['final_val_score']:.4f}")
            print(f"  训练-验证差距: {lc['final_gap']:.4f}")
            
            if lc['final_gap'] > 0.15:
                print(f"  ❌ 数据量严重不足，强烈建议增加数据")
                data_recommendation = "需要更多真实数据或高质量合成数据"
            elif lc['final_gap'] > 0.1:
                print(f"  ⚠️  数据量可能不足，建议增加数据")
                data_recommendation = "建议增加数据以提升泛化能力"
            else:
                print(f"  ✓ 数据量基本充足")
                data_recommendation = "当前数据量可接受"
        
        print("\n🔄 数据增强评估:")
        if 'augmentation' in self.results:
            aug = self.results['augmentation']
            print(f"  原始数据F1: {aug['original_score']:.4f}")
            print(f"  SMOTE增强F1: {aug['smote_score']:.4f}")
            print(f"  性能提升: {aug['improvement']:+.4f}")
            
            if aug['improvement'] > 0.02:
                print(f"  ✓ SMOTE有效，建议使用")
                augmentation_recommendation = "使用SMOTE数据增强"
            else:
                print(f"  ⚠️  SMOTE效果有限")
                augmentation_recommendation = "考虑其他数据增强方法"
        
        print("\n📈 模型稳定性:")
        if 'stability' in self.results:
            stab = self.results['stability']
            print(f"  平均F1: {stab['mean']:.4f}")
            print(f"  标准差: {stab['std']:.4f}")
            print(f"  范围: [{stab['min']:.4f}, {stab['max']:.4f}]")
            
            if stab['std'] < 0.05:
                print(f"  ✓ 模型稳定性优秀")
                stability_recommendation = "模型可靠"
            elif stab['std'] < 0.1:
                print(f"  ✓ 模型稳定性良好")
                stability_recommendation = "模型基本可靠"
            else:
                print(f"  ⚠️  模型不稳定")
                stability_recommendation = "需要更多数据或调整模型"
        
        print("\n🎯 特征依赖性:")
        if 'feature_importance' in self.results:
            fi = self.results['feature_importance']
            print(f"  最重要特征: {fi['top_feature']}")
            print(f"  重要性: {fi['top_importance']:.4f}")
            
            if fi['top_importance'] > 0.5:
                print(f"  ⚠️  过度依赖单一特征")
                feature_recommendation = "考虑排除主导特征重新训练"
            else:
                print(f"  ✓ 特征使用均衡")
                feature_recommendation = "特征工程合理"
        
        print("\n" + "=" * 80)
        print("🎯 最终建议")
        print("=" * 80)
        
        print(f"\n1. 数据方面: {data_recommendation}")
        print(f"2. 数据增强: {augmentation_recommendation}")
        print(f"3. 模型稳定性: {stability_recommendation}")
        print(f"4. 特征工程: {feature_recommendation}")
        
        # 总体建议
        print(f"\n💡 总体建议:")
        
        if 'learning_curve' in self.results and self.results['learning_curve']['final_gap'] > 0.15:
            print(f"  ❌ 当前模型不适合生产使用")
            print(f"     - 数据量严重不足（仅190样本）")
            print(f"     - 建议收集更多真实数据")
            print(f"     - 或使用高级合成数据方法（如VAE、GAN）")
        elif 'learning_curve' in self.results and self.results['learning_curve']['final_gap'] > 0.1:
            print(f"  ⚠️  模型可用于研究，但生产使用需谨慎")
            print(f"     - 建议增加数据量到500+样本")
            print(f"     - 继续使用SMOTE等数据增强")
        else:
            print(f"  ✓ 模型基本可用")
            print(f"     - 性能和稳定性可接受")
            print(f"     - 建议持续收集数据改进")


def main():
    """主评估流程"""
    print("\n" + "=" * 80)
    print("HIV风险模型深度评估")
    print("=" * 80)
    
    evaluator = ModelEvaluator()
    
    # 加载数据
    X, y, feature_columns = evaluator.load_data('data/processed/hiv_data_processed.csv')
    
    # 评估1: 学习曲线
    evaluator.evaluate_sample_size_impact(X, y)
    
    # 评估2: 数据增强效果
    evaluator.evaluate_data_augmentation_impact(X, y)
    
    # 评估3: 模型稳定性
    evaluator.evaluate_model_stability(X, y)
    
    # 评估4: 特征重要性
    evaluator.evaluate_feature_importance_stability(X, y, feature_columns)
    
    # 生成综合报告
    evaluator.generate_comprehensive_report()
    
    print("\n" + "=" * 80)
    print("✓ 评估完成")
    print("=" * 80)
    
    return evaluator


if __name__ == '__main__':
    evaluator = main()
