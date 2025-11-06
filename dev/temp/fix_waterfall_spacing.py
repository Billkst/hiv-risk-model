#!/usr/bin/env python3
"""
修复瀑布图字体重叠问题 - 终极版本
使用更大的间距和更清晰的布局
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from pathlib import Path
from models.predictor import HIVRiskPredictor

# 加载中文字体
user_font_path = Path.home() / '.fonts' / 'SourceHanSansSC.otf'
if user_font_path.exists():
    fm.fontManager.addfont(str(user_font_path))
    plt.rcParams['font.sans-serif'] = ['Source Han Sans SC', 'DejaVu Sans']
    print(f"✓ 使用字体: Source Han Sans SC")
else:
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
    print(f"⚠️  使用默认字体")

plt.rcParams['axes.unicode_minus'] = False

def create_spaced_waterfall(result, save_path, top_k=15):
    """
    创建间距优化的瀑布图 - 彻底解决重叠问题
    """
    if 'feature_contributions' not in result:
        print("⚠️  结果中不包含特征贡献度")
        return
    
    contrib = result['feature_contributions']
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
    
    # 优化特征名称显示
    display_features = []
    for feature in features:
        if len(feature) > 18:
            if '_' in feature:
                parts = feature.split('_')
                if len(parts) == 2:
                    display_features.append(f"{parts[0][:8]}_{parts[1][:7]}")
                else:
                    display_features.append(feature[:16] + '..')
            else:
                display_features.append(feature[:16] + '..')
        else:
            display_features.append(feature)
    
    # 计算图表尺寸：每个特征0.7英寸高度
    fig_height = max(14, len(features) * 0.7)
    fig_width = 16
    
    print(f"  图表尺寸: {fig_width} x {fig_height} 英寸")
    print(f"  特征数量: {len(features)}")
    
    # 创建图表
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    
    # 颜色
    colors = ['#d62728' if c > 0 else '#1f77b4' for c in contributions]
    
    # 使用更大的间距：每个特征之间间隔1.5单位
    y_positions = np.arange(len(features)) * 1.5
    
    # 绘制条形图，条形高度0.4
    bars = ax.barh(y_positions, contributions, color=colors, alpha=0.8, height=0.4)
    
    # 设置y轴
    ax.set_yticks(y_positions)
    ax.set_yticklabels(display_features, fontsize=13)
    
    # 设置x轴
    ax.set_xlabel('特征贡献度', fontsize=14, fontweight='bold')
    
    # 标题
    title = f'特征贡献度分析 (Top {top_k})\\n'
    title += f'风险等级: {result["risk_level_5"]} - {result["risk_description"]}'
    ax.set_title(title, fontsize=16, fontweight='bold', pad=25)
    
    # 网格
    ax.grid(axis='x', alpha=0.3, linestyle='--', linewidth=0.5)
    ax.set_axisbelow(True)
    
    # 零线
    ax.axvline(x=0, color='black', linewidth=1.2)
    
    # 数值标签
    for i, (bar, contrib) in enumerate(zip(bars, contributions)):
        width = bar.get_width()
        x_pos = width + (0.02 if width > 0 else -0.02)
        ha = 'left' if width > 0 else 'right'
        
        ax.text(x_pos, y_positions[i], f'{contrib:+.3f}', 
               va='center', ha=ha, fontsize=11, fontweight='bold')
    
    # 图例
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#d62728', alpha=0.8, label='正贡献（增加风险）'),
        Patch(facecolor='#1f77b4', alpha=0.8, label='负贡献（降低风险）')
    ]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=12, 
             framealpha=0.95, edgecolor='gray')
    
    # 设置y轴范围
    ax.set_ylim(-1, y_positions[-1] + 1)
    
    # 调整布局
    plt.subplots_adjust(left=0.18, right=0.95, top=0.94, bottom=0.06)
    
    # y轴刻度参数 - 关键：增加pad避免重叠
    ax.tick_params(axis='y', which='major', pad=15, labelsize=13, length=0)
    ax.tick_params(axis='x', which='major', labelsize=11)
    
    # 反转y轴
    ax.invert_yaxis()
    
    # 保存
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        print(f"✓ 优化瀑布图已保存: {save_path}")
    
    plt.close()

def main():
    print("\\n" + "="*70)
    print("修复瀑布图字体重叠问题")
    print("="*70)
    
    # 加载预测器
    print("\\n1. 加载模型...")
    predictor = HIVRiskPredictor(enable_contributions=True)
    
    # 准备测试样本
    print("\\n2. 准备测试样本...")
    sample_features = {col: 0 for col in predictor.feature_columns}
    sample_features.update({
        '存活数': 1200,
        '新报告': 80,
        '感染率': 0.12,
        '治疗覆盖率': 92.0,
        '病毒抑制比例': 88.0,
        '筛查人数': 120000,
        '暗娼规模': 800,
        '城市MSM规模': 1500,
        '按人数筛查覆盖率': 25.0
    })
    
    # 预测
    print("\\n3. 进行预测...")
    result = predictor.predict_single(sample_features, include_contributions=True)
    
    print(f"  风险等级: {result['risk_level_5']} - {result['risk_description']}")
    print(f"  风险分数: {result['risk_score']:.2f}")
    
    # 生成优化的瀑布图
    print("\\n4. 生成间距优化瀑布图...")
    create_spaced_waterfall(
        result,
        save_path='outputs/visualizations/waterfall_fixed.png',
        top_k=15
    )
    
    print("\\n" + "="*70)
    print("✓ 修复完成！")
    print("请查看: outputs/visualizations/waterfall_fixed.png")
    print("="*70)

if __name__ == '__main__':
    main()
