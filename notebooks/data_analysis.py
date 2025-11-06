"""
HIV 数据探索性分析
分析处理后的真实数据
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 设置样式
sns.set_style('whitegrid')
sns.set_palette('husl')


def load_processed_data():
    """加载处理后的数据"""
    data_path = Path('data/processed/hiv_data_processed.csv')
    df = pd.read_csv(data_path)
    print(f"✓ 数据加载成功: {df.shape[0]} 个区县, {df.shape[1]} 个特征")
    return df


def analyze_basic_stats(df):
    """基本统计分析"""
    print("\n" + "=" * 70)
    print("📊 基本统计信息")
    print("=" * 70)
    
    # 关键指标统计
    key_metrics = {
        '感染率': df['感染率'],
        '存活数': df['存活数'],
        '治疗覆盖率': df['治疗覆盖率'],
        '病毒抑制比例': df['病毒抑制比例'],
        '风险等级': df['risk_level']
    }
    
    for name, series in key_metrics.items():
        print(f"\n{name}:")
        print(f"  均值: {series.mean():.4f}")
        print(f"  中位数: {series.median():.4f}")
        print(f"  标准差: {series.std():.4f}")
        print(f"  最小值: {series.min():.4f}")
        print(f"  最大值: {series.max():.4f}")


def analyze_age_distribution(df):
    """分析年龄分布"""
    print("\n" + "=" * 70)
    print("👥 年龄分布分析")
    print("=" * 70)
    
    # 存活病例年龄分布
    survival_age_cols = [col for col in df.columns if col.startswith('存活_') and col.endswith('-')]
    survival_age_data = df[survival_age_cols].mean()
    
    # 新报告病例年龄分布
    new_report_age_cols = [col for col in df.columns if col.startswith('新报告_') and col.endswith('-')]
    new_report_age_data = df[new_report_age_cols].mean()
    
    print("\n存活病例年龄分布 (平均百分比):")
    for col, val in survival_age_data.items():
        age_group = col.replace('存活_', '')
        print(f"  {age_group:6s}: {val:6.2f}%")
    
    print("\n新报告病例年龄分布 (平均百分比):")
    for col, val in new_report_age_data.items():
        age_group = col.replace('新报告_', '')
        print(f"  {age_group:6s}: {val:6.2f}%")
    
    return survival_age_data, new_report_age_data


def analyze_transmission_routes(df):
    """分析传播途径"""
    print("\n" + "=" * 70)
    print("🔗 传播途径分析")
    print("=" * 70)
    
    # 存活病例传播途径
    survival_transmission_cols = [
        '存活_同性传播', '存活_配偶阳性', '存活_商业性行为', 
        '存活_非婚非商业', '存活_非婚未分类', '存活_注射毒品', 
        '存活_母婴传播', '存活_其他或不详'
    ]
    
    # 新报告病例传播途径
    new_report_transmission_cols = [
        '新报告_同性传播', '新报告_配偶阳性', '新报告_商业性行为',
        '新报告_非婚非商业', '新报告_非婚未分类', '新报告_注射毒品',
        '新报告_母婴传播', '新报告_其他或不详'
    ]
    
    print("\n存活病例传播途径 (平均百分比):")
    for col in survival_transmission_cols:
        route = col.replace('存活_', '')
        val = df[col].mean()
        print(f"  {route:12s}: {val:6.2f}%")
    
    print("\n新报告病例传播途径 (平均百分比):")
    for col in new_report_transmission_cols:
        route = col.replace('新报告_', '')
        val = df[col].mean()
        print(f"  {route:12s}: {val:6.2f}%")
    
    return df[survival_transmission_cols].mean(), df[new_report_transmission_cols].mean()


def analyze_intervention_coverage(df):
    """分析干预覆盖情况"""
    print("\n" + "=" * 70)
    print("🎯 重点人群干预覆盖分析")
    print("=" * 70)
    
    # 各重点人群的干预覆盖率
    intervention_groups = {
        '暗娼': 'fsw',
        'MSM': 'msm',
        '吸毒者': 'drug_user',
        '外来务工': 'migrant',
        '其他人群': 'other'
    }
    
    # 映射到实际列名
    coverage_mapping = {
        '暗娼': '暗娼_月均覆盖率',
        'MSM': 'MSM_月均覆盖率',
        '吸毒者': '吸毒者_月均覆盖率',
        '外来务工': '外来务工_月均覆盖率',
        '其他人群': '其他人群_月均覆盖率'
    }
    
    print("\n各人群干预覆盖率:")
    for group_name, col_name in coverage_mapping.items():
        if col_name in df.columns:
            coverage = df[col_name].mean()
            print(f"  {group_name:8s}: {coverage:6.2f}%")


def analyze_risk_levels(df):
    """分析风险等级分布"""
    print("\n" + "=" * 70)
    print("⚠️  风险等级分布")
    print("=" * 70)
    
    risk_dist = df['risk_level'].value_counts().sort_index()
    
    print("\n风险等级分布:")
    for level, count in risk_dist.items():
        pct = count / len(df) * 100
        print(f"  等级 {level}: {count:3d} 个区县 ({pct:5.1f}%)")
    
    # 各风险等级的关键指标
    print("\n各风险等级的关键指标:")
    for level in sorted(df['risk_level'].unique()):
        level_data = df[df['risk_level'] == level]
        print(f"\n  等级 {level} ({len(level_data)} 个区县):")
        print(f"    平均感染率: {level_data['感染率'].mean():.4f}")
        print(f"    平均存活数: {level_data['存活数'].mean():.0f}")
        print(f"    平均治疗覆盖率: {level_data['治疗覆盖率'].mean():.2f}%")


def create_visualizations(df):
    """创建可视化图表"""
    print("\n" + "=" * 70)
    print("📈 生成可视化图表")
    print("=" * 70)
    
    # 创建输出目录
    output_dir = Path('outputs/figures')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. 风险等级分布
    plt.figure(figsize=(10, 6))
    risk_counts = df['risk_level'].value_counts().sort_index()
    plt.bar(risk_counts.index, risk_counts.values, color='steelblue', alpha=0.7)
    plt.xlabel('风险等级', fontsize=12)
    plt.ylabel('区县数量', fontsize=12)
    plt.title('HIV 风险等级分布', fontsize=14, fontweight='bold')
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / 'risk_level_distribution.png', dpi=300, bbox_inches='tight')
    print(f"  ✓ 保存: risk_level_distribution.png")
    plt.close()
    
    # 2. 感染率分布
    plt.figure(figsize=(10, 6))
    plt.hist(df['感染率'], bins=30, color='coral', alpha=0.7, edgecolor='black')
    plt.xlabel('感染率', fontsize=12)
    plt.ylabel('区县数量', fontsize=12)
    plt.title('HIV 感染率分布', fontsize=14, fontweight='bold')
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / 'infection_rate_distribution.png', dpi=300, bbox_inches='tight')
    print(f"  ✓ 保存: infection_rate_distribution.png")
    plt.close()
    
    # 3. 年龄分布对比
    survival_age_cols = [col for col in df.columns if col.startswith('存活_') and col.endswith('-')]
    new_report_age_cols = [col for col in df.columns if col.startswith('新报告_') and col.endswith('-')]
    
    age_labels = [col.replace('存活_', '').replace('-', '') for col in survival_age_cols]
    survival_age_means = df[survival_age_cols].mean().values
    new_report_age_means = df[new_report_age_cols].mean().values
    
    x = np.arange(len(age_labels))
    width = 0.35
    
    plt.figure(figsize=(14, 6))
    plt.bar(x - width/2, survival_age_means, width, label='存活病例', color='skyblue', alpha=0.8)
    plt.bar(x + width/2, new_report_age_means, width, label='新报告病例', color='lightcoral', alpha=0.8)
    plt.xlabel('年龄组', fontsize=12)
    plt.ylabel('平均百分比 (%)', fontsize=12)
    plt.title('HIV 病例年龄分布对比', fontsize=14, fontweight='bold')
    plt.xticks(x, age_labels, rotation=45)
    plt.legend()
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / 'age_distribution_comparison.png', dpi=300, bbox_inches='tight')
    print(f"  ✓ 保存: age_distribution_comparison.png")
    plt.close()
    
    # 4. 传播途径对比
    survival_transmission_cols = [
        '存活_同性传播', '存活_配偶阳性', '存活_商业性行为', 
        '存活_非婚非商业', '存活_注射毒品', '存活_母婴传播'
    ]
    new_report_transmission_cols = [
        '新报告_同性传播', '新报告_配偶阳性', '新报告_商业性行为',
        '新报告_非婚非商业', '新报告_注射毒品', '新报告_母婴传播'
    ]
    
    transmission_labels = [col.replace('存活_', '') for col in survival_transmission_cols]
    survival_transmission_means = df[survival_transmission_cols].mean().values
    new_report_transmission_means = df[new_report_transmission_cols].mean().values
    
    x = np.arange(len(transmission_labels))
    
    plt.figure(figsize=(12, 6))
    plt.bar(x - width/2, survival_transmission_means, width, label='存活病例', color='mediumseagreen', alpha=0.8)
    plt.bar(x + width/2, new_report_transmission_means, width, label='新报告病例', color='orange', alpha=0.8)
    plt.xlabel('传播途径', fontsize=12)
    plt.ylabel('平均百分比 (%)', fontsize=12)
    plt.title('HIV 传播途径分布对比', fontsize=14, fontweight='bold')
    plt.xticks(x, transmission_labels, rotation=45, ha='right')
    plt.legend()
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / 'transmission_routes_comparison.png', dpi=300, bbox_inches='tight')
    print(f"  ✓ 保存: transmission_routes_comparison.png")
    plt.close()
    
    # 5. 关键指标相关性热图
    key_features = [
        '感染率', '存活数', '治疗覆盖率', '病毒抑制比例',
        '暗娼_月均覆盖率', 'MSM_月均覆盖率', '筛查覆盖率'
    ]
    
    corr_matrix = df[key_features].corr()
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', 
                center=0, square=True, linewidths=1, cbar_kws={"shrink": 0.8})
    plt.title('关键指标相关性热图', fontsize=14, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig(output_dir / 'correlation_heatmap.png', dpi=300, bbox_inches='tight')
    print(f"  ✓ 保存: correlation_heatmap.png")
    plt.close()
    
    print(f"\n✓ 所有图表已保存到: {output_dir}")


def generate_summary_report(df):
    """生成数据摘要报告"""
    print("\n" + "=" * 70)
    print("📝 生成数据摘要报告")
    print("=" * 70)
    
    report_path = Path('outputs/data_analysis_report.txt')
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("HIV 数据分析报告\n")
        f.write("=" * 70 + "\n\n")
        
        f.write(f"数据概况:\n")
        f.write(f"  区县数量: {len(df)}\n")
        f.write(f"  特征数量: {len(df.columns)}\n\n")
        
        f.write(f"关键指标统计:\n")
        f.write(f"  平均感染率: {df['感染率'].mean():.4f}\n")
        f.write(f"  平均存活数: {df['存活数'].mean():.0f}\n")
        f.write(f"  平均治疗覆盖率: {df['治疗覆盖率'].mean():.2f}%\n")
        f.write(f"  平均病毒抑制比例: {df['病毒抑制比例'].mean():.2f}%\n\n")
        
        f.write(f"风险等级分布:\n")
        for level in sorted(df['risk_level'].unique()):
            count = (df['risk_level'] == level).sum()
            pct = count / len(df) * 100
            f.write(f"  等级 {level}: {count:3d} 个区县 ({pct:5.1f}%)\n")
    
    print(f"✓ 报告已保存: {report_path}")


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("🔬 HIV 数据探索性分析")
    print("=" * 70)
    
    # 加载数据
    df = load_processed_data()
    
    # 基本统计分析
    analyze_basic_stats(df)
    
    # 年龄分布分析
    analyze_age_distribution(df)
    
    # 传播途径分析
    analyze_transmission_routes(df)
    
    # 干预覆盖分析
    analyze_intervention_coverage(df)
    
    # 风险等级分析
    analyze_risk_levels(df)
    
    # 创建可视化
    create_visualizations(df)
    
    # 生成摘要报告
    generate_summary_report(df)
    
    print("\n" + "=" * 70)
    print("✅ 数据分析完成！")
    print("=" * 70)
    print("\n下一步:")
    print("1. 查看可视化图表: outputs/figures/")
    print("2. 查看分析报告: outputs/data_analysis_report.txt")
    print("3. 开始特征工程和模型训练")


if __name__ == '__main__':
    main()
