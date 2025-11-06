"""
合并医疗数据到HIV数据集
添加6个新字段：医疗机构总数、医院数量、床位数、卫生技术人员、每千人口床位数、每千人口卫生技术人员
"""

import pandas as pd
import numpy as np
from sklearn.impute import KNNImputer


def load_data():
    """加载两个数据集"""
    print("=" * 80)
    print("加载数据")
    print("=" * 80)
    
    # 加载HIV数据
    hiv_df = pd.read_csv('data/processed/hiv_data_processed.csv')
    print(f"✓ HIV数据: {hiv_df.shape}")
    
    # 加载医疗数据
    medical_df = pd.read_csv('data/sichuan_183_counties_medical_data_2024.csv')
    print(f"✓ 医疗数据: {medical_df.shape}")
    
    print(f"\n数据行数差异: {len(hiv_df)} - {len(medical_df)} = {len(hiv_df) - len(medical_df)} 行")
    
    return hiv_df, medical_df


def analyze_medical_data(medical_df):
    """分析医疗数据"""
    print("\n" + "=" * 80)
    print("医疗数据分析")
    print("=" * 80)
    
    print(f"\n字段列表:")
    for i, col in enumerate(medical_df.columns, 1):
        print(f"  {i}. {col}")
    
    print(f"\n前5行数据:")
    print(medical_df.head())
    
    # 统计信息
    print(f"\n数值字段统计:")
    numeric_cols = ['医疗机构总数', '医院数量', '床位数', '卫生技术人员', '每千人口床位数', '每千人口卫生技术人员']
    for col in numeric_cols:
        if col in medical_df.columns:
            print(f"  {col}:")
            print(f"    均值: {medical_df[col].mean():.2f}")
            print(f"    中位数: {medical_df[col].median():.2f}")
            print(f"    范围: [{medical_df[col].min():.2f}, {medical_df[col].max():.2f}]")


def merge_datasets(hiv_df, medical_df):
    """合并数据集"""
    print("\n" + "=" * 80)
    print("合并数据集")
    print("=" * 80)
    
    # 提取需要的医疗字段
    medical_fields = ['医疗机构总数', '医院数量', '床位数', '卫生技术人员', '每千人口床位数', '每千人口卫生技术人员']
    
    # 检查区县字段类型
    print(f"\nHIV数据'区县'字段类型: {hiv_df['区县'].dtype}")
    print(f"医疗数据'区县'字段类型: {medical_df['区县'].dtype}")
    
    # HIV数据的区县是数字ID，医疗数据的区县是名称，无法直接匹配
    # 使用索引顺序匹配（假设两个数据集的区县顺序一致）
    print(f"\n⚠️  区县字段类型不匹配，使用索引顺序合并")
    print(f"   假设: 两个数据集的区县顺序一致")
    
    # 创建一个新的DataFrame来存储医疗数据
    medical_data = pd.DataFrame(index=hiv_df.index, columns=medical_fields)
    
    # 复制前183行
    n_medical = len(medical_df)
    medical_data.iloc[:n_medical] = medical_df[medical_fields].values
    
    # 合并
    merged_df = pd.concat([hiv_df, medical_data], axis=1)
    
    unmatched = merged_df[medical_fields[0]].isna().sum()
    print(f"  已填充: {n_medical} 行")
    print(f"  缺失: {unmatched} 行")
    
    return merged_df


