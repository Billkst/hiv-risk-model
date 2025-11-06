import pandas as pd

df = pd.read_csv('data/processed/hiv_data_processed.csv')

print("=" * 60)
print("数据验证")
print("=" * 60)

print(f"\n数据维度: {df.shape}")
print(f"字段数: {len(df.columns)}")

print("\n按方案评定级别分布:")
print(df['按方案评定级别'].value_counts().sort_index())

print("\nrisk_level分布:")
print(df['risk_level'].value_counts().sort_index())

print("\n前5行关键字段:")
print(df[['区县', '存活数', '感染率', '按方案评定级别', 'risk_level']].head())

print("\n字段列表:")
for i, col in enumerate(df.columns, 1):
    print(f"{i:3d}. {col}")
