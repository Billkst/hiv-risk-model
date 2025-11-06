"""
特征工程模块
处理特征选择、标准化和数据集划分
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib
import os


class FeatureEngineer:
    """特征工程类"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.feature_columns = None
        self.target_column = 'risk_level'
        
    def load_data(self, csv_path):
        """加载处理后的数据"""
        print("=" * 60)
        print("加载数据")
        print("=" * 60)
        
        df = pd.read_csv(csv_path)
        print(f"✓ 数据加载成功: {df.shape[0]} 行 × {df.shape[1]} 列")
        
        return df
    
    def select_features(self, df):
        """选择特征列"""
        print("\n" + "=" * 60)
        print("特征选择")
        print("=" * 60)
        
        # 排除的列
        exclude_columns = [
            '区县',                    # ID列，不用于训练
            '按方案评定级别',          # 原始标签，不用于训练
            'risk_level'              # 目标变量
        ]
        
        # 选择特征列
        self.feature_columns = [col for col in df.columns if col not in exclude_columns]
        
        print(f"✓ 特征数量: {len(self.feature_columns)}")
        print(f"  排除列: {exclude_columns}")
        
        # 显示特征类别统计
        print(f"\n特征分类:")
        feature_categories = {
            '基本信息': ['存活数', '感染率'],
            '年龄构成': [col for col in self.feature_columns if '存活_' in col and '-' in col or '新报告_' in col and '-' in col],
            '传播途径': [col for col in self.feature_columns if '同性传播' in col or '配偶阳性' in col or '商业性行为' in col or '非婚' in col or '注射毒品' in col or '母婴传播' in col],
            '治疗检测': [col for col in self.feature_columns if '治疗' in col or '检测' in col or '病毒' in col or '病载' in col],
            '干预数据': [col for col in self.feature_columns if '暗娼' in col or 'MSM' in col or '吸毒者' in col or '性病就诊者' in col or '外来务工' in col or '其他人群' in col],
            '人群规模': [col for col in self.feature_columns if '规模' in col or '移动评估' in col],
            '筛查数据': [col for col in self.feature_columns if '筛查' in col or '人口数' in col],
            '公安挡获': [col for col in self.feature_columns if '挡获' in col or '既往阳性' in col]
        }
        
        for category, cols in feature_categories.items():
            print(f"  {category}: {len(cols)} 个特征")
        
        return self.feature_columns
    
    def prepare_data(self, df):
        """准备训练数据"""
        print("\n" + "=" * 60)
        print("准备训练数据")
        print("=" * 60)
        
        # 分离特征和目标
        X = df[self.feature_columns].copy()
        y = df[self.target_column].copy()
        
        print(f"✓ 特征矩阵 X: {X.shape}")
        print(f"✓ 目标变量 y: {y.shape}")
        
        # 检查目标变量分布
        print(f"\n目标变量分布:")
        for level in sorted(y.unique()):
            count = (y == level).sum()
            pct = count / len(y) * 100
            print(f"  等级 {level}: {count:3d} 样本 ({pct:5.1f}%)")
        
        # 检查特征缺失值
        missing = X.isnull().sum().sum()
        if missing > 0:
            print(f"\n⚠️  特征中存在 {missing} 个缺失值")
        else:
            print(f"\n✓ 特征无缺失值")
        
        return X, y
    
    def split_data(self, X, y, test_size=0.15, val_size=0.15, random_state=42):
        """划分数据集（训练集、验证集、测试集）"""
        print("\n" + "=" * 60)
        print("数据集划分")
        print("=" * 60)
        
        # 检查是否可以进行分层采样
        min_class_count = y.value_counts().min()
        use_stratify = min_class_count >= 2
        
        if not use_stratify:
            print(f"⚠️  最小类别样本数为 {min_class_count}，无法使用分层采样")
            print(f"   将使用随机采样")
        
        # 先划分出测试集
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y, 
            test_size=test_size, 
            random_state=random_state,
            stratify=y if use_stratify else None
        )
        
        # 再从剩余数据中划分验证集
        val_ratio = val_size / (1 - test_size)
        
        # 检查剩余数据是否可以分层
        min_temp_count = y_temp.value_counts().min()
        use_stratify_val = min_temp_count >= 2
        
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp,
            test_size=val_ratio,
            random_state=random_state,
            stratify=y_temp if use_stratify_val else None
        )
        
        print(f"✓ 训练集: {X_train.shape[0]} 样本 ({X_train.shape[0]/len(X)*100:.1f}%)")
        print(f"✓ 验证集: {X_val.shape[0]} 样本 ({X_val.shape[0]/len(X)*100:.1f}%)")
        print(f"✓ 测试集: {X_test.shape[0]} 样本 ({X_test.shape[0]/len(X)*100:.1f}%)")
        
        # 检查各集合的类别分布
        print(f"\n各数据集类别分布:")
        for dataset_name, y_data in [('训练集', y_train), ('验证集', y_val), ('测试集', y_test)]:
            print(f"\n{dataset_name}:")
            for level in sorted(y.unique()):
                count = (y_data == level).sum()
                pct = count / len(y_data) * 100
                print(f"  等级 {level}: {count:2d} 样本 ({pct:5.1f}%)")
        
        return X_train, X_val, X_test, y_train, y_val, y_test
    
    def scale_features(self, X_train, X_val, X_test):
        """特征标准化"""
        print("\n" + "=" * 60)
        print("特征标准化")
        print("=" * 60)
        
        # 在训练集上拟合
        self.scaler.fit(X_train)
        
        # 转换所有数据集
        X_train_scaled = pd.DataFrame(
            self.scaler.transform(X_train),
            columns=X_train.columns,
            index=X_train.index
        )
        
        X_val_scaled = pd.DataFrame(
            self.scaler.transform(X_val),
            columns=X_val.columns,
            index=X_val.index
        )
        
        X_test_scaled = pd.DataFrame(
            self.scaler.transform(X_test),
            columns=X_test.columns,
            index=X_test.index
        )
        
        print(f"✓ 使用 StandardScaler 进行标准化")
        print(f"✓ 训练集: {X_train_scaled.shape}")
        print(f"✓ 验证集: {X_val_scaled.shape}")
        print(f"✓ 测试集: {X_test_scaled.shape}")
        
        # 显示标准化前后的统计信息
        print(f"\n标准化前（训练集）:")
        print(f"  均值范围: [{X_train.mean().min():.2f}, {X_train.mean().max():.2f}]")
        print(f"  标准差范围: [{X_train.std().min():.2f}, {X_train.std().max():.2f}]")
        
        print(f"\n标准化后（训练集）:")
        print(f"  均值范围: [{X_train_scaled.mean().min():.2e}, {X_train_scaled.mean().max():.2e}]")
        print(f"  标准差范围: [{X_train_scaled.std().min():.2f}, {X_train_scaled.std().max():.2f}]")
        
        return X_train_scaled, X_val_scaled, X_test_scaled
    
    def save_scaler(self, save_path='saved_models/scaler.pkl'):
        """保存标准化器"""
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        joblib.dump(self.scaler, save_path)
        print(f"\n✓ 标准化器已保存: {save_path}")
    
    def process_pipeline(self, csv_path, save_scaler=True):
        """完整的特征工程流程"""
        print("\n" + "=" * 80)
        print("特征工程流程")
        print("=" * 80)
        
        # 1. 加载数据
        df = self.load_data(csv_path)
        
        # 2. 选择特征
        self.select_features(df)
        
        # 3. 准备数据
        X, y = self.prepare_data(df)
        
        # 4. 划分数据集
        X_train, X_val, X_test, y_train, y_val, y_test = self.split_data(X, y)
        
        # 5. 特征标准化
        X_train_scaled, X_val_scaled, X_test_scaled = self.scale_features(
            X_train, X_val, X_test
        )
        
        # 6. 保存标准化器
        if save_scaler:
            self.save_scaler()
        
        print("\n" + "=" * 80)
        print("✓ 特征工程完成！")
        print("=" * 80)
        
        return {
            'X_train': X_train_scaled,
            'X_val': X_val_scaled,
            'X_test': X_test_scaled,
            'y_train': y_train,
            'y_val': y_val,
            'y_test': y_test,
            'feature_columns': self.feature_columns
        }


if __name__ == '__main__':
    # 测试特征工程流程
    engineer = FeatureEngineer()
    data = engineer.process_pipeline('data/processed/hiv_data_processed.csv')
    
    print(f"\n返回的数据字典包含:")
    for key, value in data.items():
        if key != 'feature_columns':
            print(f"  {key}: {value.shape}")
        else:
            print(f"  {key}: {len(value)} 个特征")
