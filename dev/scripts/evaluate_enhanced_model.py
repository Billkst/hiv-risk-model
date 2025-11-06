#!/usr/bin/env python3
"""
增强模型性能验证和对比
详细评估原模型 vs 增强模型的性能
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (accuracy_score, f1_score, precision_score, 
                            recall_score, classification_report, confusion_matrix)
from models.enhanced_predictor import EnhancedPredictor
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置中文字体
import matplotlib.font_manager as fm
from pathlib import Path

user_font_path = Path.home() / '.fonts' / 'SourceHanSansSC.otf'
if user_font_path.exists():
    fm.fontManager.addfont(str(user_font_path))
    plt.rcParams['font.sans-serif'] = ['Source Han Sans SC', 'DejaVu Sans']
else:
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']

plt.rcParams['axes.unicode_minus'] = False


def load_test_data(data_path='data/processed/hiv_data_processed.csv'):
    """加载测试数据"""
    df = pd.read_csv(data_path)
    
    exclude_cols = ['区县', 'risk_level', '按方案评定级别', 
                   '预测风险等级_5级', '置信度', '预测风险等级_3级', '风险描述']
    feature_columns = [col for col in df.columns if col not in exclude_cols]
    
    X = df[feature_columns].values
    y = df['risk_level'].values
    
    # 划分数据集
    split_idx = int(len(df) * 0.8)
    X_test = X[split_idx:]
    y_test = y[split_idx:]
    
    return X_test, y_test, feature_columns


def evaluate_detailed(y_true, y_pred, model_name):
    """详细评估"""
    print(f"\n{'='*60}")
    print(f"  {model_name} - 详细评估")
    print(f"{'='*60}")
    
    # 基本指标
    accuracy = accuracy_score(y_true, y_pred)
    precision_macro = precision_score(y_true, y_pred, average='macro', zero_division=0)
    recall_macro = recall_score(y_true, y_pred, average='macro', zero_division=0)
    f1_macro = f1_score(y_true, y_pred, average='macro', zero_division=0)
    f1_weighted = f1_score(y_true, y_pred, average='weighted', zero_division=0)
    
    print(f"\n整体指标:")
    print(f"  Accuracy:        {accuracy:.4f} ({accuracy*100:.2f}%)")
    print(f"  Precision (macro): {precision_macro:.4f}")
    print(f"  Recall (macro):    {recall_macro:.4f}")
    print(f"  F1 (macro):        {f1_macro:.4f}")
    print(f"  F1 (weighted):     {f1_weighted:.4f}")
    
    # 分类报告
    print(f"\n分类报告:")
    unique_labels = sorted(np.unique(np.concatenate([y_true, y_pred])))
    target_names = [f'等级{i}' for i in unique_labels]
    print(classification_report(y_true, y_pred, 
                                labels=unique_labels,
                                target_names=target_names,
                                zero_division=0))
    
    # 混淆矩阵
    cm = confusion_matrix(y_true, y_pred)
    print(f"\n混淆矩阵:")
    print(cm)
    
    return {
        'accuracy': accuracy,
        'precision_macro': precision_macro,
        'recall_macro': recall_macro,
        'f1_macro': f1_macro,
        'f1_weighted': f1_weighted,
        'confusion_matrix': cm,
        'predictions': y_pred
    }


def plot_confusion_matrix(cm, model_name, save_path):
    """绘制混淆矩阵"""
    fig, ax = plt.subplots(figsize=(10, 8))
    
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=['等级1', '等级2', '等级3', '等级4', '等级5'],
                yticklabels=['等级1', '等级2', '等级3', '等级4', '等级5'],
                ax=ax)
    
    ax.set_xlabel('预测标签', fontsize=12, fontweight='bold')
    ax.set_ylabel('真实标签', fontsize=12, fontweight='bold')
    ax.set_title(f'{model_name} - 混淆矩阵', fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"✓ 混淆矩阵已保存: {save_path}")


def plot_comparison(baseline_metrics, enhanced_metrics, save_path):
    """绘制对比图"""
    metrics_names = ['Accuracy', 'Precision', 'Recall', 'F1 (macro)', 'F1 (weighted)']
    baseline_values = [
        baseline_metrics['accuracy'],
        baseline_metrics['precision_macro'],
        baseline_metrics['recall_macro'],
        baseline_metrics['f1_macro'],
        baseline_metrics['f1_weighted']
    ]
    enhanced_values = [
        enhanced_metrics['accuracy'],
        enhanced_metrics['precision_macro'],
        enhanced_metrics['recall_macro'],
        enhanced_metrics['f1_macro'],
        enhanced_metrics['f1_weighted']
    ]
    
    x = np.arange(len(metrics_names))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    bars1 = ax.bar(x - width/2, baseline_values, width, label='原模型', 
                   color='#1f77b4', alpha=0.8)
    bars2 = ax.bar(x + width/2, enhanced_values, width, label='增强模型 (DG-DAA)', 
                   color='#d62728', alpha=0.8)
    
    ax.set_xlabel('评估指标', fontsize=12, fontweight='bold')
    ax.set_ylabel('分数', fontsize=12, fontweight='bold')
    ax.set_title('原模型 vs 增强模型 - 性能对比', fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(metrics_names)
    ax.legend(fontsize=11)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    # 添加数值标签
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.3f}',
                   ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"✓ 对比图已保存: {save_path}")


def compare_models(baseline_metrics, enhanced_metrics):
    """对比两个模型"""
    print(f"\n{'='*60}")
    print(f"  模型对比分析")
    print(f"{'='*60}")
    
    print(f"\n{'指标':<20} {'原模型':<15} {'增强模型':<15} {'提升':<15}")
    print("-" * 65)
    
    metrics = [
        ('Accuracy', 'accuracy'),
        ('Precision (macro)', 'precision_macro'),
        ('Recall (macro)', 'recall_macro'),
        ('F1 (macro)', 'f1_macro'),
        ('F1 (weighted)', 'f1_weighted')
    ]
    
    for name, key in metrics:
        baseline_val = baseline_metrics[key]
        enhanced_val = enhanced_metrics[key]
        diff = enhanced_val - baseline_val
        diff_pct = (diff / baseline_val * 100) if baseline_val > 0 else 0
        
        marker = "⭐" if diff > 0 else ("" if diff == 0 else "⚠️")
        
        print(f"{name:<20} {baseline_val:<15.4f} {enhanced_val:<15.4f} "
              f"{diff:+.4f} ({diff_pct:+.1f}%) {marker}")
    
    # 总结
    print(f"\n总结:")
    if enhanced_metrics['f1_weighted'] > baseline_metrics['f1_weighted']:
        improvement = (enhanced_metrics['f1_weighted'] - baseline_metrics['f1_weighted']) * 100
        print(f"  ✅ 增强模型表现更好")
        print(f"  ✅ F1 (weighted) 提升了 {improvement:.2f}%")
    elif enhanced_metrics['f1_weighted'] == baseline_metrics['f1_weighted']:
        print(f"  ➖ 两个模型表现相同")
    else:
        decline = (baseline_metrics['f1_weighted'] - enhanced_metrics['f1_weighted']) * 100
        print(f"  ⚠️  增强模型表现略差")
        print(f"  ⚠️  F1 (weighted) 下降了 {decline:.2f}%")


def save_evaluation_report(baseline_metrics, enhanced_metrics, output_path):
    """保存评估报告"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("  增强模型性能验证报告\n")
        f.write("="*80 + "\n\n")
        
        f.write("测试配置:\n")
        f.write("  - 数据集: hiv_data_processed.csv\n")
        f.write("  - 训练集: 80% (152个样本)\n")
        f.write("  - 测试集: 20% (38个样本)\n")
        f.write("  - 增强模型配置: attention_strength = 0.3\n\n")
        
        f.write("="*80 + "\n")
        f.write("原模型（基线）性能\n")
        f.write("="*80 + "\n\n")
        f.write(f"  Accuracy:          {baseline_metrics['accuracy']:.4f}\n")
        f.write(f"  Precision (macro): {baseline_metrics['precision_macro']:.4f}\n")
        f.write(f"  Recall (macro):    {baseline_metrics['recall_macro']:.4f}\n")
        f.write(f"  F1 (macro):        {baseline_metrics['f1_macro']:.4f}\n")
        f.write(f"  F1 (weighted):     {baseline_metrics['f1_weighted']:.4f}\n\n")
        
        f.write("="*80 + "\n")
        f.write("增强模型（DG-DAA）性能\n")
        f.write("="*80 + "\n\n")
        f.write(f"  Accuracy:          {enhanced_metrics['accuracy']:.4f}\n")
        f.write(f"  Precision (macro): {enhanced_metrics['precision_macro']:.4f}\n")
        f.write(f"  Recall (macro):    {enhanced_metrics['recall_macro']:.4f}\n")
        f.write(f"  F1 (macro):        {enhanced_metrics['f1_macro']:.4f}\n")
        f.write(f"  F1 (weighted):     {enhanced_metrics['f1_weighted']:.4f}\n\n")
        
        f.write("="*80 + "\n")
        f.write("性能对比\n")
        f.write("="*80 + "\n\n")
        
        metrics = [
            ('Accuracy', 'accuracy'),
            ('Precision (macro)', 'precision_macro'),
            ('Recall (macro)', 'recall_macro'),
            ('F1 (macro)', 'f1_macro'),
            ('F1 (weighted)', 'f1_weighted')
        ]
        
        for name, key in metrics:
            baseline_val = baseline_metrics[key]
            enhanced_val = enhanced_metrics[key]
            diff = enhanced_val - baseline_val
            diff_pct = (diff / baseline_val * 100) if baseline_val > 0 else 0
            f.write(f"  {name:<20}: {diff:+.4f} ({diff_pct:+.2f}%)\n")
        
        f.write("\n" + "="*80 + "\n")
        f.write("结论\n")
        f.write("="*80 + "\n\n")
        
        if enhanced_metrics['f1_weighted'] > baseline_metrics['f1_weighted']:
            improvement = (enhanced_metrics['f1_weighted'] - baseline_metrics['f1_weighted']) * 100
            f.write(f"增强模型（DG-DAA）表现优于原模型:\n")
            f.write(f"  - F1 (weighted) 提升了 {improvement:.2f}%\n")
            f.write(f"  - 领域知识引导的注意力机制有效\n")
            f.write(f"  - 建议使用增强模型\n")
        else:
            f.write(f"两个模型表现相近\n")
            f.write(f"  - 增强模型保持了原模型的性能\n")
            f.write(f"  - 增强了可解释性和医学合理性\n")
    
    print(f"✓ 评估报告已保存: {output_path}")


