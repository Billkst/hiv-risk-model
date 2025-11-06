"""
特征贡献度可视化工具
生成SHAP瀑布图、特征重要性条形图等
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 非交互式后端
import os
from models.predictor import HIVRiskPredictor
from models.feature_contribution_fast import FastFeatureContributionAnalyzer

# 设置中文字体
import matplotlib.font_manager as fm
from pathlib import Path

# 尝试加载用户目录的中文字体
user_font_path = Path.home() / '.fonts' / 'SourceHanSansSC.otf'
font_to_use = 'DejaVu Sans'  # 默认

if user_font_path.exists():
    try:
        # 添加字体到matplotlib
        fm.fontManager.addfont(str(user_font_path))
        font_to_use = 'Source Han Sans SC'
        print(f"✓ 使用中文字体: {font_to_use}")
    except Exception as e:
        print(f"⚠️  加载中文字体失败: {e}")
        print(f"  使用默认字体: {font_to_use}")
else:
    # 尝试查找系统中文字体
    available_fonts = [f.name for f in fm.fontManager.ttflist]
    chinese_fonts = ['SimHei', 'WenQuanYi Micro Hei', 'WenQuanYi Zen Hei', 
                    'Noto Sans CJK SC', 'Noto Sans CJK TC', 'Source Han Sans SC',
                    'AR PL UMing CN', 'AR PL UKai CN', 'Microsoft YaHei', 'STHeiti', 'STSong']
    
    for font in chinese_fonts:
        if font in available_fonts:
            font_to_use = font
            print(f"✓ 使用系统字体: {font_to_use}")
            break
    else:
        print(f"⚠️  未找到中文字体，使用默认字体: {font_to_use}")
        print(f"  提示: 图表中的中文可能显示为方框")

plt.rcParams['font.sans-serif'] = [font_to_use, 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# 输出目录
OUTPUT_DIR = 'outputs/visualizations'
os.makedirs(OUTPUT_DIR, exist_ok=True)


def plot_feature_contributions_waterfall(result, save_path=None, top_k=15):
    """
    绘制特征贡献度瀑布图
    
    Args:
        result: predict_single() 返回的结果（含feature_contributions）
        save_path: 保存路径
        top_k: 显示Top K个特征
    """
    if 'feature_contributions' not in result:
        print("⚠️  结果中不包含特征贡献度")
        return
    
    contrib = result['feature_contributions']
    
    # 获取所有特征贡献度
    all_contribs = contrib.get('all_contributions', [])
    feature_names = contrib.get('feature_names', [])
    
    if not all_contribs or not feature_names:
        print("⚠️  特征贡献度数据不完整")
        return
    
    # 创建特征-贡献度对
    feature_contrib_pairs = [
        (feature_names[i], all_contribs[i]) 
        for i in range(len(all_contribs))
    ]
    
    # 按绝对值排序，取Top K
    sorted_pairs = sorted(feature_contrib_pairs, 
                         key=lambda x: abs(x[1]), 
                         reverse=True)[:top_k]
    
    # 分离特征名和贡献度
    features = [p[0] for p in sorted_pairs]
    contributions = [p[1] for p in sorted_pairs]
    
    # 优化特征名称显示：智能截断长名称
    display_features = []
    for feature in features:
        if len(feature) > 20:
            # 如果包含下划线，尝试保留关键部分
            if '_' in feature:
                parts = feature.split('_')
                if len(parts) == 2:
                    # 保留前缀和后缀的关键部分
                    display_features.append(f"{parts[0][:8]}_{parts[1][:8]}")
                else:
                    display_features.append(feature[:18] + '..')
            else:
                display_features.append(feature[:18] + '..')
        else:
            display_features.append(feature)
    
    # 动态计算图表高度：每个特征至少0.6英寸高度，确保不重叠
    fig_height = max(12, len(features) * 0.6)
    fig_width = 16
    
    # 创建图表
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    
    # 颜色：正贡献红色，负贡献蓝色
    colors = ['#d62728' if c > 0 else '#1f77b4' for c in contributions]
    
    # 绘制条形图，使用更小的条形高度避免重叠
    y_pos = np.arange(len(features)) * 1.2  # 增加间距
    ax.barh(y_pos, contributions, color=colors, alpha=0.75, height=0.5)
    
    # 设置标签，使用更大的字体和间距
    ax.set_yticks(y_pos)
    ax.set_yticklabels(display_features, fontsize=12)
    ax.set_xlabel('特征贡献度', fontsize=13, fontweight='bold')
    ax.set_title(f'特征贡献度分析 (Top {top_k})\n风险等级: {result["risk_level_5"]} - {result["risk_description"]}', 
                fontsize=15, fontweight='bold', pad=20)
    
    # 设置y轴范围，确保有足够空间
    ax.set_ylim(-0.5, y_pos[-1] + 0.5)
    
    # 添加网格
    ax.grid(axis='x', alpha=0.3, linestyle='--', linewidth=0.5)
    ax.set_axisbelow(True)
    
    # 添加零线
    ax.axvline(x=0, color='black', linewidth=1.0)
    
    # 添加数值标签
    for i, (feature, contrib) in enumerate(zip(features, contributions)):
        x_pos = contrib + (0.015 if contrib > 0 else -0.015)
        ha = 'left' if contrib > 0 else 'right'
        ax.text(x_pos, i, f'{contrib:+.3f}', 
               va='center', ha=ha, fontsize=10, fontweight='bold')
    
    # 添加图例
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#d62728', alpha=0.75, label='正贡献（增加风险）'),
        Patch(facecolor='#1f77b4', alpha=0.75, label='负贡献（降低风险）')
    ]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=11, 
             framealpha=0.9, edgecolor='gray')
    
    # 调整布局：给y轴标签更多空间
    plt.subplots_adjust(left=0.20, right=0.95, top=0.94, bottom=0.06)
    
    # 设置y轴刻度参数，增加间距避免重叠
    ax.tick_params(axis='y', which='major', pad=12, labelsize=12, length=0)
    ax.tick_params(axis='x', which='major', labelsize=10)
    
    # 反转y轴，让最重要的特征在上面
    ax.invert_yaxis()
    
    # 保存
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✓ 瀑布图已保存: {save_path}")
    
    plt.close()


def plot_global_importance(importance_list, save_path=None, top_k=20):
    """
    绘制全局特征重要性条形图
    
    Args:
        importance_list: get_feature_importance() 返回的结果
        save_path: 保存路径
        top_k: 显示Top K个特征
    """
    if not importance_list:
        print("⚠️  特征重要性数据为空")
        return
    
    # 取Top K
    top_features = importance_list[:top_k]
    
    # 提取数据
    features = [f['feature'] for f in top_features]
    importances = [f['importance'] for f in top_features]
    percentages = [f['importance_normalized'] for f in top_features]
    
    # 创建图表
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # 颜色渐变
    colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(features)))
    
    # 绘制水平条形图
    y_pos = np.arange(len(features))
    bars = ax.barh(y_pos, importances, color=colors, alpha=0.8)
    
    # 设置标签
    ax.set_yticks(y_pos)
    ax.set_yticklabels(features, fontsize=10)
    ax.set_xlabel('特征重要性分数', fontsize=12)
    ax.set_title(f'全局特征重要性排名 (Top {top_k})', 
                fontsize=14, fontweight='bold')
    
    # 反转y轴（重要性高的在上）
    ax.invert_yaxis()
    
    # 添加网格
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    
    # 添加数值标签
    for i, (bar, importance, pct) in enumerate(zip(bars, importances, percentages)):
        width = bar.get_width()
        ax.text(width + 0.002, bar.get_y() + bar.get_height()/2,
               f'{importance:.4f} ({pct:.2f}%)',
               va='center', ha='left', fontsize=9)
    
    # 调整布局
    plt.tight_layout()
    
    # 保存
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✓ 特征重要性图已保存: {save_path}")
    
    plt.close()


def plot_top_contributions_comparison(result, save_path=None):
    """
    绘制Top正负贡献特征对比图
    
    Args:
        result: predict_single() 返回的结果（含feature_contributions）
        save_path: 保存路径
    """
    if 'feature_contributions' not in result:
        print("⚠️  结果中不包含特征贡献度")
        return
    
    contrib = result['feature_contributions']
    top_positive = contrib.get('top_positive', [])
    top_negative = contrib.get('top_negative', [])
    
    # 创建图表
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # 左图：正贡献（增加风险）
    if top_positive:
        features_pos = [f['feature'] for f in top_positive[:5]]
        contribs_pos = [f['contribution'] for f in top_positive[:5]]
        
        y_pos = np.arange(len(features_pos))
        ax1.barh(y_pos, contribs_pos, color='#d62728', alpha=0.7)
        ax1.set_yticks(y_pos)
        ax1.set_yticklabels(features_pos, fontsize=10)
        ax1.set_xlabel('贡献度', fontsize=11)
        ax1.set_title('Top 5 正贡献特征\n（增加风险的因素）', 
                     fontsize=12, fontweight='bold', color='#d62728')
        ax1.invert_yaxis()
        ax1.grid(axis='x', alpha=0.3, linestyle='--')
        
        # 添加数值标签
        for i, contrib in enumerate(contribs_pos):
            ax1.text(contrib + 0.01, i, f'+{contrib:.3f}',
                    va='center', ha='left', fontsize=9)
    else:
        ax1.text(0.5, 0.5, '无正贡献特征', 
                ha='center', va='center', fontsize=12)
        ax1.set_xlim(0, 1)
        ax1.set_ylim(0, 1)
    
    # 右图：负贡献（降低风险）
    if top_negative:
        features_neg = [f['feature'] for f in top_negative[:5]]
        contribs_neg = [f['contribution'] for f in top_negative[:5]]
        
        y_pos = np.arange(len(features_neg))
        ax2.barh(y_pos, contribs_neg, color='#1f77b4', alpha=0.7)
        ax2.set_yticks(y_pos)
        ax2.set_yticklabels(features_neg, fontsize=10)
        ax2.set_xlabel('贡献度', fontsize=11)
        ax2.set_title('Top 5 负贡献特征\n（降低风险的因素）', 
                     fontsize=12, fontweight='bold', color='#1f77b4')
        ax2.invert_yaxis()
        ax2.grid(axis='x', alpha=0.3, linestyle='--')
        
        # 添加数值标签
        for i, contrib in enumerate(contribs_neg):
            ax2.text(contrib - 0.01, i, f'{contrib:.3f}',
                    va='center', ha='right', fontsize=9)
    else:
        ax2.text(0.5, 0.5, '无负贡献特征', 
                ha='center', va='center', fontsize=12)
        ax2.set_xlim(0, 1)
        ax2.set_ylim(0, 1)
    
    # 总标题
    fig.suptitle(f'特征贡献度对比分析\n风险等级: {result["risk_level_5"]} - {result["risk_description"]} (分数: {result["risk_score"]:.2f})',
                fontsize=14, fontweight='bold', y=1.02)
    
    # 调整布局
    plt.tight_layout()
    
    # 保存
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✓ 对比图已保存: {save_path}")
    
    plt.close()


def demo():
    """演示可视化功能"""
    print("\n" + "="*80)
    print("特征贡献度可视化演示")
    print("="*80)
    
    # 加载预测器
    print("\n1. 加载模型...")
    predictor = HIVRiskPredictor(enable_contributions=True)
    
    # 准备测试样本
    print("\n2. 准备测试样本...")
    sample_features = {col: 0 for col in predictor.feature_columns}
    sample_features.update({
        '存活数': 1200,
        '新报告': 80,
        '感染率': 0.12,
        '治疗覆盖率': 92.0,
        '病毒抑制比例': 88.0,
        '筛查人数': 120000,
        '暗娼规模': 800,
        '城市MSM规模': 1500
    })
    
    # 预测（含特征贡献度）
    print("\n3. 进行预测...")
    result = predictor.predict_single(sample_features, include_contributions=True)
    
    print(f"  风险等级: {result['risk_level_5']} - {result['risk_description']}")
    print(f"  风险分数: {result['risk_score']:.2f}")
    print(f"  置信度: {result['confidence_percent']}")
    
    # 生成可视化
    print("\n4. 生成可视化图表...")
    
    # 图1: 特征贡献度瀑布图
    plot_feature_contributions_waterfall(
        result,
        save_path=f'{OUTPUT_DIR}/contributions_waterfall.png',
        top_k=15
    )
    
    # 图2: Top正负贡献对比
    plot_top_contributions_comparison(
        result,
        save_path=f'{OUTPUT_DIR}/contributions_comparison.png'
    )
    
    # 图3: 全局特征重要性
    print("\n5. 生成全局特征重要性图...")
    importance = predictor.get_feature_importance(top_k=20)
    if importance:
        plot_global_importance(
            importance,
            save_path=f'{OUTPUT_DIR}/global_importance.png',
            top_k=20
        )
    
    print("\n" + "="*80)
    print("✓ 可视化演示完成")
    print(f"✓ 图表已保存到: {OUTPUT_DIR}/")
    print("="*80)
    
    print("\n生成的图表:")
    print(f"  1. {OUTPUT_DIR}/contributions_waterfall.png - 特征贡献度瀑布图")
    print(f"  2. {OUTPUT_DIR}/contributions_comparison.png - Top正负贡献对比图")
    print(f"  3. {OUTPUT_DIR}/global_importance.png - 全局特征重要性图")


if __name__ == '__main__':
    try:
        demo()
    finally:
        import matplotlib.pyplot as plt
        import sys
        plt.close('all')
        sys.exit(0)
