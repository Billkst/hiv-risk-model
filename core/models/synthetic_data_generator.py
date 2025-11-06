"""
使用CTGAN生成高质量合成数据
"""

import pandas as pd
import numpy as np
from sdv.single_table import CTGANSynthesizer
from sdv.metadata import SingleTableMetadata
import warnings
warnings.filterwarnings('ignore')


class SyntheticDataGenerator:
    """合成数据生成器"""
    
    def __init__(self):
        self.synthesizer = None
        self.metadata = None
        
    def load_real_data(self, csv_path):
        """加载真实数据"""
        print("\n" + "=" * 80)
        print("加载真实数据")
        print("=" * 80)
        
        df = pd.read_csv(csv_path)
        print(f"✓ 数据加载成功: {df.shape}")
        
        # 准备训练数据（排除ID列）
        exclude_columns = ['区县', 'risk_level']  # 排除区县ID和计算的risk_level
        
        # 保留"按方案评定级别"作为目标
        train_df = df.drop(columns=exclude_columns)
        
        print(f"\n训练数据:")
        print(f"  样本数: {len(train_df)}")
        print(f"  特征数: {len(train_df.columns)}")
        
        # 显示目标变量分布
        if '按方案评定级别' in train_df.columns:
            print(f"\n目标变量分布:")
            for level in sorted(train_df['按方案评定级别'].unique()):
                count = (train_df['按方案评定级别'] == level).sum()
                pct = count / len(train_df) * 100
                print(f"  等级 {int(level)}: {count} 样本 ({pct:.1f}%)")
        
        return train_df
    
    def create_metadata(self, df):
        """创建数据元数据"""
        print("\n" + "=" * 80)
        print("创建元数据")
        print("=" * 80)
        
        # 自动检测元数据
        metadata = SingleTableMetadata()
        metadata.detect_from_dataframe(df)
        
        # 设置主键（如果需要）
        # metadata.set_primary_key('id')
        
        # 显示元数据信息
        print(f"\n✓ 元数据创建完成")
        print(f"  字段数: {len(metadata.columns)}")
        
        # 显示字段类型
        print(f"\n字段类型统计:")
        sdtypes = {}
        for col_name, col_info in metadata.columns.items():
            sdtype = col_info.get('sdtype', 'unknown')
            sdtypes[sdtype] = sdtypes.get(sdtype, 0) + 1
        
        for sdtype, count in sdtypes.items():
            print(f"  {sdtype}: {count} 个字段")
        
        self.metadata = metadata
        return metadata
    
    def train_ctgan(self, df, epochs=300, batch_size=500):
        """训练CTGAN模型"""
        print("\n" + "=" * 80)
        print("训练CTGAN模型")
        print("=" * 80)
        
        print(f"\n训练参数:")
        print(f"  Epochs: {epochs}")
        print(f"  Batch size: {batch_size}")
        print(f"  样本数: {len(df)}")
        
        # 创建CTGAN合成器
        self.synthesizer = CTGANSynthesizer(
            metadata=self.metadata,
            epochs=epochs,
            batch_size=batch_size,
            verbose=True
        )
        
        print(f"\n开始训练...")
        print(f"⏳ 这可能需要几分钟时间...")
        
        # 训练模型
        self.synthesizer.fit(df)
        
        print(f"\n✓ 训练完成")
        
    def generate_synthetic_data(self, n_samples):
        """生成合成数据"""
        print("\n" + "=" * 80)
        print("生成合成数据")
        print("=" * 80)
        
        print(f"\n生成 {n_samples} 个合成样本...")
        
        # 生成数据
        synthetic_df = self.synthesizer.sample(num_rows=n_samples)
        
        print(f"✓ 生成完成: {synthetic_df.shape}")
        
        # 显示合成数据的目标变量分布
        if '按方案评定级别' in synthetic_df.columns:
            print(f"\n合成数据目标变量分布:")
            for level in sorted(synthetic_df['按方案评定级别'].unique()):
                count = (synthetic_df['按方案评定级别'] == level).sum()
                pct = count / len(synthetic_df) * 100
                print(f"  等级 {int(level)}: {count} 样本 ({pct:.1f}%)")
        
        return synthetic_df
    
    def evaluate_quality(self, real_df, synthetic_df):
        """评估合成数据质量"""
        print("\n" + "=" * 80)
        print("评估合成数据质量")
        print("=" * 80)
        
        # 1. 统计特征对比
        print(f"\n1. 统计特征对比:")
        
        numeric_cols = real_df.select_dtypes(include=[np.number]).columns[:5]  # 只显示前5个
        
        print(f"\n{'字段':<30} {'真实均值':<15} {'合成均值':<15} {'差异':<10}")
        print("-" * 70)
        
        for col in numeric_cols:
            if col in synthetic_df.columns:
                real_mean = real_df[col].mean()
                synth_mean = synthetic_df[col].mean()
                diff = abs(real_mean - synth_mean) / (real_mean + 1e-10) * 100
                
                print(f"{col:<30} {real_mean:<15.2f} {synth_mean:<15.2f} {diff:<10.2f}%")
        
        # 2. 类别分布对比
        if '按方案评定级别' in real_df.columns and '按方案评定级别' in synthetic_df.columns:
            print(f"\n2. 目标变量分布对比:")
            print(f"{'等级':<10} {'真实数量':<15} {'合成数量':<15} {'真实比例':<15} {'合成比例':<15}")
            print("-" * 70)
            
            for level in sorted(real_df['按方案评定级别'].unique()):
                real_count = (real_df['按方案评定级别'] == level).sum()
                synth_count = (synthetic_df['按方案评定级别'] == level).sum()
                real_pct = real_count / len(real_df) * 100
                synth_pct = synth_count / len(synthetic_df) * 100
                
                print(f"{int(level):<10} {real_count:<15} {synth_count:<15} {real_pct:<15.1f}% {synth_pct:<15.1f}%")
        
        # 3. 数据范围检查
        print(f"\n3. 数据范围检查:")
        out_of_range = 0
        
        for col in numeric_cols:
            if col in synthetic_df.columns:
                real_min = real_df[col].min()
                real_max = real_df[col].max()
                synth_min = synthetic_df[col].min()
                synth_max = synthetic_df[col].max()
                
                if synth_min < real_min or synth_max > real_max:
                    out_of_range += 1
        
        if out_of_range == 0:
            print(f"  ✓ 所有字段的合成数据都在真实数据范围内")
        else:
            print(f"  ⚠️  {out_of_range} 个字段的合成数据超出真实数据范围")
    
    def save_synthetic_data(self, synthetic_df, output_path):
        """保存合成数据"""
        synthetic_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"\n✓ 合成数据已保存: {output_path}")
    
    def save_model(self, model_path):
        """保存训练好的模型"""
        self.synthesizer.save(model_path)
        print(f"✓ CTGAN模型已保存: {model_path}")


