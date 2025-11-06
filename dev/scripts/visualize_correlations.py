#!/usr/bin/env python3
"""
风险因素相关性可视化工具
生成热力图、条形图、散点图等
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import os
from models.correlation_analyzer import RiskFactorCorrelationAnalyzer

# 设置中文字体
import matplotlib.font_manager as fm
from pathlib import Path

user_font_path = Path.home() / '.fonts' / 'SourceHanSansSC.otf'
if user_font_path.exists():
    fm.fontManager.addfont(str(user_font_path))
    plt.rcParams['font.sans-serif'] = ['Source Han Sans SC', 'DejaVu Sans']
    print(f"✓ 使用中文字体: Source Han Sans SC")
else:
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
    print(f"⚠️  使用默认字体")

plt.rcParams['axes.unicode_minus'] = False

# 输出目录
OUTPUT_DIR = 'outputs/correlation_visualizations'
os.makedirs(OUTPUT_DIR, exist_ok=True)


def plot_correlation_heatmap(analyzer, correlation_results, save_path=None, top_k=30):
    """
    绘制相关性热力图
    显示Top K个特征与风险等级的相关系数
    
    Args:
        analyzer: 分析器实例
        correlation_results: 相关性分析结果
        save_path: 保存路径
        top_k: 显示Top K个特征
    """
    print(f"\n生成相关性热力图 (Top {top_k})...")
    
    # 获取Top K特征
    top_features = analyzer.get_top_correlations(correlation_results, top_k=top_k)
    
    # 提取数据
    feature_names = [item['feature'] for item in top_features]
    pearson_r = [item['pearson_r'] for item in top_features]
    
    # 创建数据矩阵（单列热力图）
    data = np.array(pearson_r).reshape(-1, 1)
    
    # 创建图表
    fig, ax = plt.subplots(figsize=(8, max(12, top_k * 0.4)))
    
    # 绘制热力图
    sns.heatmap(
        data,
        annot=True,
        fmt='.3f',
        cmap='RdBu_r',
        center=0,
        vmin=-1,
        vmax=1,
        cbar_kws={'label': 'Pearson相关系数'},
        yticklabels=feature_names,
        xticklabels=['风险等级'],
        ax=ax
    )
    
    # 设置标题
    ax.set_title(f'特征与风险等级相关性热力图 (Top {top_k})', 
                fontsize=16, fontweight='bold', pad=20)
    
    # 调整布局
    plt.tight_layout()
    
    # 保存
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"✓ 热力图已保存: {save_path}")
    
    plt.close()


def plot_top_correlations_bar(analyzer, correlation_results, save_path=None, top_k=20):
    """
    绘制Top K相关特征条形图
    
    Args:
        analyzer: 分析器实例
        correlation_results: 相关性分析结果
        save_path: 保存路径
        top_k: 显示Top K个特征
    """
    print(f"\n生成Top {top_k}相关特征条形图...")
    
    # 获取Top K特征
    top_features = analyzer.get_top_correlations(correlation_results, top_k=top_k)
    
    # 提取数据
    feature_names = [item['feature'] for item in top_features]
    pearson_r = [item['pearson_r'] for item in top_features]
    
    # 反转顺序（最高的在上面）
    feature_names = feature_names[::-1]
    pearson_r = pearson_r[::-1]
    
    # 创建图表
    fig, ax = plt.subplots(figsize=(12, max(10, top_k * 0.5)))
    
    # 颜色：正相关红色，负相关蓝色
    colors = ['#d62728' if r > 0 else '#1f77b4' for r in pearson_r]
    
    # 绘制条形图
    y_pos = np.arange(len(feature_names))
    bars = ax.barh(y_pos, pearson_r, color=colors, alpha=0.8, height=0.7)
    
    # 设置标签
    ax.set_yticks(y_pos)
    ax.set_yticklabels(feature_names, fontsize=11)
    ax.set_xlabel('Pearson相关系数', fontsize=13, fontweight='bold')
    ax.set_title(f'Top {top_k} 相关性最强特征', fontsize=16, fontweight='bold', pad=20)
    
    # 添加网格
    ax.grid(axis='x', alpha=0.3, linestyle='--', linewidth=0.5)
    ax.set_axisbelow(True)
    
    # 添加零线
    ax.axvline(x=0, color='black', linewidth=1.2)
    
    # 添加数值标签
    for i, (bar, r) in enumerate(zip(bars, pearson_r)):
        width = bar.get_width()
        x_pos = width + (0.02 if width > 0 else -0.02)
        ha = 'left' if width > 0 else 'right'
        ax.text(x_pos, i, f'{r:+.3f}', va='center', ha=ha, fontsize=10, fontweight='bold')
    
    # 添加图例
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#d62728', alpha=0.8, label='正相关（增加风险）'),
        Patch(facecolor='#1f77b4', alpha=0.8, label='负相关（降低风险）')
    ]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=11, framealpha=0.9)
    
    # 调整布局
    plt.subplots_adjust(left=0.25, right=0.95, top=0.94, bottom=0.06)
    
    # 保存
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"✓ 条形图已保存: {save_path}")
    
    plt.close()


def plot_known_correlations_verification(analyzer, verification_results, correlation_results, save_path=None):
    """
    绘制已知关联验证对比图
    
    Args:
        analyzer: 分析器实例
        verification_results: 验证结果
        correlation_results: 相关性分析结果
        save_path: 保存路径
    """
    print(f"\n生成已知关联验证对比图...")
    
    # 创建图表
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 10))
    
    # === 左图：正相关特征 ===
    positive_features = []
    positive_r = []
    positive_colors = []
    
    for req_name, model_name in analyzer.positive_features.items():
        if model_name and model_name in correlation_results:
            result = correlation_results[model_name]
            r = result['pearson_r']
            p = result['pearson_p']
            
            positive_features.append(req_name)
            positive_r.append(r)
            
            # 颜色：通过验证为绿色，未通过为红色
            if r > 0 and p < 0.05:
                positive_colors.append('#2ca02c')  # 绿色
            else:
                positive_colors.append('#d62728')  # 红色
    
    # 反转顺序
    positive_features = positive_features[::-1]
    positive_r = positive_r[::-1]
    positive_colors = positive_colors[::-1]
    
    y_pos = np.arange(len(positive_features))
    ax1.barh(y_pos, positive_r, color=positive_colors, alpha=0.8, height=0.7)
    
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(positive_features, fontsize=11)
    ax1.set_xlabel('Pearson相关系数', fontsize=12, fontweight='bold')
    ax1.set_title('已知正相关特征验证\n（预期: r > 0, p < 0.05）', 
                 fontsize=14, fontweight='bold', pad=15)
    ax1.axvline(x=0, color='black', linewidth=1.2)
    ax1.grid(axis='x', alpha=0.3, linestyle='--')
    ax1.set_axisbelow(True)
    
    # 添加数值标签
    for i, r in enumerate(positive_r):
        x_pos = r + (0.02 if r > 0 else -0.02)
        ha = 'left' if r > 0 else 'right'
        ax1.text(x_pos, i, f'{r:+.3f}', va='center', ha=ha, fontsize=9, fontweight='bold')
    
    # 添加图例
    from matplotlib.patches import Patch
    legend1 = [
        Patch(facecolor='#2ca02c', alpha=0.8, label='验证通过'),
        Patch(facecolor='#d62728', alpha=0.8, label='验证未通过')
    ]
    ax1.legend(handles=legend1, loc='lower right', fontsize=10)
    
    # === 右图：负相关特征 ===
    negative_features = []
    negative_r = []
    negative_colors = []
    
    for req_name, model_name in analyzer.negative_features.items():
        if model_name and model_name in correlation_results:
            result = correlation_results[model_name]
            r = result['pearson_r']
            p = result['pearson_p']
            
            negative_features.append(req_name)
            negative_r.append(r)
            
            # 颜色：通过验证为绿色，未通过为红色
            if r < 0 and p < 0.05:
                negative_colors.append('#2ca02c')  # 绿色
            else:
                negative_colors.append('#d62728')  # 红色
    
    # 反转顺序
    negative_features = negative_features[::-1]
    negative_r = negative_r[::-1]
    negative_colors = negative_colors[::-1]
    
    y_pos = np.arange(len(negative_features))
    ax2.barh(y_pos, negative_r, color=negative_colors, alpha=0.8, height=0.7)
    
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(negative_features, fontsize=11)
    ax2.set_xlabel('Pearson相关系数', fontsize=12, fontweight='bold')
    ax2.set_title('已知负相关特征验证\n（预期: r < 0, p < 0.05）', 
                 fontsize=14, fontweight='bold', pad=15)
    ax2.axvline(x=0, color='black', linewidth=1.2)
    ax2.grid(axis='x', alpha=0.3, linestyle='--')
    ax2.set_axisbelow(True)
    
    # 添加数值标签
    for i, r in enumerate(negative_r):
        x_pos = r + (0.02 if r > 0 else -0.02)
        ha = 'left' if r > 0 else 'right'
        ax2.text(x_pos, i, f'{r:+.3f}', va='center', ha=ha, fontsize=9, fontweight='bold')
    
    # 添加图例
    legend2 = [
        Patch(facecolor='#2ca02c', alpha=0.8, label='验证通过'),
        Patch(facecolor='#d62728', alpha=0.8, label='验证未通过')
    ]
    ax2.legend(handles=legend2, loc='lower right', fontsize=10)
    
    # 调整布局
    plt.tight_layout()
    
    # 保存
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"✓ 验证对比图已保存: {save_path}")
    
    plt.close()


def plot_scatter_matrix(analyzer, save_path=None, features=None):
    """
    绘制关键特征散点图矩阵
    
    Args:
        analyzer: 分析器实例
        save_path: 保存路径
        features: 要绘制的特征列表（默认选择Top 6）
    """
    print(f"\n生成关键特征散点图矩阵...")
    
    if features is None:
        # 选择Top 6个相关性最强的特征
        features = ['感染率', '存活数', '新报告', '注射吸毒者规模', 
                   '按人数筛查覆盖率', '筛查覆盖率']
    
    # 提取数据
    data_dict = {'风险等级': analyzer.y}
    for feature in features:
        if feature in analyzer.feature_names:
            idx = analyzer.feature_names.index(feature)
            data_dict[feature] = analyzer.X[:, idx]
    
    df = pd.DataFrame(data_dict)
    
    # 创建散点图矩阵
    fig = plt.figure(figsize=(16, 14))
    
    # 使用seaborn的pairplot
    g = sns.pairplot(
        df,
        diag_kind='hist',
        plot_kws={'alpha': 0.6, 's': 30},
        diag_kws={'bins': 20, 'alpha': 0.7}
    )
    
    # 设置标题
    g.fig.suptitle('关键特征散点图矩阵', fontsize=18, fontweight='bold', y=1.01)
    
    # 保存
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"✓ 散点图矩阵已保存: {save_path}")
    
    # 关闭所有图形
    plt.close('all')


def plot_unknown_features_discovery(unknown_results, save_path=None, top_k=15):
    """
    绘制未知特征发现图
    
    Args:
        unknown_results: 未知特征探索结果
        save_path: 保存路径
        top_k: 显示Top K个特征
    """
    print(f"\n生成未知特征发现图 (Top {top_k})...")
    
    # 获取Top K未知特征
    significant_features = unknown_results['significant_features'][:top_k]
    
    # 提取数据
    feature_names = [item['feature'] for item in significant_features]
    pearson_r = [item['pearson_r'] for item in significant_features]
    
    # 反转顺序
    feature_names = feature_names[::-1]
    pearson_r = pearson_r[::-1]
    
    # 创建图表
    fig, ax = plt.subplots(figsize=(12, max(10, top_k * 0.5)))
    
    # 颜色渐变
    colors = plt.cm.RdYlGn_r(np.linspace(0.3, 0.9, len(feature_names)))
    
    # 绘制条形图
    y_pos = np.arange(len(feature_names))
    bars = ax.barh(y_pos, pearson_r, color=colors, alpha=0.8, height=0.7)
    
    # 设置标签
    ax.set_yticks(y_pos)
    ax.set_yticklabels(feature_names, fontsize=11)
    ax.set_xlabel('Pearson相关系数', fontsize=13, fontweight='bold')
    ax.set_title(f'新发现的显著相关特征 (Top {top_k})', 
                fontsize=16, fontweight='bold', pad=20)
    
    # 添加网格
    ax.grid(axis='x', alpha=0.3, linestyle='--', linewidth=0.5)
    ax.set_axisbelow(True)
    
    # 添加零线
    ax.axvline(x=0, color='black', linewidth=1.2)
    
    # 添加数值标签
    for i, (bar, r) in enumerate(zip(bars, pearson_r)):
        width = bar.get_width()
        x_pos = width + (0.02 if width > 0 else -0.02)
        ha = 'left' if width > 0 else 'right'
        ax.text(x_pos, i, f'{r:+.3f}', va='center', ha=ha, fontsize=10, fontweight='bold')
    
    # 调整布局
    plt.subplots_adjust(left=0.25, right=0.95, top=0.94, bottom=0.06)
    
    # 保存
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"✓ 未知特征发现图已保存: {save_path}")
    
    plt.close()


def main():
    """
    生成所有相关性可视化图表
    """
    print("="*80)
    print("  HIV风险因素相关性可视化")
    print("="*80)
    
    # 1. 初始化分析器
    print("\n步骤1: 初始化分析器...")
    analyzer = RiskFactorCorrelationAnalyzer('data/processed/hiv_data_processed.csv')
    
    # 2. 执行相关性分析
    print("\n步骤2: 执行相关性分析...")
    correlation_results = analyzer.analyze_correlations(method='all')
    
    # 3. 验证已知关联
    print("\n步骤3: 验证已知关联...")
    verification_results = analyzer.verify_known_correlations(correlation_results)
    
    # 4. 探索未知特征
    print("\n步骤4: 探索未知特征...")
    unknown_results = analyzer.explore_unknown_features(correlation_results)
    
    # 5. 生成可视化图表
    print("\n步骤5: 生成可视化图表...")
    
    # 5.1 相关性热力图
    plot_correlation_heatmap(
        analyzer,
        correlation_results,
        save_path=os.path.join(OUTPUT_DIR, 'correlation_heatmap.png'),
        top_k=30
    )
    
    # 5.2 Top 20相关特征条形图
    plot_top_correlations_bar(
        analyzer,
        correlation_results,
        save_path=os.path.join(OUTPUT_DIR, 'top_correlations_bar.png'),
        top_k=20
    )
    
    # 5.3 已知关联验证对比图
    plot_known_correlations_verification(
        analyzer,
        verification_results,
        correlation_results,
        save_path=os.path.join(OUTPUT_DIR, 'known_correlations_verification.png')
    )
    
    # 5.4 未知特征发现图
    plot_unknown_features_discovery(
        unknown_results,
        save_path=os.path.join(OUTPUT_DIR, 'unknown_features_discovery.png'),
        top_k=15
    )
    
    # 5.5 散点图矩阵
    plot_scatter_matrix(
        analyzer,
        save_path=os.path.join(OUTPUT_DIR, 'scatter_matrix.png')
    )
    
    print("\n" + "="*80)
    print("✓ 可视化完成")
    print(f"✓ 图表已保存到: {OUTPUT_DIR}/")
    print("="*80)
    
    print("\n生成的图表:")
    print("  1. correlation_heatmap.png - 相关性热力图")
    print("  2. top_correlations_bar.png - Top 20相关特征条形图")
    print("  3. known_correlations_verification.png - 已知关联验证对比图")
    print("  4. unknown_features_discovery.png - 未知特征发现图")
    print("  5. scatter_matrix.png - 关键特征散点图矩阵")


if __name__ == '__main__':
    try:
        main()
    finally:
        # 确保所有matplotlib资源被释放
        plt.close('all')
        # 明确退出
        sys.exit(0)
