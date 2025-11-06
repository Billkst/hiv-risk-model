import pandas as pd

df = pd.read_csv('data/processed/hiv_data_processed.csv')

print(f'数据维度: {df.shape}')
print(f'\n最后10列:')
print(df.columns[-10:].tolist())

print(f'\n前5行的医疗数据:')
medical_cols = ['医疗机构总数', '医院数量', '床位数', '卫生技术人员', '每千人口床位数', '每千人口卫生技术人员']
print(df[medical_cols].head())

print(f'\n医疗数据统计:')
print(df[medical_cols].describe())