def create_mixed_dataset(real_df, synthetic_df, mix_ratio=0.5):
    """创建混合数据集（真实+合成）"""
    print("\n" + "=" * 80)
    print("创建混合数据集")
    print("=" * 80)
    
    n_real = int(len(real_df) * mix_ratio)
    n_synthetic = len(real_df) - n_real
    
    # 从真实数据中采样
    real_sample = real_df.sample(n=n_real, random_state=42)
    
    # 从合成数据中采样
    synthetic_sample = synthetic_df.sample(n=n_synthetic, random_state=42)
    
    # 合并
    mixed_df = pd.concat([real_sample, synthetic_sample], ignore_index=True)
    
    # 打乱顺序
    mixed_df = mixed_df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    print(f"\n混合数据集:")
    print(f"  真实数据: {n_real} 样本 ({mix_ratio*100:.0f}%)")
    print(f"  合成数据: {n_synthetic} 样本 ({(1-mix_ratio)*100:.0f}%)")
    print(f"  总计: {len(mixed_df)} 样本")
    
    return mixed_df


def main():
    """主流程"""
    print("\n" + "=" * 80)
    print("CTGAN 合成数据生成")
    print("=" * 80)
    
    # 初始化生成器
    generator = SyntheticDataGenerator()
    
    # 步骤1: 加载真实数据
    print("\n【步骤 1/6】加载真实数据")
    real_df = generator.load_real_data('data/processed/hiv_data_processed.csv')
    
    # 步骤2: 创建元数据
    print("\n【步骤 2/6】创建元数据")
    metadata = generator.create_metadata(real_df)
    
    # 步骤3: 训练CTGAN
    print("\n【步骤 3/6】训练CTGAN")
    generator.train_ctgan(real_df, epochs=300, batch_size=100)
    
    # 步骤4: 生成合成数据
    print("\n【步骤 4/6】生成合成数据")
    n_synthetic = 500  # 生成500个合成样本
    synthetic_df = generator.generate_synthetic_data(n_synthetic)
    
    # 步骤5: 评估质量
    print("\n【步骤 5/6】评估质量")
    generator.evaluate_quality(real_df, synthetic_df)
    
    # 步骤6: 保存数据和模型
    print("\n【步骤 6/6】保存数据")
    generator.save_synthetic_data(
        synthetic_df,
        'data/processed/hiv_synthetic_data.csv'
    )
    
    generator.save_model('saved_models/ctgan_model.pkl')
    
    # 额外：创建混合数据集
    print("\n【额外】创建混合数据集")
    
    # 方案1: 50%真实 + 50%合成
    mixed_50_50 = create_mixed_dataset(real_df, synthetic_df, mix_ratio=0.5)
    mixed_50_50.to_csv(
        'data/processed/hiv_mixed_50_50.csv',
        index=False,
        encoding='utf-8-sig'
    )
    print(f"✓ 混合数据集(50-50)已保存")
    
    # 方案2: 70%真实 + 30%合成
    mixed_70_30 = create_mixed_dataset(real_df, synthetic_df, mix_ratio=0.7)
    mixed_70_30.to_csv(
        'data/processed/hiv_mixed_70_30.csv',
        index=False,
        encoding='utf-8-sig'
    )
    print(f"✓ 混合数据集(70-30)已保存")
    
    print("\n" + "=" * 80)
    print("✓ 合成数据生成完成")
    print("=" * 80)
    
    print(f"\n生成的文件:")
    print(f"  1. data/processed/hiv_synthetic_data.csv - 纯合成数据({n_synthetic}样本)")
    print(f"  2. data/processed/hiv_mixed_50_50.csv - 混合数据(50%真实+50%合成)")
    print(f"  3. data/processed/hiv_mixed_70_30.csv - 混合数据(70%真实+30%合成)")
    print(f"  4. saved_models/ctgan_model.pkl - CTGAN模型")
    
    print(f"\n下一步建议:")
    print(f"  1. 使用混合数据集重新训练模型")
    print(f"  2. 对比不同数据集的模型性能")
    print(f"  3. 选择最佳数据集配置")
    
    return generator, real_df, synthetic_df


if __name__ == '__main__':
    generator, real_df, synthetic_df = main()
