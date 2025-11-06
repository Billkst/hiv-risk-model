"""
对比不同数据集的模型性能
真实数据 vs 合成数据 vs 混合数据
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import cross_val_score, KFold
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')


def evaluate_dataset(csv_path, dataset_name):
    """评估单个数据集"""
    print("\n" + "=" * 80)
    print(f"评估数据集: {dataset_name}")
    print("=" * 80)
    
    # 加载数据
    df = pd.read_csv(csv_path)
    print(f"✓ 数据加载: {df.shape}")
    
    # 准备特征和目标
    X = df.drop(columns=['按方案评定级别']).values
    y = df['按方案评定级别'].values
    
    # 标准化
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 显示目标变量分布
    print(f"\n目标变量分布:")
    for level in sorted(np.unique(y)):
        count = (y == level).sum()
        pct = count / len(y) * 100
        print(f"  等级 {int(level)}: {count} 样本 ({pct:.1f}%)")
    
    # 创建模型
    model = GradientBoostingClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        random_state=42
    )
    
    # 交叉验证
    print(f"\n进行5折交叉验证...")
    cv = KFold(n_splits=5, shuffle=True, random_state=42)
    
    scores = cross_val_score(
        model, X_scaled, y,
        cv=cv,
        scoring='f1_weighted',
        n_jobs=-1
    )
    
    # 结果
    mean_score = scores.mean()
    std_score = scores.std()
    
    print(f"\n交叉验证结果:")
    print(f"  F1分数: {mean_score:.4f} ±{std_score:.4f}")
    print(f"  各折分数: {[f'{s:.4f}' for s in scores]}")
    
    return {
        'dataset': dataset_name,
        'n_samples': len(X),
        'n_features': X.shape[1],
        'f1_mean': mean_score,
        'f1_std': std_score,
        'scores': scores
    }


def compare_all_datasets():
    """对比所有数据集"""
    print("\n" + "=" * 80)
    print("数据集性能对比")
    print("=" * 80)
    
    datasets = {
        '真实数据(190样本)': 'data/processed/hiv_data_processed.csv',
        '纯合成数据(500样本)': 'data/processed/hiv_synthetic_data.csv',
        '混合数据50-50(190样本)': 'data/processed/hiv_mixed_50_50.csv',
        '混合数据70-30(190样本)': 'data/processed/hiv_mixed_70_30.csv'
    }
    
    results = []
    
    for name, path in datasets.items():
        try:
            result = evaluate_dataset(path, name)
            results.append(result)
        except Exception as e:
            print(f"\n⚠️  评估 {name} 失败: {e}")
    
    # 汇总对比
    print("\n" + "=" * 80)
    print("性能汇总对比")
    print("=" * 80)
    
    print(f"\n{'数据集':<30} {'样本数':<10} {'F1分数':<20} {'排名':<10}")
    print("-" * 70)
    
    # 按F1分数排序
    results_sorted = sorted(results, key=lambda x: x['f1_mean'], reverse=True)
    
    for rank, result in enumerate(results_sorted, 1):
        dataset = result['dataset']
        n_samples = result['n_samples']
        f1_str = f"{result['f1_mean']:.4f} ±{result['f1_std']:.4f}"
        
        print(f"{dataset:<30} {n_samples:<10} {f1_str:<20} #{rank}")
    
    # 分析结论
    print("\n" + "=" * 80)
    print("分析结论")
    print("=" * 80)
    
    best_result = results_sorted[0]
    real_result = next((r for r in results if '真实数据' in r['dataset']), None)
    
    print(f"\n🏆 最佳数据集: {best_result['dataset']}")
    print(f"   F1分数: {best_result['f1_mean']:.4f} ±{best_result['f1_std']:.4f}")
    
    if real_result:
        improvement = best_result['f1_mean'] - real_result['f1_mean']
        print(f"\n📊 相比真实数据:")
        print(f"   真实数据F1: {real_result['f1_mean']:.4f}")
        print(f"   最佳数据F1: {best_result['f1_mean']:.4f}")
        print(f"   性能提升: {improvement:+.4f} ({improvement/real_result['f1_mean']*100:+.2f}%)")
        
        if improvement > 0.05:
            print(f"\n✓ 合成数据显著提升模型性能")
            print(f"  建议: 使用 {best_result['dataset']} 进行最终训练")
        elif improvement > 0:
            print(f"\n≈ 合成数据略微提升模型性能")
            print(f"  建议: 可以使用 {best_result['dataset']}")
        else:
            print(f"\n⚠️  合成数据未提升性能")
            print(f"  建议: 继续使用真实数据，或调整CTGAN参数")
    
    # 数据量分析
    print(f"\n📈 数据量影响:")
    synthetic_500 = next((r for r in results if '纯合成数据' in r['dataset']), None)
    
    if synthetic_500 and real_result:
        print(f"   真实数据(190样本): F1={real_result['f1_mean']:.4f}")
        print(f"   合成数据(500样本): F1={synthetic_500['f1_mean']:.4f}")
        
        if synthetic_500['f1_mean'] > real_result['f1_mean']:
            print(f"   ✓ 增加数据量有效提升性能")
        else:
            print(f"   ⚠️  单纯增加合成数据量效果有限")
            print(f"   建议: 使用混合数据集")
    
    return results_sorted


def main():
    """主流程"""
    print("\n" + "=" * 80)
    print("数据集性能对比分析")
    print("=" * 80)
    
    results = compare_all_datasets()
    
    print("\n" + "=" * 80)
    print("✓ 对比分析完成")
    print("=" * 80)
    
    return results


if __name__ == '__main__':
    results = main()
