"""
处理真实 HIV 数据
根据提供的字段信息处理 CSV 数据
"""

import pandas as pd
import numpy as np
import os

# 根据你提供的字段信息定义列名
COLUMN_NAMES = [
    # 基本信息
    '区县', '存活数', '感染率',
    
    # 存活病例年龄构成 (0-, 5-, 10-, ..., 80-)
    '存活_0-', '存活_5-', '存活_10-', '存活_15-', '存活_20-', '存活_25-', 
    '存活_30-', '存活_35-', '存活_40-', '存活_45-', '存活_50-', '存活_55-', 
    '存活_60-', '存活_65-', '存活_70-', '存活_75-', '存活_80-',
    
    # 现存活病例感染途径构成
    '存活_同性传播', '存活_配偶阳性', '存活_商业性行为', '存活_非婚非商业', 
    '存活_非婚未分类', '存活_注射毒品', '存活_母婴传播', '存活_其他或不详',
    
    # 新报告
    '新报告',
    
    # 新报告病例年龄构成
    '新报告_0-', '新报告_5-', '新报告_10-', '新报告_15-', '新报告_20-', '新报告_25-',
    '新报告_30-', '新报告_35-', '新报告_40-', '新报告_45-', '新报告_50-', '新报告_55-',
    '新报告_60-', '新报告_65-', '新报告_70-', '新报告_75-', '新报告_80-',
    
    # 新报告病例感染途径构成
    '新报告_同性传播', '新报告_配偶阳性', '新报告_商业性行为', '新报告_非婚非商业',
    '新报告_非婚未分类', '新报告_注射毒品', '新报告_母婴传播', '新报告_其他或不详',
    
    # 治疗相关
    '治疗覆盖率', '30天治疗比例',
    
    # 病毒载量检测
    '检测比例', '病毒抑制比例', '病载小于50占现存活比例',
    
    # 暗娼
    '暗娼_月均估计数', '暗娼_月均干预人数', '暗娼_月均覆盖率', '暗娼_HIV检测人数', '暗娼_HIV检测阳性人数',
    
    # 男男性行为者
    'MSM_月均估计数', 'MSM_月均干预人数', 'MSM_月均覆盖率', 'MSM_HIV检测人数', 'MSM_HIV检测阳性人数',
    
    # 吸毒者
    '吸毒者_月均估计数', '吸毒者_月均干预人数', '吸毒者_月均覆盖率', '吸毒者_HIV检测人数', '吸毒者_HIV检测阳性人数',
    
    # 性病就诊者
    '性病就诊者_干预人数', '性病就诊者_HIV检测人数', '性病就诊者_本年累计HIV检测率', '性病就诊者_HIV检测阳性人数',
    
    # 外来务工人员
    '外来务工_月均估计数', '外来务工_月均干预人数', '外来务工_月均覆盖率', '外来务工_HIV检测人数', '外来务工_HIV检测阳性人数',
    
    # 其他人群
    '其他人群_月均估计数', '其他人群_月均干预人数', '其他人群_月均覆盖率', '其他人群_HIV检测人数', '其他人群_HIV检测阳性人数',
    
    # 人群规模
    '注射吸毒者规模', '城市MSM规模', '暗娼规模', '嫖客规模', '农村MSM规模', '移动评估MSM人数',
    
    # 筛查数据
    '人口数', '筛查人次数', '筛查覆盖率', '筛查人数', '按人数筛查覆盖率',
    
    # 公安挡获
    '挡获暗娼人次数', '暗娼HIV检测阳性率', '既往阳性暗娼数', 
    '挡获嫖客人次数', '嫖客HIV检测阳性率', '既往阳性嫖客数',
    
    # 按方案评定级别
    '按方案评定级别'
]


