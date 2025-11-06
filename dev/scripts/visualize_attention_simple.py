#!/usr/bin/env python3
"""
注意力权重可视化工具 - 简化版
生成关键的注意力可视化图表
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.enhanced_predictor import EnhancedPredictor

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 输出目录
OUTPUT_DIR = 'outputs/attention_visualizations'
os.makedirs(OUTPUT_DIR, exist_ok=True)


def plot_domain_priors_simple(predictor, save_path):
    """可视化领域知识先验权重"""
    feature_names = predictor.feature_columns
    priors = predictor.prior_weights
    
    # 按先验权重排序，选择Top 30
    sorted_indices = np.argsort(priors)[::-1]
    top_30_indices = sorted_indices[:30]
    
    top_features = [feature_names[i] for i in top_30_indices]
    top_priors = priors[top_30_indices]
    
    # 创建图表
    fig, ax = plt.subplots(figsize=(10, 12))
    
    # 颜色：>1.0为红色，=1.0为灰色
    colors = ['#d73027' if p > 1.0 else '#cccccc' for p in top_priors]
    
    bars = ax.barh(range(len(top_features)), top_priors, color=colors, edgecolor='black', linewidth=0.5)
    
    # 添加数值标签
    for i, (bar, prior) in enumerate(zip(bars, top_priors)):
        width = bar.get_width()
        ax.text(width + 0.02, bar.get_y() + bar.get_height()/2, 
               f'{prior:.2f}', ha='left', va='center', fontsize=9)
    
    ax.set_yticks(range(len(top_features)))
    ax.set_yticklabels(top_features, fontsize=10)
    ax.set_xlabel('Prior Weight', fontsize=12, fontweight='bold')
    ax.set_title('Domain Knowledge Priors - Top 30 Features\n(Red=Positive Prior, Gray=Neutral)', 
                fontsize=14, fontweight='bold', pad=20)
    ax.axvline(x=1.0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    ax.grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Domain priors heatmap saved: {save_path}")


def plot_attention_comparison_simple(predictor, X_samples, y_samples, save_path):
    """对比不同风险阶段的注意力权重"""
    # 选择3个代表性样本
    low_idx = np.where(y_samples == 1)[0][0] if len(np.where(y_samples == 1)[0]) > 0 else 0
    mid_idx = np.where(y_samples == 2)[0][0] if len(np.where(y_samples == 2)[0]) > 0 else 1
    high_idx = np.where(y_samples >= 3)[0][0] if len(np.where(y_samples >= 3)[0]) > 0 else 2
    
    samples = [
        ('Low Risk (<2)', X_samples[low_idx]),
        ('Medium Risk (2-3)', X_samples[mid_idx]),
        ('High Risk (>3)', X_samples[high_idx])
    ]
    
    fig, axes = plt.subplots(1, 3, figsize=(20, 10))
    
    for idx, (stage_name, X) in enumerate(samples):
        ax = axes[idx]
        
        # 获取注意力权重
        X_reshaped = X.reshape(1, -1)
        _, attention_weights_batch = predictor.predict_batch(X_reshaped, return_attention=True)
        attention_weights = attention_weights_batch[0]
        
        # 选择Top 20特征
        top_20_indices = np.argsort(attention_weights)[-20:]
        top_features = [predictor.feature_columns[i] for i in top_20_indices]
        top_weights = attention_weights[top_20_indices]
        
        # 颜色映射
        colors = plt.cm.RdYlGn_r(np.linspace(0.3, 0.9, len(top_weights)))
        
        bars = ax.barh(range(len(top_features)), top_weights, color=colors, edgecolor='black', linewidth=0.5)
        
        # 添加数值标签
        for i, (bar, weight) in enumerate(zip(bars, top_weights)):
            width = bar.get_width()
            ax.text(width + 0.02, bar.get_y() + bar.get_height()/2, 
                   f'{weight:.2f}', ha='left', va='center', fontsize=8)
        
        ax.set_yticks(range(len(top_features)))
        ax.set_yticklabels(top_features, fontsize=9)
        ax.set_xlabel('Attention Weight', fontsize=11, fontweight='bold')
        ax.set_title(f'{stage_name}\nTop 20 Features', fontsize=12, fontweight='bold')
        ax.axvline(x=1.0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
        ax.grid(axis='x', alpha=0.3)
        ax.set_xlim(0.5, max(top_weights) * 1.1)
    
    plt.suptitle('Attention Weights Comparison Across Risk Stages', fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Stage comparison saved: {save_path}")


def main():
    """主函数"""
    print("="*80)
    print("  Attention Weights Visualization Tool")
    print("="*80)
    
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. 加载增强预测器
    print("\nStep 1: Loading enhanced predictor...")
    model_path = os.path.join(script_dir, 'saved_models/final_model_3to5.pkl')
    predictor = EnhancedPredictor(
        model_path=model_path,
        enable_attention=True,
        attention_strength=0.3
    )
    print(f"✓ Predictor loaded (attention_strength=0.3)")
    
    # 2. 加载数据
    print("\nStep 2: Loading data...")
    data_path = os.path.join(script_dir, 'data/processed/hiv_data_processed.csv')
    df = pd.read_csv(data_path)
    exclude_cols = ['区县', 'risk_level', '按方案评定级别', 
                   '预测风险等级_5级', '置信度', '预测风险等级_3级', '风险描述']
    feature_columns = [col for col in df.columns if col not in exclude_cols]
    X = df[feature_columns].values
    y = df['risk_level'].values
    print(f"✓ Data loaded: {len(X)} samples, {len(feature_columns)} features")
    
    # 3. 生成可视化
    print("\nStep 3: Generating visualizations...")
    
    # 3.1 领域知识先验
    print("  3.1 Generating domain priors heatmap...")
    plot_domain_priors_simple(
        predictor,
        save_path=f'{OUTPUT_DIR}/domain_priors_heatmap.png'
    )
    
    # 3.2 不同阶段注意力对比
    print("  3.2 Generating attention comparison across stages...")
    plot_attention_comparison_simple(
        predictor,
        X, y,
        save_path=f'{OUTPUT_DIR}/attention_stages_comparison.png'
    )
    
    print("\n" + "="*80)
    print("✓ All visualizations generated")
    print(f"✓ Output directory: {OUTPUT_DIR}")
    print("="*80)
    
    # 列出生成的文件
    print("\nGenerated files:")
    for filename in os.listdir(OUTPUT_DIR):
        if filename.endswith('.png'):
            filepath = os.path.join(OUTPUT_DIR, filename)
            size_kb = os.path.getsize(filepath) / 1024
            print(f"  - {filename} ({size_kb:.1f} KB)")


if __name__ == '__main__':
    try:
        main()
    finally:
        import matplotlib.pyplot as plt
        import sys
        plt.close('all')
        sys.exit(0)
