"""
重新运行预测并生成详细报告
显示每个区县的风险等级和分数
"""

import sys
sys.path.append('.')

from models.predictor import HIVRiskPredictor
import pandas as pd

def main():
    print("\n" + "=" * 80)
    print("HIV 风险预测 - 详细报告")
    print("=" * 80)
    
    # 加载预测器
    predictor = HIVRiskPredictor()
    
    # 批量预测
    df_result = predictor.batch_predict_from_csv(
        'data/processed/hiv_data_processed.csv',
        'data/processed/hiv_predictions_detailed.csv'
    )
    
    # 显示每个区县的预测结果
    print(f"\n每个区县的风险等级和分数:")
    print("=" * 80)
    
    # 选择要显示的列
    display_cols = ['区县', '预测风险等级_5级', '风险描述', '风险分数', '置信度', '感染率', '存活数']
    
    # 检查区县列是否存在
    if '区县' not in df_result.columns:
        # 如果没有区县列，使用索引
        df_result['区县'] = df_result.index
    
    # 按风险等级排序
    df_display = df_result[display_cols].sort_values('预测风险等级_5级', ascending=False)
    
    # 分等级显示
    for level in range(5, 0, -1):
        level_data = df_display[df_display['预测风险等级_5级'] == level]
        if len(level_data) > 0:
            print(f"\n等级 {level} - {level_data.iloc[0]['风险描述']} ({len(level_data)} 个区县):")
            print("-" * 80)
            for idx, row in level_data.iterrows():
                county = str(row['区县']) if pd.notna(row['区县']) else f"区县{idx}"
                print(f"  {county:15s} | 分数: {row['风险分数']:6.2f} | "
                      f"置信度: {row['置信度']:.4f} | 感染率: {row['感染率']:.2f}% | "
                      f"存活数: {int(row['存活数'])}")
    
    # 生成简化版报告
    print(f"\n\n生成简化版报告...")
    simple_report = df_result[['区县', '预测风险等级_5级', '风险描述', '风险分数', '感染率', '存活数']].copy()
    simple_report = simple_report.sort_values('预测风险等级_5级', ascending=False)
    simple_report.to_csv('data/processed/hiv_risk_report_simple.csv', index=False, encoding='utf-8-sig')
    print(f"✓ 简化报告已保存: data/processed/hiv_risk_report_simple.csv")
    
    # 统计每个等级的分数范围
    print(f"\n\n各等级风险分数详细统计:")
    print("=" * 80)
    for level in range(1, 6):
        level_data = df_result[df_result['预测风险等级_5级'] == level]
        if len(level_data) > 0:
            scores = level_data['风险分数']
            print(f"\n等级 {level} - {level_data.iloc[0]['风险描述']}:")
            print(f"  样本数: {len(level_data)}")
            print(f"  分数范围: {scores.min():.2f} - {scores.max():.2f}")
            print(f"  平均分数: {scores.mean():.2f}")
            print(f"  中位数: {scores.median():.2f}")
            print(f"  标准差: {scores.std():.2f}")
    
    print("\n" + "=" * 80)
    print("✓ 预测完成！")
    print("=" * 80)

if __name__ == '__main__':
    main()