def load_and_process_data(csv_path='data/hiv数据.csv'):
    """加载并处理真实数据"""
    
    print("=" * 60)
    print("加载真实 HIV 数据")
    print("=" * 60)
    
    # 读取 CSV（无表头）
    df = pd.read_csv(csv_path, header=None)
    
    print(f"\n原始数据维度: {df.shape}")
    print(f"列数: {df.shape[1]}")
    print(f"预期列数: {len(COLUMN_NAMES)}")
    
    # 检查最后一列是否全为空（由于末尾逗号导致）
    if df.shape[1] == 107 and df.iloc[:, -1].isna().all():
        print("\n⚠️  检测到末尾空列（由CSV末尾逗号导致），已删除")
        df = df.iloc[:, :-1]  # 删除最后一列
        print(f"   修正后列数: {df.shape[1]}")
    
    # 检查列数是否匹配
    if df.shape[1] != len(COLUMN_NAMES):
        print(f"\n⚠️  警告: 列数不匹配!")
        print(f"   实际: {df.shape[1]} 列")
        print(f"   预期: {len(COLUMN_NAMES)} 列")
        print(f"   差异: {df.shape[1] - len(COLUMN_NAMES)} 列")
        
        # 使用实际列数
        if df.shape[1] < len(COLUMN_NAMES):
            column_names = COLUMN_NAMES[:df.shape[1]]
        else:
            column_names = COLUMN_NAMES + [f'未知字段_{i}' for i in range(len(COLUMN_NAMES), df.shape[1])]
    else:
        column_names = COLUMN_NAMES
    
    # 设置列名
    df.columns = column_names
    
    print(f"\n✓ 数据加载完成: {len(df)} 个区县")
    
    # 数据清洗
    print("\n" + "=" * 60)
    print("数据清洗")
    print("=" * 60)
    
    # 处理百分比字符串
    for col in df.columns:
        if df[col].dtype == 'object':
            # 移除百分号并转换为数值
            df[col] = df[col].astype(str).str.replace('%', '').str.strip()
            # 尝试转换为数值
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # 处理缺失值
    missing_count = df.isnull().sum().sum()
    print(f"缺失值总数: {missing_count}")
    
    # 填充缺失值
    df = df.fillna(0)
    
    # 基本统计
    print(f"\n✓ 数据清洗完成")
    print(f"  区县数量: {len(df)}")
    print(f"  特征数量: {len(df.columns)}")
    
    # 显示关键字段统计
    print(f"\n关键字段统计:")
    print(f"  感染率范围: {df['感染率'].min():.4f} ~ {df['感染率'].max():.4f}")
    print(f"  存活数范围: {df['存活数'].min():.0f} ~ {df['存活数'].max():.0f}")
    if '治疗覆盖率' in df.columns:
        print(f"  治疗覆盖率: {df['治疗覆盖率'].mean():.2f}%")
    
    return df


def create_risk_labels(df):
    """创建风险等级标签（基于感染率）"""
    
    print("\n" + "=" * 60)
    print("创建风险等级标签")
    print("=" * 60)
    
    # 检查感染率数据
    print(f"感染率统计:")
    print(f"  最小值: {df['感染率'].min():.6f}")
    print(f"  最大值: {df['感染率'].max():.6f}")
    print(f"  缺失值: {df['感染率'].isna().sum()}")
    
    # 基于感染率分级（扩大上限以包含所有值）
    df['risk_level'] = pd.cut(
        df['感染率'],
        bins=[0, 0.1, 0.5, 1.0, 5.0, 100.0],  # 调整区间以适应实际数据范围
        labels=[1, 2, 3, 4, 5],
        include_lowest=True
    )
    
    # 填充可能的 NaN 值（如果有）
    df['risk_level'] = df['risk_level'].fillna(3)  # 默认为中等风险
    
    # 转换为整数
    df['risk_level'] = df['risk_level'].astype(int)
    
    # 统计分布
    print("\n风险等级分布:")
    for level in range(1, 6):
        count = (df['risk_level'] == level).sum()
        pct = count / len(df) * 100
        print(f"  等级 {level}: {count:3d} 个区县 ({pct:5.1f}%)")
    
    return df


def save_processed_data(df, output_path='data/processed/hiv_data_processed.csv'):
    """保存处理后的数据"""
    
    # 创建输出目录
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 保存
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    print(f"\n✓ 处理后的数据已保存: {output_path}")
    
    return output_path


def main():
    """主函数"""
    
    # 加载数据
    df = load_and_process_data('data/hiv数据.csv')
    
    # 创建风险标签
    df = create_risk_labels(df)
    
    # 保存处理后的数据
    output_path = save_processed_data(df)
    
    print("\n" + "=" * 60)
    print("✓ 数据处理完成！")
    print("=" * 60)
    print(f"\n下一步:")
    print(f"1. 查看处理后的数据: {output_path}")
    print(f"2. 运行模型训练: python models/model_trainer.py")
    
    return df


if __name__ == '__main__':
    df = main()