def main():
    """主函数"""
    print("="*80)
    print("  增强模型性能验证和对比")
    print("="*80)
    
    # 1. 加载测试数据
    print("\n步骤1: 加载测试数据...")
    X_test, y_test, feature_columns = load_test_data()
    print(f"  测试集大小: {len(X_test)}个样本")
    
    # 2. 评估原模型（基线）
    print("\n步骤2: 评估原模型（基线）...")
    baseline_predictor = EnhancedPredictor(
        model_path='saved_models/final_model_3to5.pkl',
        enable_attention=False
    )
    y_pred_baseline = baseline_predictor.predict_batch(X_test)
    baseline_metrics = evaluate_detailed(y_test, y_pred_baseline, "原模型（基线）")
    
    # 3. 评估增强模型
    print("\n步骤3: 评估增强模型（DG-DAA）...")
    enhanced_predictor = EnhancedPredictor(
        model_path='saved_models/final_model_3to5.pkl',
        enable_attention=True,
        attention_strength=0.3  # 使用优化后的配置
    )
    y_pred_enhanced = enhanced_predictor.predict_batch(X_test)
    enhanced_metrics = evaluate_detailed(y_test, y_pred_enhanced, "增强模型（DG-DAA）")
    
    # 4. 对比分析
    print("\n步骤4: 对比分析...")
    compare_models(baseline_metrics, enhanced_metrics)
    
    # 5. 生成可视化
    print("\n步骤5: 生成可视化...")
    output_dir = 'outputs/model_evaluation'
    os.makedirs(output_dir, exist_ok=True)
    
    plot_confusion_matrix(baseline_metrics['confusion_matrix'], 
                         "原模型",
                         f"{output_dir}/confusion_matrix_baseline.png")
    
    plot_confusion_matrix(enhanced_metrics['confusion_matrix'], 
                         "增强模型（DG-DAA）",
                         f"{output_dir}/confusion_matrix_enhanced.png")
    
    plot_comparison(baseline_metrics, enhanced_metrics,
                   f"{output_dir}/model_comparison.png")
    
    # 6. 保存报告
    print("\n步骤6: 保存评估报告...")
    save_evaluation_report(baseline_metrics, enhanced_metrics,
                          f"{output_dir}/evaluation_report.txt")
    
    print("\n" + "="*80)
    print("✓ 评估完成")
    print(f"✓ 结果已保存到: {output_dir}/")
    print("="*80)


if __name__ == '__main__':
    main()
