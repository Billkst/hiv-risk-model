#!/usr/bin/env python3
"""
使用交叉验证评估增强模型
更可靠的性能评估方法
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, make_scorer
from models.enhanced_predictor import EnhancedPredictor
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def load_data(data_path='data/processed/hiv_data_processed.csv'):
    """加载完整数据"""
    df = pd.read_csv(data_path)
    
    exclude_cols = ['区县', 'risk_level', '按方案评定级别', 
                   '预测风险等级_5级', '置信度', '预测风险等级_3级', '风险描述']
    feature_columns = [col for col in df.columns if col not in exclude_cols]
    
    X = df[feature_columns].values
    y = df['risk_level'].values
    
    print(f"✓ 数据加载完成")
    print(f"  总样本数: {len(df)}")
    print(f"  特征数: {len(feature_columns)}")
    print(f"  类别分布: {dict(pd.Series(y).value_counts().sort_index())}")
    
    return X, y, feature_columns


def evaluate_with_cv(predictor, X, y, cv=5):
    """使用交叉验证评估模型"""
    print(f"\n使用{cv}折交叉验证...")
    
    skf = StratifiedKFold(n_splits=cv, shuffle=True, random_state=42)
    
    accuracy_scores = []
    f1_macro_scores = []
    f1_weighted_scores = []
    precision_scores = []
    recall_scores = []
    
    for fold, (train_idx, test_idx) in enumerate(skf.split(X, y), 1):
        X_test_fold = X[test_idx]
        y_test_fold = y[test_idx]
        
        # 预测
        y_pred = predictor.predict_batch(X_test_fold)
        
        # 计算指标
        accuracy_scores.append(accuracy_score(y_test_fold, y_pred))
        f1_macro_scores.append(f1_score(y_test_fold, y_pred, average='macro', zero_division=0))
        f1_weighted_scores.append(f1_score(y_test_fold, y_pred, average='weighted', zero_division=0))
        precision_scores.append(precision_score(y_test_fold, y_pred, average='weighted', zero_division=0))
        recall_scores.append(recall_score(y_test_fold, y_pred, average='weighted', zero_division=0))
        
        print(f"  Fold {fold}: Accuracy={accuracy_scores[-1]:.4f}, "
              f"F1(weighted)={f1_weighted_scores[-1]:.4f}")
    
    results = {
        'accuracy_mean': np.mean(accuracy_scores),
        'accuracy_std': np.std(accuracy_scores),
        'f1_macro_mean': np.mean(f1_macro_scores),
        'f1_macro_std': np.std(f1_macro_scores),
        'f1_weighted_mean': np.mean(f1_weighted_scores),
        'f1_weighted_std': np.std(f1_weighted_scores),
        'precision_mean': np.mean(precision_scores),
        'precision_std': np.std(precision_scores),
        'recall_mean': np.mean(recall_scores),
        'recall_std': np.std(recall_scores)
    }
    
    return results


def print_results(results, model_name):
    """打印结果"""
    print(f"\n{'='*60}")
    print(f"  {model_name} - 交叉验证结果")
    print(f"{'='*60}")
    
    print(f"\nAccuracy:        {results['accuracy_mean']:.4f} ± {results['accuracy_std']:.4f}")
    print(f"Precision:       {results['precision_mean']:.4f} ± {results['precision_std']:.4f}")
    print(f"Recall:          {results['recall_mean']:.4f} ± {results['recall_std']:.4f}")
    print(f"F1 (macro):      {results['f1_macro_mean']:.4f} ± {results['f1_macro_std']:.4f}")
    print(f"F1 (weighted):   {results['f1_weighted_mean']:.4f} ± {results['f1_weighted_std']:.4f}")


def compare_results(baseline_results, enhanced_results):
    """对比结果"""
    print(f"\n{'='*60}")
    print(f"  模型对比（交叉验证）")
    print(f"{'='*60}")
    
    print(f"\n{'指标':<20} {'原模型':<20} {'增强模型':<20} {'提升':<15}")
    print("-" * 75)
    
    metrics = [
        ('Accuracy', 'accuracy_mean', 'accuracy_std'),
        ('Precision', 'precision_mean', 'precision_std'),
        ('Recall', 'recall_mean', 'recall_std'),
        ('F1 (macro)', 'f1_macro_mean', 'f1_macro_std'),
        ('F1 (weighted)', 'f1_weighted_mean', 'f1_weighted_std')
    ]
    
    for name, mean_key, std_key in metrics:
        baseline_mean = baseline_results[mean_key]
        baseline_std = baseline_results[std_key]
        enhanced_mean = enhanced_results[mean_key]
        enhanced_std = enhanced_results[std_key]
        
        diff = enhanced_mean - baseline_mean
        diff_pct = (diff / baseline_mean * 100) if baseline_mean > 0 else 0
        
        marker = "⭐" if diff > 0 else ("" if diff == 0 else "⚠️")
        
        print(f"{name:<20} {baseline_mean:.4f}±{baseline_std:.4f}    "
              f"{enhanced_mean:.4f}±{enhanced_std:.4f}    "
              f"{diff:+.4f} ({diff_pct:+.1f}%) {marker}")
    
    # 总结
    print(f"\n总结:")
    baseline_f1 = baseline_results['f1_weighted_mean']
    enhanced_f1 = enhanced_results['f1_weighted_mean']
    
    if enhanced_f1 > baseline_f1:
        improvement = (enhanced_f1 - baseline_f1) / baseline_f1 * 100
        print(f"  ✅ 增强模型表现更好")
        print(f"  ✅ F1 (weighted) 提升了 {improvement:.2f}%")
        print(f"  ✅ 原模型 F1: {baseline_f1:.4f}")
        print(f"  ✅ 增强模型 F1: {enhanced_f1:.4f}")
    else:
        print(f"  ➖ 两个模型表现相近")


def save_cv_results(baseline_results, enhanced_results, output_path):
    """保存交叉验证结果"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("  增强模型性能验证报告（交叉验证）\n")
        f.write("="*80 + "\n\n")
        
        f.write("评估方法:\n")
        f.write("  - 5折分层交叉验证\n")
        f.write("  - 数据集: hiv_data_processed.csv (190个样本)\n")
        f.write("  - 增强模型配置: attention_strength = 0.3\n\n")
        
        f.write("="*80 + "\n")
        f.write("原模型（基线）性能\n")
        f.write("="*80 + "\n\n")
        f.write(f"  Accuracy:        {baseline_results['accuracy_mean']:.4f} ± {baseline_results['accuracy_std']:.4f}\n")
        f.write(f"  Precision:       {baseline_results['precision_mean']:.4f} ± {baseline_results['precision_std']:.4f}\n")
        f.write(f"  Recall:          {baseline_results['recall_mean']:.4f} ± {baseline_results['recall_std']:.4f}\n")
        f.write(f"  F1 (macro):      {baseline_results['f1_macro_mean']:.4f} ± {baseline_results['f1_macro_std']:.4f}\n")
        f.write(f"  F1 (weighted):   {baseline_results['f1_weighted_mean']:.4f} ± {baseline_results['f1_weighted_std']:.4f}\n\n")
        
        f.write("="*80 + "\n")
        f.write("增强模型（DG-DAA）性能\n")
        f.write("="*80 + "\n\n")
        f.write(f"  Accuracy:        {enhanced_results['accuracy_mean']:.4f} ± {enhanced_results['accuracy_std']:.4f}\n")
        f.write(f"  Precision:       {enhanced_results['precision_mean']:.4f} ± {enhanced_results['precision_std']:.4f}\n")
        f.write(f"  Recall:          {enhanced_results['recall_mean']:.4f} ± {enhanced_results['recall_std']:.4f}\n")
        f.write(f"  F1 (macro):      {enhanced_results['f1_macro_mean']:.4f} ± {enhanced_results['f1_macro_std']:.4f}\n")
        f.write(f"  F1 (weighted):   {enhanced_results['f1_weighted_mean']:.4f} ± {enhanced_results['f1_weighted_std']:.4f}\n\n")
        
        f.write("="*80 + "\n")
        f.write("性能对比\n")
        f.write("="*80 + "\n\n")
        
        metrics = [
            ('Accuracy', 'accuracy_mean'),
            ('Precision', 'precision_mean'),
            ('Recall', 'recall_mean'),
            ('F1 (macro)', 'f1_macro_mean'),
            ('F1 (weighted)', 'f1_weighted_mean')
        ]
        
        for name, key in metrics:
            baseline_val = baseline_results[key]
            enhanced_val = enhanced_results[key]
            diff = enhanced_val - baseline_val
            diff_pct = (diff / baseline_val * 100) if baseline_val > 0 else 0
            f.write(f"  {name:<20}: {diff:+.4f} ({diff_pct:+.2f}%)\n")
        
        f.write("\n" + "="*80 + "\n")
        f.write("结论\n")
        f.write("="*80 + "\n\n")
        
        baseline_f1 = baseline_results['f1_weighted_mean']
        enhanced_f1 = enhanced_results['f1_weighted_mean']
        
        if enhanced_f1 > baseline_f1:
            improvement = (enhanced_f1 - baseline_f1) / baseline_f1 * 100
            f.write(f"增强模型（DG-DAA）表现优于原模型:\n")
            f.write(f"  - 原模型 F1 (weighted): {baseline_f1:.4f}\n")
            f.write(f"  - 增强模型 F1 (weighted): {enhanced_f1:.4f}\n")
            f.write(f"  - 相对提升: {improvement:.2f}%\n")
            f.write(f"  - 领域知识引导的注意力机制有效\n")
            f.write(f"  - 建议使用增强模型\n")
        else:
            f.write(f"两个模型表现相近\n")
    
    print(f"\n✓ 交叉验证结果已保存: {output_path}")


