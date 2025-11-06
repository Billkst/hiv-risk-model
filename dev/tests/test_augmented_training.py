"""
测试不同数量的合成数据增强效果
策略: 190真实数据 + N条合成数据
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sdv.single_table import CTGANSynthesizer
from sdv.metadata import SingleTableMetadata
import warnings
warnings.filterwarnings('ignore')


def generate_more_synthetic_data(real_df, n_synthetic, model_path=None):
    """生成更多合成数据"""
    print(f"\n生成 {n_synthetic} 条合成数据...")
    
    if model_path:
        # 加载已训练的模型
        try:
            synthesizer = CTGANSynthesizer.load(model_path)
            print(f"✓ 加载已有CTGAN模型")
        except:
            print(f"⚠️  无法加载模型，重新训练...")
            model_path = None
    
    if not model_path:
        # 重新训练
        print(f"训练CTGAN模型...")
        metadata = SingleTableMetadata()
        metadata.detect_from_dataframe(real_df)
        
        synthesizer = CTGANSynthesizer(
            metadata=metadata,
            epochs=300,
            batch_size=100,
            verbose=False
        )
        synthesizer.fit(real_df)
        print(f"✓ 训练完成")
    
    # 生成数据
    synthetic_df = synthesizer.sample(num_rows=n_synthetic)
    print(f"✓ 生成完成: {synthetic_df.shape}")
    
    return synthetic_df


def create_augmented_dataset(real_df, n_synthetic):
    """创建增强数据集：全部真实数据 + N条合成数据"""
    print(f"\n" + "=" * 80)
    print(f"创建增强数据集: 190真实 + {n_synthetic}合成")
    print("=" * 80)
    
    # 生成合成数据
    synthetic_df = generate_more_synthetic_data(
        real_df, 
        n_synthetic,
        model_path='saved_models/ctgan_model.pkl'
    )
    
    # 合并：全部真实数据 + 合成数据
    augmented_df = pd.concat([real_df, synthetic_df], ignore_index=True)
    
    # 打乱顺序
    augmented_df = augmented_df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    print(f"\n增强数据集:")
    print(f"  真实数据: {len(real_df)} 样本 (100%真实数据)")
    print(f"  合成数据: {n_synthetic} 样本")
    print(f"  总计: {len(augmented_df)} 样本")
    
    # 显示目标变量分布
    if '按方案评定级别' in augmented_df.columns:
        print(f"\n目标变量分布:")
        for level in sorted(augmented_df['按方案评定级别'].unique()):
            count = (augmented_df['按方案评定级别'] == level).sum()
            pct = count / len(augmented_df) * 100
            print(f"  等级 {int(level)}: {count} 样本 ({pct:.1f}%)")
    
    return augmented_df


def evaluate_augmented_dataset(augmented_df, dataset_name):
    """评估增强数据集"""
    print(f"\n评估: {dataset_name}")
    
    # 准备数据
    X = augmented_df.drop(columns=['按方案评定级别']).values
    y = augmented_df['按方案评定级别'].values
    
    # 标准化
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 模型
    model = GradientBoostingClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        random_state=42
    )
    
    # 交叉验证
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    scores = cross_val_score(
        model, X_scaled, y,
        cv=cv,
        scoring='f1_weighted',
        n_jobs=-1
    )
    
    mean_score = scores.mean()
    std_score = scores.std()
    
    print(f"  F1分数: {mean_score:.4f} ±{std_score:.4f}")
    
    return {
        'dataset': dataset_name,
        'n_samples': len(X),
        'f1_mean': mean_score,
        'f1_std': std_score
    }


def test_different_augmentation_levels():
    """测试不同数量的合成数据增强"""
    print("\n" + "=" * 80)
    print("测试不同数量的合成数据增强")
    print("=" * 80)
    
    # 加载真实数据
    print("\n加载真实数据...")
    df = pd.read_csv('data/processed/hiv_data_processed.csv')
    
    # 准备训练数据
    exclude_columns = ['区县', 'risk_level']
    real_df = df.drop(columns=exclude_columns)
    
    print(f"✓ 真实数据: {real_df.shape}")
    
    # 测试不同的增强级别
    augmentation_levels = [
        0,      # 基线：仅真实数据
        200,    # 190 + 200 = 390
        500,    # 190 + 500 = 690
        1000,   # 190 + 1000 = 1190
        2000,   # 190 + 2000 = 2190
    ]
    
    results = []
    
    for n_synthetic in augmentation_levels:
        if n_synthetic == 0:
            # 基线：仅真实数据
            dataset_name = f"仅真实数据({len(real_df)}样本)"
            result = evaluate_augmented_dataset(real_df, dataset_name)
        else:
            # 增强数据
            augmented_df = create_augmented_dataset(real_df, n_synthetic)
            dataset_name = f"真实+合成({len(real_df)}+{n_synthetic}={len(augmented_df)}样本)"
            result = evaluate_augmented_dataset(augmented_df, dataset_name)
        
        results.append(result)
    
    # 汇总对比
    print("\n" + "=" * 80)
    print("性能汇总对比")
    print("=" * 80)
    
    print(f"\n{'数据集配置':<50} {'总样本数':<12} {'F1分数':<20}")
    print("-" * 82)
    
    baseline_f1 = results[0]['f1_mean']
    
    for result in results:
        dataset = result['dataset']
        n_samples = result['n_samples']
        f1_str = f"{result['f1_mean']:.4f} ±{result['f1_std']:.4f}"
        
        # 计算相对基线的提升
        improvement = result['f1_mean'] - baseline_f1
        if improvement != 0:
            improvement_str = f"({improvement:+.4f})"
        else:
            improvement_str = "(基线)"
        
        print(f"{dataset:<50} {n_samples:<12} {f1_str:<20} {improvement_str}")
    
    # 找出最佳配置
    best_result = max(results, key=lambda x: x['f1_mean'])
    
    print("\n" + "=" * 80)
    print("分析结论")
    print("=" * 80)
    
    print(f"\n🏆 最佳配置: {best_result['dataset']}")
    print(f"   F1分数: {best_result['f1_mean']:.4f} ±{best_result['f1_std']:.4f}")
    
    improvement = best_result['f1_mean'] - baseline_f1
    improvement_pct = improvement / baseline_f1 * 100
    
    print(f"\n📊 相比基线(仅真实数据):")
    print(f"   基线F1: {baseline_f1:.4f}")
    print(f"   最佳F1: {best_result['f1_mean']:.4f}")
    print(f"   提升: {improvement:+.4f} ({improvement_pct:+.2f}%)")
    
    if improvement > 0.05:
        print(f"\n✓ 合成数据显著提升性能！")
        print(f"  建议: 使用 {best_result['dataset']} 配置")
    elif improvement > 0.02:
        print(f"\n✓ 合成数据有效提升性能")
        print(f"  建议: 使用 {best_result['dataset']} 配置")
    elif improvement > 0:
        print(f"\n≈ 合成数据略微提升性能")
        print(f"  建议: 可以使用 {best_result['dataset']} 配置")
    else:
        print(f"\n⚠️  合成数据未提升性能")
        print(f"  建议: 继续使用真实数据")
    
    # 保存最佳配置的数据
    if improvement > 0:
        print(f"\n保存最佳配置数据...")
        
        # 找出最佳的合成数据数量
        best_n_synthetic = None
        for i, result in enumerate(results):
            if result == best_result and i > 0:
                best_n_synthetic = augmentation_levels[i]
                break
        
        if best_n_synthetic:
            best_augmented_df = create_augmented_dataset(real_df, best_n_synthetic)
            output_path = f'data/processed/hiv_best_augmented_{len(real_df)}+{best_n_synthetic}.csv'
            best_augmented_df.to_csv(output_path, index=False, encoding='utf-8-sig')
            print(f"✓ 最佳配置数据已保存: {output_path}")
    
    return results


def main():
    """主流程"""
    print("\n" + "=" * 80)
    print("测试合成数据增强策略")
    print("策略: 保留全部190条真实数据 + 增加N条合成数据")
    print("=" * 80)
    
    results = test_different_augmentation_levels()
    
    print("\n" + "=" * 80)
    print("✓ 测试完成")
    print("=" * 80)
    
    return results


if __name__ == '__main__':
    results = main()
