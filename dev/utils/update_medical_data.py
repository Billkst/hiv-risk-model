"""
使用新的准确匹配的医疗数据更新HIV数据集
"""

import pandas as pd
import numpy as np


def load_data():
    """加载数据"""
    print("=" * 80)
    print("加载数据")
    print("=" * 80)
    
    # 加载HIV数据
    hiv_df = pd.read_csv('data/processed/hiv_data_processed.csv')
    print(f"✓ HIV数据: {hiv_df.shape}")
    print(f"  区县ID范围: {hiv_df['区县'].min():.6f} ~ {hiv_df['区县'].max():.6f}")
    
    # 加载新的医疗数据
    medical_df = pd.read_csv('data/183县区.CSV')
    print(f"✓ 新医疗数据: {medical_df.shape}")
    print(f"  区县ID范围: {medical_df['区县'].min():.6f} ~ {medical_df['区县'].max():.6f}")
    
    return hiv_df, medical_df


def check_matching(hiv_df, medical_df):
    """检查区县ID匹配情况"""
    print("\n" + "=" * 80)
    print("检查区县ID匹配")
    print("=" * 80)
    
    # 转换为相同类型
    hiv_ids = set(hiv_df['区县'].values)
    medical_ids = set(medical_df['区县'].values)
    
    # 匹配分析
    matched = hiv_ids & medical_ids
    hiv_only = hiv_ids - medical_ids
    medical_only = medical_ids - hiv_ids
    
    print(f"\n匹配统计:")
    print(f"  HIV数据区县数: {len(hiv_ids)}")
    print(f"  医疗数据区县数: {len(medical_ids)}")
    print(f"  匹配成功: {len(matched)} 个区县")
    print(f"  仅在HIV数据: {len(hiv_only)} 个区县")
    print(f"  仅在医疗数据: {len(medical_only)} 个区县")
    
    if len(hiv_only) > 0:
        print(f"\n⚠️  未匹配的HIV区县ID（前5个）:")
        for id in list(hiv_only)[:5]:
            print(f"    {id:.8f}")
    
    return matched, hiv_only, medical_only


def update_medical_fields(hiv_df, medical_df):
    """更新医疗字段"""
    print("\n" + "=" * 80)
    print("更新医疗字段")
    print("=" * 80)
    
    # 旧的医疗字段
    old_medical_fields = [
        '医疗机构总数', '医院数量', '床位数', 
        '卫生技术人员', '每千人口床位数', '每千人口卫生技术人员'
    ]
    
    # 备份旧数据
    print(f"\n备份旧医疗数据...")
    old_medical_data = hiv_df[old_medical_fields].copy()
    
    # 删除旧的医疗字段
    hiv_df_clean = hiv_df.drop(columns=old_medical_fields)
    print(f"✓ 删除旧医疗字段")
    print(f"  清理后维度: {hiv_df_clean.shape}")
    
    # 合并新的医疗数据（基于区县ID）
    print(f"\n合并新医疗数据...")
    merged_df = hiv_df_clean.merge(
        medical_df,
        on='区县',
        how='left'
    )
    
    print(f"✓ 合并完成")
    print(f"  合并后维度: {merged_df.shape}")
    
    # 检查缺失值
    missing_count = merged_df[old_medical_fields].isna().sum()
    
    print(f"\n新医疗数据缺失情况:")
    for field in old_medical_fields:
        missing = missing_count[field]
        if missing > 0:
            print(f"  {field}: {missing} 个缺失值")
        else:
            print(f"  {field}: ✓ 无缺失")
    
    return merged_df, old_medical_data


def fill_missing_medical_data(df, medical_fields):
    """填充缺失的医疗数据"""
    print("\n" + "=" * 80)
    print("处理缺失值")
    print("=" * 80)
    
    total_missing = df[medical_fields].isna().sum().sum()
    
    if total_missing == 0:
        print("✓ 无缺失值，无需处理")
        return df
    
    print(f"\n使用中位数填充缺失值...")
    
    for field in medical_fields:
        missing = df[field].isna().sum()
        if missing > 0:
            median_value = df[field].median()
            df[field].fillna(median_value, inplace=True)
            print(f"  {field}: 填充 {missing} 个缺失值 (中位数={median_value:.2f})")
    
    print(f"\n✓ 填充完成")
    
    return df


def compare_old_new_data(old_data, new_data, fields):
    """对比新旧医疗数据"""
    print("\n" + "=" * 80)
    print("新旧数据对比")
    print("=" * 80)
    
    print(f"\n{'字段':<30} {'旧数据均值':<15} {'新数据均值':<15} {'差异':<10}")
    print("-" * 70)
    
    for field in fields:
        old_mean = old_data[field].mean()
        new_mean = new_data[field].mean()
        diff_pct = (new_mean - old_mean) / old_mean * 100 if old_mean > 0 else 0
        
        print(f"{field:<30} {old_mean:<15.2f} {new_mean:<15.2f} {diff_pct:+.2f}%")


def save_updated_data(df, output_path='data/processed/hiv_data_processed.csv'):
    """保存更新后的数据"""
    print("\n" + "=" * 80)
    print("保存数据")
    print("=" * 80)
    
    # 备份原文件
    import shutil
    backup_path = output_path.replace('.csv', '_old_medical.csv')
    
    try:
        shutil.copy(output_path, backup_path)
        print(f"✓ 原文件已备份: {backup_path}")
    except:
        print(f"⚠️  无法备份原文件")
    
    # 保存新文件
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"✓ 更新后数据已保存: {output_path}")
    print(f"  维度: {df.shape}")
    print(f"  字段数: {len(df.columns)}")


def main():
    """主流程"""
    print("\n" + "=" * 80)
    print("更新医疗数据")
    print("使用新的准确匹配的医疗数据")
    print("=" * 80)
    
    # 步骤1: 加载数据
    hiv_df, medical_df = load_data()
    
    # 步骤2: 检查匹配
    matched, hiv_only, medical_only = check_matching(hiv_df, medical_df)
    
    # 步骤3: 更新医疗字段
    updated_df, old_medical_data = update_medical_fields(hiv_df, medical_df)
    
    # 步骤4: 填充缺失值
    medical_fields = [
        '医疗机构总数', '医院数量', '床位数',
        '卫生技术人员', '每千人口床位数', '每千人口卫生技术人员'
    ]
    updated_df = fill_missing_medical_data(updated_df, medical_fields)
    
    # 步骤5: 对比新旧数据
    compare_old_new_data(old_medical_data, updated_df[medical_fields], medical_fields)
    
    # 步骤6: 保存数据
    save_updated_data(updated_df)
    
    print("\n" + "=" * 80)
    print("✓ 医疗数据更新完成")
    print("=" * 80)
    
    print(f"\n变化总结:")
    print(f"  - 使用新的准确匹配的医疗数据")
    print(f"  - 匹配成功: {len(matched)} 个区县")
    print(f"  - 数据维度: {updated_df.shape}")
    
    return updated_df


if __name__ == '__main__':
    updated_df = main()