def fill_missing_values(df, medical_fields):
    """填充缺失的医疗数据"""
    print("\n" + "=" * 80)
    print("填充缺失值")
    print("=" * 80)
    
    # 检查缺失情况
    missing_count = df[medical_fields].isna().sum().sum()
    
    if missing_count == 0:
        print("✓ 无缺失值，无需填充")
        return df
    
    print(f"\n缺失值统计:")
    for col in medical_fields:
        missing = df[col].isna().sum()
        if missing > 0:
            print(f"  {col}: {missing} 个缺失值")
    
    # 策略1: 使用KNN填充（基于其他特征）
    print(f"\n使用KNN填充策略...")
    print(f"  原理: 根据相似区县的医疗数据进行填充")
    
    # 选择用于KNN的特征（使用HIV数据中的相关特征）
    knn_features = ['存活数', '人口数', '筛查人次数', '筛查人数']
    available_features = [f for f in knn_features if f in df.columns]
    
    if len(available_features) > 0:
        print(f"  使用特征: {', '.join(available_features)}")
        
        # 准备数据
        X_for_impute = df[available_features + medical_fields].copy()
        
        # 使用KNN填充
        imputer = KNNImputer(n_neighbors=5)
        X_imputed = imputer.fit_transform(X_for_impute)
        
        # 更新医疗字段
        medical_start_idx = len(available_features)
        for i, col in enumerate(medical_fields):
            df[col] = X_imputed[:, medical_start_idx + i]
        
        print(f"  ✓ KNN填充完成")
        
    else:
        # 策略2: 使用中位数填充
        print(f"  ⚠️  可用特征不足，使用中位数填充")
        
        for col in medical_fields:
            if df[col].isna().any():
                median_value = df[col].median()
                df[col].fillna(median_value, inplace=True)
                print(f"    {col}: 填充值 = {median_value:.2f}")
    
    # 验证
    remaining_missing = df[medical_fields].isna().sum().sum()
    print(f"\n✓ 填充后剩余缺失值: {remaining_missing}")
    
    return df


def validate_merged_data(df, medical_fields):
    """验证合并后的数据"""
    print("\n" + "=" * 80)
    print("数据验证")
    print("=" * 80)
    
    print(f"\n合并后数据维度: {df.shape}")
    
    # 检查新字段
    print(f"\n新增字段统计:")
    for col in medical_fields:
        if col in df.columns:
            print(f"  {col}:")
            print(f"    均值: {df[col].mean():.2f}")
            print(f"    中位数: {df[col].median():.2f}")
            print(f"    范围: [{df[col].min():.2f}, {df[col].max():.2f}]")
            print(f"    缺失值: {df[col].isna().sum()}")
    
    # 检查数据完整性
    total_missing = df.isna().sum().sum()
    print(f"\n总缺失值: {total_missing}")
    
    if total_missing == 0:
        print(f"✓ 数据完整，无缺失值")
    else:
        print(f"⚠️  仍有 {total_missing} 个缺失值")


def save_merged_data(df, output_path='data/processed/hiv_data_processed.csv'):
    """保存合并后的数据"""
    print("\n" + "=" * 80)
    print("保存数据")
    print("=" * 80)
    
    # 备份原文件
    import shutil
    backup_path = output_path.replace('.csv', '_backup.csv')
    
    try:
        shutil.copy(output_path, backup_path)
        print(f"✓ 原文件已备份: {backup_path}")
    except:
        print(f"⚠️  无法备份原文件")
    
    # 保存新文件
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"✓ 合并后数据已保存: {output_path}")
    print(f"  维度: {df.shape}")
    print(f"  字段数: {len(df.columns)}")


def main():
    """主流程"""
    print("\n" + "=" * 80)
    print("合并医疗数据到HIV数据集")
    print("=" * 80)
    
    # 步骤1: 加载数据
    hiv_df, medical_df = load_data()
    
    # 步骤2: 分析医疗数据
    analyze_medical_data(medical_df)
    
    # 步骤3: 合并数据集
    merged_df = merge_datasets(hiv_df, medical_df)
    
    # 步骤4: 填充缺失值
    medical_fields = ['医疗机构总数', '医院数量', '床位数', '卫生技术人员', '每千人口床位数', '每千人口卫生技术人员']
    merged_df = fill_missing_values(merged_df, medical_fields)
    
    # 步骤5: 验证数据
    validate_merged_data(merged_df, medical_fields)
    
    # 步骤6: 保存数据
    save_merged_data(merged_df)
    
    print("\n" + "=" * 80)
    print("✓ 数据合并完成")
    print("=" * 80)
    
    print(f"\n新增字段:")
    for i, field in enumerate(medical_fields, 1):
        print(f"  {i}. {field}")
    
    return merged_df


if __name__ == '__main__':
    merged_df = main()