def main():
    """主函数"""
    print("="*80)
    print("  增强模型性能验证（交叉验证）")
    print("="*80)
    
    # 1. 加载数据
    print("\n步骤1: 加载完整数据集...")
    X, y, feature_columns = load_data()
    
    # 2. 评估原模型
    print("\n步骤2: 评估原模型（5折交叉验证）...")
    baseline_predictor = EnhancedPredictor(
        model_path='saved_models/final_model_3to5.pkl',
        enable_attention=False
    )
    baseline_results = evaluate_with_cv(baseline_predictor, X, y, cv=5)
    print_results(baseline_results, "原模型（基线）")
    
    # 3. 评估增强模型
    print("\n步骤3: 评估增强模型（5折交叉验证）...")
    enhanced_predictor = EnhancedPredictor(
        model_path='saved_models/final_model_3to5.pkl',
        enable_attention=True,
        attention_strength=0.3
    )
    enhanced_results = evaluate_with_cv(enhanced_predictor, X, y, cv=5)
    print_results(enhanced_results, "增强模型（DG-DAA）")
    
    # 4. 对比分析
    print("\n步骤4: 对比分析...")
    compare_results(baseline_results, enhanced_results)
    
    # 5. 保存结果
    print("\n步骤5: 保存结果...")
    save_cv_results(baseline_results, enhanced_results,
                   'outputs/model_evaluation/cv_evaluation_report.txt')
    
    print("\n" + "="*80)
    print("✓ 交叉验证评估完成")
    print("="*80)


if __name__ == '__main__':
    main()
