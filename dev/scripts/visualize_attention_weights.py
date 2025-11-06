#!/usr/bin/env python3
"""
注意力权重可视化工具
生成不同风险阶段的注意力热力图，展示领域知识先验的影响
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


def plot_domain_priors_heatmap(predictor, save_path=None):
    """
    可视化领域知识先验权重
    """
    feature_names = predictor.feature_columns
    priors = predictor.prior_weights
    
    # 按先验权重排序
    sorted_indices = np.argsort(priors)[::-1]
    top_30_indices = sorted_indices[:30]
    
    top_features = [feature_names[i] for i in top_30_indices]
    top_priors = priors[top_30_indices]
    
    # 创建图表
    fig, ax = plt.subplots(figsize=(10, 12))
    
    # 颜色映射：>1.0为红色（正相关），=1.0为白色（中性）
    colors = ['#d73027' if p > 1.0 else '#f7f7f7' for p in top_priors]
    
    bars = ax.barh(range(len(top_features)), top_priors, color=colors, edgecolor='black', linewidth=0.5)
    
    # 添加数值标签
    for i, (bar, prior) in enumerate(zip(bars, top_priors)):
        width = bar.get_width()
        label = f'{prior:.2f}'
        ax.text(width + 0.02, bar.get_y() + bar.get_height()/2, 
               label, ha='left', va='center', fontsize=9)
    
    ax.set_yticks(range(len(top_features)))
    ax.set_yticklabels(top_features, fontsize=10)
    ax.set_xlabel('先验权重 (Prior Weight)', fontsize=12, fontweight='bold')
    ax.set_title('领域知识先验权重 - Top 30特征\n(红色=正相关先验, 白色=中性)', 
                fontsize=14, fontweight='bold', pad=20)
    ax.axvline(x=1.0, color='gray', linestyle='--', linewidth=1, alpha=0.5, label='中性权重=1.0')
    ax.legend(loc='lower right')
    ax.grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✓ 领域知识先验热力图已保存: {save_path}")
    
    plt.close()


def plot_attention_comparison_stages(predictor, X_samples, y_samples, save_path=None):
    """
    对比不同风险阶段的注意力权重分布
    """
    # 选择3个代表性样本：低风险、中风险、高风险
    low_risk_idx = np.where(y_samples == 1)[0][0] if len(np.where(y_samples == 1)[0]) > 0 else 0
    mid_risk_idx = np.where(y_samples == 2)[0][0] if len(np.where(y_samples == 2)[0]) > 0 else 1
    high_risk_idx = np.where(y_samples >= 3)[0][0] if len(np.where(y_samples >= 3)[0]) > 0 else 2
    
    samples = [
        ('低风险区 (预测<2)', X_samples[low_risk_idx]),
        ('中风险区 (预测=2-3)', X_samples[mid_risk_idx]),
        ('高风险区 (预测>3)', X_samples[high_risk_idx])
    ]
    
    fig, axes = plt.subplots(1, 3, figsize=(20, 10))
    
    for idx, (stage_name, X) in enumerate(samples):
        ax = axes[idx]
        
        # 获取注意力权重（使用predict_batch）
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
            label = f'{weight:.2f}'
            ax.text(width + 0.02, bar.get_y() + bar.get_height()/2, 
                   label, ha='left', va='center', fontsize=8)
        
        ax.set_yticks(range(len(top_features)))
        ax.set_yticklabels(top_features, fontsize=9)
        ax.set_xlabel('注意力权重', fontsize=11, fontweight='bold')
        ax.set_title(f'{stage_name}\nTop 20 关注特征', fontsize=12, fontweight='bold')
        ax.axvline(x=1.0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
        ax.grid(axis='x', alpha=0.3)
        ax.set_xlim(0.5, max(top_weights) * 1.1)
    
    plt.suptitle('不同疫情阶段的注意力权重对比', fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✓ 阶段对比图已保存: {save_path}")
    
    plt.close()



def plot_attention_heatmap_matrix(predictor, X_samples, save_path=None):
    """
    生成注意力权重热力图矩阵（样本 × 特征）
    """
    # 选择10个代表性样本
    n_samples = min(10, len(X_samples))
    sample_indices = np.linspace(0, len(X_samples)-1, n_samples, dtype=int)
    
    # 收集所有样本的注意力权重
    attention_matrix = []
    for idx in sample_indices:
        X_reshaped = X_samples[idx].reshape(1, -1)
        _, attention_weights_batch = predictor.predict_batch(X_reshaped, return_attention=True)
        attention_matrix.append(attention_weights_batch[0])
    
    attention_matrix = np.array(attention_matrix)
    
    # 选择Top 30特征（按平均注意力权重）
    mean_attention = attention_matrix.mean(axis=0)
    top_30_indices = np.argsort(mean_attention)[-30:]
    
    top_features = [predictor.feature_columns[i] for i in top_30_indices]
    attention_subset = attention_matrix[:, top_30_indices]
    
    # 创建热力图
    fig, ax = plt.subplots(figsize=(14, 10))
    
    sns.heatmap(attention_subset.T, 
                xticklabels=[f'样本{i+1}' for i in range(n_samples)],
                yticklabels=top_features,
                cmap='RdYlGn_r',
                center=1.0,
                vmin=0.5,
                vmax=2.0,
                annot=True,
                fmt='.2f',
                cbar_kws={'label': '注意力权重'},
                linewidths=0.5,
                linecolor='gray',
                ax=ax)
    
    ax.set_xlabel('样本', fontsize=12, fontweight='bold')
    ax.set_ylabel('特征', fontsize=12, fontweight='bold')
    ax.set_title('注意力权重热力图矩阵 (Top 30特征 × 10样本)\n颜色越深表示注意力权重越高', 
                fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✓ 注意力热力图矩阵已保存: {save_path}")
    
    plt.close()


def plot_prior_vs_learned_comparison(predictor, save_path=None):
    """
    对比领域知识先验 vs 数据驱动学习的特征重要性
    """
    feature_names = predictor.feature_columns
    priors = predictor.prior_weights
    importance = predictor.feature_importances
    
    # 归一化
    importance = importance / importance.sum() * priors.mean()
    
    # 选择Top 20特征（按先验权重）
    top_20_indices = np.argsort(priors)[-20:]
    
    top_features = [feature_names[i] for i in top_20_indices]
    top_priors = priors[top_20_indices]
    top_importance = importance[top_20_indices]
    
    # 创建对比图
    fig, ax = plt.subplots(figsize=(12, 10))
    
    y_pos = np.arange(len(top_features))
    width = 0.35
    
    bars1 = ax.barh(y_pos - width/2, top_priors, width, 
                    label='领域知识先验', color='#d73027', alpha=0.8, edgecolor='black', linewidth=0.5)
    bars2 = ax.barh(y_pos + width/2, top_importance, width, 
                    label='数据驱动学习', color='#4575b4', alpha=0.8, edgecolor='black', linewidth=0.5)
    
    # 添加数值标签
    for bars in [bars1, bars2]:
        for bar in bars:
            width_val = bar.get_width()
            ax.text(width_val + 0.02, bar.get_y() + bar.get_height()/2, 
                   f'{width_val:.2f}', ha='left', va='center', fontsize=8)
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(top_features, fontsize=10)
    ax.set_xlabel('权重值', fontsize=12, fontweight='bold')
    ax.set_title('领域知识先验 vs 数据驱动学习 - Top 20特征对比\n(DG-DAA融合两者优势)', 
                fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='lower right', fontsize=11)
    ax.axvline(x=1.0, color='gray', linestyle='--', linewidth=1, alpha=0.5, label='中性权重=1.0')
    ax.grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✓ 先验vs学习对比图已保存: {save_path}")
    
    plt.close()


def plot_attention_strength_impact(X_sample, model_path, save_path=None):
    """
    展示注意力强度参数α的影响
    """
    alphas = [0.0, 0.1, 0.3, 0.5, 0.7, 1.0]
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    axes = axes.flatten()
    
    for idx, alpha in enumerate(alphas):
        ax = axes[idx]
        
        # 创建不同α的预测器
        predictor = EnhancedPredictor(
            model_path=model_path,
            enable_attention=True,
            attention_strength=alpha
        )
        
        # 获取注意力权重
        X_reshaped = X_sample.reshape(1, -1)
        _, attention_weights_batch = predictor.predict_batch(X_reshaped, return_attention=True)
        attention_weights = attention_weights_batch[0]
        
        # 选择Top 15特征
        top_15_indices = np.argsort(attention_weights)[-15:]
        top_features = [predictor.feature_columns[i] for i in top_15_indices]
        top_weights = attention_weights[top_15_indices]
        
        # 颜色映射
        colors = plt.cm.RdYlGn_r(np.linspace(0.3, 0.9, len(top_weights)))
        
        bars = ax.barh(range(len(top_features)), top_weights, color=colors, edgecolor='black', linewidth=0.5)
        
        # 添加数值标签
        for i, (bar, weight) in enumerate(zip(bars, top_weights)):
            width = bar.get_width()
            label = f'{weight:.2f}'
            ax.text(width + 0.02, bar.get_y() + bar.get_height()/2, 
                   label, ha='left', va='center', fontsize=7)
        
        ax.set_yticks(range(len(top_features)))
        ax.set_yticklabels(top_features, fontsize=8)
        ax.set_xlabel('注意力权重', fontsize=10)
        
        if alpha == 0.0:
            title = f'α={alpha} (纯数据驱动)'
        elif alpha == 1.0:
            title = f'α={alpha} (纯领域先验)'
        else:
            title = f'α={alpha} (混合)'
        ax.set_title(title, fontsize=11, fontweight='bold')
        ax.axvline(x=1.0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
        ax.grid(axis='x', alpha=0.3)
        ax.set_xlim(0.5, max(top_weights) * 1.1)
    
    plt.suptitle('注意力强度参数α的影响 - Top 15特征\n(α=0: 纯数据驱动, α=1: 纯领域先验)', 
                fontsize=16, fontweight='bold', y=0.995)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✓ α参数影响图已保存: {save_path}")
    
    plt.close()


def main():
    """主函数"""
    print("="*80)
    print("  注意力权重可视化工具")
    print("="*80)
    
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. 加载增强预测器
    print("\n步骤1: 加载增强预测器...")
    model_path = os.path.join(script_dir, 'saved_models/final_model_3to5.pkl')
    predictor = EnhancedPredictor(
        model_path=model_path,
        enable_attention=True,
        attention_strength=0.3
    )
    print(f"✓ 预测器已加载 (attention_strength=0.3)")
    
    # 2. 加载数据
    print("\n步骤2: 加载数据...")
    data_path = os.path.join(script_dir, 'data/processed/hiv_data_processed.csv')
    df = pd.read_csv(data_path)
    exclude_cols = ['区县', 'risk_level', '按方案评定级别', 
                   '预测风险等级_5级', '置信度', '预测风险等级_3级', '风险描述']
    feature_columns = [col for col in df.columns if col not in exclude_cols]
    X = df[feature_columns].values
    y = df['risk_level'].values
    print(f"✓ 数据已加载: {len(X)}个样本, {len(feature_columns)}个特征")
    
    # 3. 生成可视化
    print("\n步骤3: 生成可视化图表...")
    
    # 3.1 领域知识先验热力图
    print("  3.1 生成领域知识先验热力图...")
    plot_domain_priors_heatmap(
        predictor,
        save_path=f'{OUTPUT_DIR}/domain_priors_heatmap.png'
    )
    
    # 3.2 不同阶段注意力对比
    print("  3.2 生成不同阶段注意力对比图...")
    plot_attention_comparison_stages(
        predictor,
        X, y,
        save_path=f'{OUTPUT_DIR}/attention_stages_comparison.png'
    )
    
    # 3.3 注意力热力图矩阵
    print("  3.3 生成注意力热力图矩阵...")
    plot_attention_heatmap_matrix(
        predictor,
        X,
        save_path=f'{OUTPUT_DIR}/attention_heatmap_matrix.png'
    )
    
    # 3.4 先验vs学习对比
    print("  3.4 生成先验vs学习对比图...")
    plot_prior_vs_learned_comparison(
        predictor,
        save_path=f'{OUTPUT_DIR}/prior_vs_learned_comparison.png'
    )
    
    # 3.5 α参数影响
    print("  3.5 生成α参数影响图...")
    plot_attention_strength_impact(
        X[0],
        model_path,
        save_path=f'{OUTPUT_DIR}/attention_strength_impact.png'
    )
    
    print("\n" + "="*80)
    print("✓ 所有可视化图表已生成")
    print(f"✓ 输出目录: {OUTPUT_DIR}")
    print("="*80)
    
    # 列出生成的文件
    print("\n生成的文件:")
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
