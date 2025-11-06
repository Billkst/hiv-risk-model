"""
读取 Excel 数据的工具脚本
"""

import pandas as pd
import sys

def read_excel_file(file_path):
    """读取 Excel 文件并显示基本信息"""
    try:
        # 尝试读取 Excel
        df = pd.read_excel(file_path, engine='openpyxl')
        
        print("=" * 60)
        print("✓ 文件读取成功！")
        print("=" * 60)
        
        # 基本信息
        print(f"\n数据维度: {df.shape[0]} 行 × {df.shape[1]} 列")
        
        # 列名
        print(f"\n字段列表 ({len(df.columns)} 个):")
        print("-" * 60)
        for i, col in enumerate(df.columns, 1):
            print(f"{i:2d}. {col}")
        
        # 数据类型
        print(f"\n数据类型:")
        print("-" * 60)
        print(df.dtypes)
        
        # 前几行数据
        print(f"\n前 5 行数据预览:")
        print("-" * 60)
        print(df.head())
        
        # 缺失值统计
        print(f"\n缺失值统计:")
        print("-" * 60)
        missing = df.isnull().sum()
        if missing.sum() > 0:
            print(missing[missing > 0])
        else:
            print("无缺失值")
        
        # 数值列的统计信息
        print(f"\n数值列统计:")
        print("-" * 60)
        print(df.describe())
        
        # 保存为 CSV（方便后续处理）
        csv_path = file_path.replace('.xlsx', '.csv')
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"\n✓ 已导出为 CSV: {csv_path}")
        
        return df
        
    except Exception as e:
        print(f"❌ 读取失败: {e}")
        print("\n可能的原因:")
        print("1. 文件被加密/密码保护")
        print("2. 文件格式不正确")
        print("3. 缺少必要的库 (openpyxl)")
        print("\n解决方法:")
        print("- 在 Excel 中另存为无密码版本")
        print("- 或导出为 CSV 格式")
        return None


if __name__ == '__main__':
    file_path = 'data/2024.xlsx'
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    
    print(f"正在读取: {file_path}\n")
    df = read_excel_file(file_path)
