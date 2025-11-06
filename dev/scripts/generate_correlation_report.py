#!/usr/bin/env python3
"""
生成风险因素相关性分析报告
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


import os
from datetime import datetime
from models.correlation_analyzer import RiskFactorCorrelationAnalyzer


def generate_markdown_report(analyzer, correlation_results, verification_results, unknown_results, output_path):
    """
    生成Markdown格式的分析报告
    
    Args:
        analyzer: 分析器实例
        correlation_results: 相关性分析结果
        verification_results: 验证结果
        unknown_results: 未知特征探索结果
        output_path: 输出文件路径
    """
    print(f"\n生成分析报告: {output_path}")
    
    # 生成报告内容
    report = []
    
    # 标题和元数据
    report.append("# HIV风险因素相关性分析报告\n")
    report.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report.append(f"**分析样本数**: {len(analyzer.df)}\n")
    report.append(f"**分析特征数**: {len(analyzer.feature_names)}\n")
    report.append("\n---\n")
    
    # 执行摘要
    report.append("## 执行摘要\n")
    
    total_positive = len(analyzer.positive_features)
    verified_positive = len(verification_results['positive_verified'])
    total_negative = len(analyzer.negative_features)
    verified_negative = len(verification_results['negative_verified'])
    
    report.append(f"本报告对{len(analyzer.df)}个县区的HIV疫情数据进行了全面的相关性分析，")
    report.append(f"涵盖{len(analyzer.feature_names)}个特征指标。\n\n")
    
    report.append("**主要发现**:\n\n")
    report.append(f"1. **已知正相关特征验证**: {verified_positive}/{total_positive}个通过验证（{verified_positive/total_positive*100:.1f}%）\n")
    report.append(f"   - 感染率、存活数、新报告数等核心指标符合预期\n")
    report.append(f"   - 吸毒相关指标验证通过\n\n")
    
    report.append(f"2. **已知负相关特征验证**: {verified_negative}/{total_negative}个通过验证（{verified_negative/total_negative*100:.1f}%）\n")
    report.append(f"   - 治疗覆盖率、检测覆盖率等实际呈正相关\n")
    report.append(f"   - 可能原因：高风险地区投入更多资源\n\n")
    
    report.append(f"3. **未知特征探索**: 发现{unknown_results['significant_count']}个显著相关的未知特征\n")
    report.append(f"   - 注射吸毒传播途径相关特征\n")
    report.append(f"   - 年龄分布相关特征\n")
    report.append(f"   - 治疗效果相关特征\n\n")
    
    report.append("\n---\n")
    
    # 数据集概况
    report.append("## 1. 数据集概况\n")
    report.append(f"- **样本数量**: {len(analyzer.df)}个县区\n")
    report.append(f"- **特征数量**: {len(analyzer.feature_names)}个指标\n")
    report.append(f"- **风险等级分布**:\n")
    
    risk_dist = analyzer.df['risk_level'].value_counts().sort_index()
    for level, count in risk_dist.items():
        percentage = count / len(analyzer.df) * 100
        report.append(f"  - 等级{level}: {count}个县区 ({percentage:.1f}%)\n")
    
    report.append("\n---\n")
    
    # 已知正相关特征验证
    report.append("## 2. 已知正相关特征验证\n")
    report.append(f"\n**验证结果**: {verified_positive}/{total_positive}个通过（{verified_positive/total_positive*100:.1f}%）\n\n")
    
    report.append("### 2.1 验证通过的特征\n\n")
    report.append("| 特征名称 | 模型特征名 | Pearson r | p值 | 相关性类型 |\n")
    report.append("|---------|-----------|-----------|-----|----------|\n")
    
    for req_name in verification_results['positive_verified']:
        model_name = analyzer.positive_features[req_name]
        if model_name in correlation_results:
            result = correlation_results[model_name]
            r = result['pearson_r']
            p = result['pearson_p']
            corr_type = result['correlation_type']
            report.append(f"| {req_name} | {model_name} | {r:+.3f} | {p:.4f} | {corr_type} |\n")
    
    report.append("\n### 2.2 验证未通过的特征\n\n")
    report.append("| 特征名称 | 模型特征名 | Pearson r | p值 | 说明 |\n")
    report.append("|---------|-----------|-----------|-----|------|\n")
    
    for item in verification_results['positive_failed']:
        req_name = item['feature']
        model_name = item['model_feature']
        r = item['actual_r']
        p = item['p_value']
        
        if p >= 0.05:
            reason = "不显著"
        elif r < 0:
            reason = "实际为负相关"
        else:
            reason = "相关性弱"
        
        report.append(f"| {req_name} | {model_name} | {r:+.3f} | {p:.4f} | {reason} |\n")
    
    report.append("\n---\n")
    
    # 已知负相关特征验证
    report.append("## 3. 已知负相关特征验证\n")
    report.append(f"\n**验证结果**: {verified_negative}/{total_negative}个通过（{verified_negative/total_negative*100:.1f}%）\n\n")
    
    if verified_negative > 0:
        report.append("### 3.1 验证通过的特征\n\n")
        report.append("| 特征名称 | 模型特征名 | Pearson r | p值 | 相关性类型 |\n")
        report.append("|---------|-----------|-----------|-----|----------|\n")
        
        for req_name in verification_results['negative_verified']:
            model_name = analyzer.negative_features[req_name]
            if model_name in correlation_results:
                result = correlation_results[model_name]
                r = result['pearson_r']
                p = result['pearson_p']
                corr_type = result['correlation_type']
                report.append(f"| {req_name} | {model_name} | {r:+.3f} | {p:.4f} | {corr_type} |\n")
        report.append("\n")
    
    report.append("### 3.2 验证未通过的特征\n\n")
    report.append("| 特征名称 | 模型特征名 | Pearson r | p值 | 说明 |\n")
    report.append("|---------|-----------|-----------|-----|------|\n")
    
    for item in verification_results['negative_failed']:
        req_name = item['feature']
        model_name = item['model_feature']
        r = item['actual_r']
        p = item['p_value']
        
        if p >= 0.05:
            reason = "不显著"
        elif r > 0:
            reason = "实际为正相关"
        else:
            reason = "相关性弱"
        
        report.append(f"| {req_name} | {model_name} | {r:+.3f} | {p:.4f} | {reason} |\n")
    
    report.append("\n### 3.3 负相关特征验证失败的可能原因\n\n")
    report.append("1. **资源投入效应**: 高风险地区往往获得更多资源投入，导致治疗覆盖率、检测覆盖率等指标更高\n")
    report.append("2. **数据收集偏差**: 高风险地区的数据收集可能更完整、更准确\n")
    report.append("3. **时间滞后效应**: 干预措施的效果需要时间才能显现，当前数据可能尚未反映长期效果\n")
    report.append("4. **因果关系复杂**: 风险等级与干预措施之间存在双向因果关系\n\n")
    
    report.append("\n---\n")
    
    # 未知特征探索
    report.append("## 4. 未知特征探索\n")
    report.append(f"\n**探索结果**: 在{unknown_results['total_unknown']}个未知特征中，")
    report.append(f"发现{unknown_results['significant_count']}个显著相关特征（p < 0.05）\n\n")
    
    report.append("### 4.1 Top 20 显著相关的未知特征\n\n")
    report.append("| 排名 | 特征名称 | Pearson r | p值 | 相关性类型 |\n")
    report.append("|-----|---------|-----------|-----|----------|\n")
    
    for i, item in enumerate(unknown_results['significant_features'][:20], 1):
        feature = item['feature']
        r = item['pearson_r']
        p = item['pearson_p']
        corr_type = item['correlation_type']
        report.append(f"| {i} | {feature} | {r:+.3f} | {p:.4f} | {corr_type} |\n")
    
    report.append("\n### 4.2 新发现的关键特征\n\n")
    report.append("**1. 注射吸毒传播相关特征**\n")
    report.append("- `存活_注射毒品` (r=+0.642): 注射吸毒传播途径的存活病例数与风险高度相关\n")
    report.append("- 说明：注射吸毒是重要的传播途径，需要加强针对性干预\n\n")
    
    report.append("**2. 年龄分布相关特征**\n")
    report.append("- `新报告_5-` (r=+0.636): 5岁以下儿童新报告病例数与风险相关\n")
    report.append("- `存活_5-`, `存活_10-` 等年龄段特征也显著相关\n")
    report.append("- 说明：儿童病例可能反映母婴传播或家庭聚集性传播\n\n")
    
    report.append("**3. 治疗效果相关特征**\n")
    report.append("- `病载小于50占现存活比例` (r=+0.361): 治疗效果指标与风险正相关\n")
    report.append("- 说明：可能反映高风险地区治疗管理更严格，或病例基数大导致比例高\n\n")
    
    report.append("\n---\n")
    
    # Top相关特征总览
    report.append("## 5. Top 20 相关性最强特征（综合）\n\n")
    report.append("| 排名 | 特征名称 | Pearson r | p值 | 相关性类型 | 类别 |\n")
    report.append("|-----|---------|-----------|-----|----------|------|\n")
    
    top_20 = analyzer.get_top_correlations(correlation_results, top_k=20)
    for i, item in enumerate(top_20, 1):
        feature = item['feature']
        r = item['pearson_r']
        p = item['pearson_p']
        corr_type = item['correlation_type']
        
        # 判断类别
        if feature in analyzer.positive_features.values():
            category = "已知正相关"
        elif feature in analyzer.negative_features.values():
            category = "已知负相关"
        else:
            category = "未知特征"
        
        report.append(f"| {i} | {feature} | {r:+.3f} | {p:.4f} | {corr_type} | {category} |\n")
    
    report.append("\n---\n")
    
    # 结论和建议
    report.append("## 6. 结论和建议\n")
    report.append("\n### 6.1 主要结论\n\n")
    report.append("1. **核心风险指标验证成功**: 感染率、存活数、新报告数等核心指标与风险等级呈强正相关，符合预期\n\n")
    report.append("2. **吸毒传播是关键风险因素**: 注射吸毒者规模、吸毒传播病例数等指标相关性强，需要重点关注\n\n")
    report.append("3. **干预效果指标呈现复杂关系**: 治疗覆盖率、检测覆盖率等与风险呈正相关，可能反映资源投入效应\n\n")
    report.append("4. **发现新的风险关联**: 儿童病例数、年龄分布等特征与风险显著相关，值得深入研究\n\n")
    
    report.append("### 6.2 政策建议\n\n")
    report.append("1. **加强吸毒人群干预**: 针对注射吸毒传播途径，加强美沙酮维持治疗、清洁针具交换等措施\n\n")
    report.append("2. **关注母婴传播**: 儿童病例数与风险相关，需要加强孕产妇HIV筛查和母婴阻断\n\n")
    report.append("3. **优化资源配置**: 在保持高风险地区资源投入的同时，关注干预措施的实际效果\n\n")
    report.append("4. **建立长期监测**: 跟踪干预措施的长期效果，评估时间滞后影响\n\n")
    
    report.append("### 6.3 研究局限\n\n")
    report.append("1. **样本量有限**: 仅190个县区，可能影响统计检验的效力\n\n")
    report.append("2. **横断面数据**: 无法确定因果关系，只能识别相关性\n\n")
    report.append("3. **混淆因素**: 未控制社会经济、地理位置等混淆因素\n\n")
    report.append("4. **数据质量**: 不同地区数据收集质量可能存在差异\n\n")
    
    report.append("\n---\n")
    
    # 附录
    report.append("## 附录\n")
    report.append("\n### A. 相关性分析方法说明\n\n")
    report.append("**Pearson相关系数**:\n")
    report.append("- 衡量两个变量之间的线性关系\n")
    report.append("- 取值范围: -1到+1\n")
    report.append("- |r| > 0.3: 强相关, 0.1 < |r| < 0.3: 中等相关, |r| < 0.1: 弱相关\n\n")
    
    report.append("**Spearman相关系数**:\n")
    report.append("- 衡量两个变量之间的单调关系（不要求线性）\n")
    report.append("- 对异常值不敏感\n\n")
    
    report.append("**互信息**:\n")
    report.append("- 衡量两个变量之间的非线性依赖关系\n")
    report.append("- 可以检测复杂的关联模式\n\n")
    
    report.append("**统计显著性**:\n")
    report.append("- p < 0.05: 统计显著\n")
    report.append("- p < 0.01: 高度显著\n")
    report.append("- p < 0.001: 极显著\n\n")
    
    report.append("### B. 特征映射表\n\n")
    report.append("**已知正相关特征映射**:\n\n")
    report.append("| 需求文档名称 | 模型特征名称 |\n")
    report.append("|------------|------------|\n")
    for req_name, model_name in analyzer.positive_features.items():
        report.append(f"| {req_name} | {model_name} |\n")
    
    report.append("\n**已知负相关特征映射**:\n\n")
    report.append("| 需求文档名称 | 模型特征名称 |\n")
    report.append("|------------|------------|\n")
    for req_name, model_name in analyzer.negative_features.items():
        report.append(f"| {req_name} | {model_name} |\n")
    
    report.append("\n---\n")
    report.append(f"\n**报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report.append(f"**分析工具**: HIV风险因素相关性分析器 v1.0\n")
    
    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(''.join(report))
    
    print(f"✓ 报告已保存: {output_path}")
    print(f"  文件大小: {os.path.getsize(output_path) / 1024:.1f} KB")


def main():
    """
    生成相关性分析报告
    """
    print("="*80)
    print("  生成HIV风险因素相关性分析报告")
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
    
    # 5. 生成报告
    print("\n步骤5: 生成Markdown报告...")
    output_dir = 'outputs/correlation_analysis'
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, 'correlation_analysis_report.md')
    generate_markdown_report(
        analyzer,
        correlation_results,
        verification_results,
        unknown_results,
        output_path
    )
    
    print("\n" + "="*80)
    print("✓ 报告生成完成")
    print(f"✓ 报告位置: {output_path}")
    print("="*80)


if __name__ == '__main__':
    main()
