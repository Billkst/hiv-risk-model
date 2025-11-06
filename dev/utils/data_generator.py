"""
HIV Risk Assessment - Mock Data Generator
根据合作方提供的字段结构生成模拟数据
"""

import numpy as np
import pandas as pd
import json
from datetime import datetime
import os


class HIVDataGenerator:
    """HIV 风险评估模拟数据生成器"""
    
    def __init__(self, n_regions=200, data_year=2024, random_seed=42):
        """
        Args:
            n_regions: 生成的区县数量
            data_year: 数据年份
            random_seed: 随机种子
        """
        self.n_regions = n_regions
        self.data_year = data_year
        np.random.seed(random_seed)
        
        # 中国区县名称示例（简化）
        self.region_names = self._generate_region_names()
    
    def _generate_region_names(self):
        """生成区县名称"""
        provinces = ['北京市', '上海市', '广东省', '浙江省', '江苏省', 
                    '四川省', '湖北省', '河南省', '山东省', '湖南省']
        districts = ['朝阳区', '海淀区', '浦东新区', '黄浦区', '天河区',
                    '越秀区', '武侯区', '锦江区', '江汉区', '武昌区']
        
        names = []
        for i in range(self.n_regions):
            province = np.random.choice(provinces)
            district = np.random.choice(districts)
            names.append(f"{province}{district}")
        
        return names
    
    def generate_complete_dataset(self):
        """生成完整的数据集"""
        
        data_list = []
        
        for i in range(self.n_regions):
            region_data = self._generate_single_region(i)
            data_list.append(region_data)
        
        # 转换为 DataFrame
        df = self._flatten_to_dataframe(data_list)
        
        # 生成风险等级标签
        df = self._generate_risk_labels(df)
        
        return df, data_list
    
    def _generate_single_region(self, idx):
        """生成单个区县的数据"""
        
        # 基础人口规模（影响其他指标）
        population = np.random.randint(100000, 5000000)
        
        # 经济水平（影响医疗资源和防控能力）
        gdp_per_capita = np.random.uniform(30000, 200000)
        urbanization = np.random.uniform(0.3, 0.95)
        
        # 根据经济水平调整其他指标
        economic_factor = gdp_per_capita / 100000  # 归一化
        
        data = {
            # ========== 元数据 ==========
            "region_id": f"CN{idx:04d}",
            "region_name": self.region_names[idx],
            "data_year": self.data_year,
            "data_date": f"{self.data_year}-12-31",
            
            # ========== 人口数据 ==========
            "population_total": population,
            "outflow_ratio": np.random.uniform(0.05, 0.30),
            "inflow_ratio": np.random.uniform(0.05, 0.35),
            "elderly_burden_index": np.random.uniform(0.10, 0.40),
            
            # ========== 报告存活病例 ==========
            "survival_total": int(population * np.random.uniform(0.0001, 0.001)),
            "prevalence_rate": np.random.uniform(0.0001, 0.001),
            
            # 年龄分布（存活）
            "survival_age_0_14": 0,
            "survival_age_15_19": 0,
            "survival_age_20_24": 0,
            "survival_age_25_29": 0,
            "survival_age_30_34": 0,
            "survival_age_35_39": 0,
            "survival_age_40_44": 0,
            "survival_age_45_49": 0,
            "survival_age_50_54": 0,
            "survival_age_55_59": 0,
            "survival_age_60_64": 0,
            "survival_age_65_69": 0,
            "survival_age_70_plus": 0,
            
            # 传播途径（存活）
            "survival_injection_drug_ratio": np.random.uniform(0.01, 0.15),
            "survival_heterosexual_ratio": np.random.uniform(0.30, 0.60),
            "survival_homosexual_ratio": np.random.uniform(0.20, 0.50),
            "survival_mother_to_child_ratio": np.random.uniform(0.005, 0.03),
            "survival_other_unknown_ratio": np.random.uniform(0.05, 0.20),
            
            # ========== 年新报告病例 ==========
            "new_cases_total": int(population * np.random.uniform(0.00001, 0.0002)),
            
            # 年龄分布（新报告）
            "new_age_0_14": 0,
            "new_age_15_19": 0,
            "new_age_20_24": 0,
            "new_age_25_29": 0,
            "new_age_30_34": 0,
            "new_age_35_39": 0,
            "new_age_40_44": 0,
            "new_age_45_49": 0,
            "new_age_50_54": 0,
            "new_age_55_59": 0,
            "new_age_60_64": 0,
            "new_age_65_69": 0,
            "new_age_70_plus": 0,
            
            # 传播途径（新报告）
            "new_injection_drug_ratio": np.random.uniform(0.005, 0.10),
            "new_heterosexual_ratio": np.random.uniform(0.30, 0.60),
            "new_heterosexual_spouse_ratio": np.random.uniform(0.10, 0.25),
            "new_heterosexual_commercial_ratio": np.random.uniform(0.10, 0.30),
            "new_heterosexual_non_marital_ratio": np.random.uniform(0.05, 0.20),
            "new_homosexual_ratio": np.random.uniform(0.25, 0.55),
            "new_mother_to_child_ratio": np.random.uniform(0.002, 0.02),
            "new_other_unknown_ratio": np.random.uniform(0.05, 0.15),
            
            # ========== 治疗数据 ==========
            "treatment_coverage_rate": np.random.uniform(0.70, 0.98) * economic_factor,
            "treatment_success_rate": np.random.uniform(0.75, 0.95) * economic_factor,
            
            # ========== 高危人群干预 ==========
            "fsw_estimated_size": int(population * np.random.uniform(0.0005, 0.003)),
            "fsw_intervention_count": 0,
            "fsw_first_test_count": 0,
            
            "msm_estimated_size": int(population * np.random.uniform(0.001, 0.01)),
            "msm_intervention_count": 0,
            "msm_first_test_count": 0,
            
            "pwid_estimated_size": int(population * np.random.uniform(0.0001, 0.001)),
            "pwid_intervention_count": 0,
            "pwid_first_test_count": 0,
            
            # ========== 公众检测 ==========
            "test_person_times": int(population * np.random.uniform(0.05, 0.20)),
            "test_persons": int(population * np.random.uniform(0.04, 0.18)),
            "testing_coverage_rate": np.random.uniform(0.05, 0.25) * economic_factor,
            "population_test_ratio": np.random.uniform(0.04, 0.18),
            
            # ========== 公安执法 ==========
            "law_crackdown_count": int(np.random.uniform(10, 200)),
            "clients_caught_count": int(np.random.uniform(50, 1000)),
            "clients_previous_positive": int(np.random.uniform(0, 20)),
            "clients_hiv_positive_rate": np.random.uniform(0.005, 0.05),
            "fsw_caught_count": int(np.random.uniform(30, 500)),
            "fsw_previous_positive": int(np.random.uniform(0, 30)),
            "fsw_hiv_positive_rate": np.random.uniform(0.01, 0.08),
            
            # ========== 经济数据 ==========
            "gdp_per_capita": gdp_per_capita,
            "urbanization_rate": urbanization,
            
            # ========== 医疗卫生资源 ==========
            "medical_institutions": int(population / np.random.uniform(5000, 20000)),
            "testing_institutions": int(population / np.random.uniform(20000, 100000)),
            "public_health_doctors_per_1000": np.random.uniform(0.5, 5.0) * economic_factor,
        }
        
        # 计算高危人群干预数（基于规模）
        data["fsw_intervention_count"] = int(data["fsw_estimated_size"] * np.random.uniform(0.4, 0.9))
        data["fsw_first_test_count"] = int(data["fsw_intervention_count"] * np.random.uniform(0.6, 0.95))
        
        data["msm_intervention_count"] = int(data["msm_estimated_size"] * np.random.uniform(0.3, 0.8))
        data["msm_first_test_count"] = int(data["msm_intervention_count"] * np.random.uniform(0.6, 0.95))
        
        data["pwid_intervention_count"] = int(data["pwid_estimated_size"] * np.random.uniform(0.5, 0.95))
        data["pwid_first_test_count"] = int(data["pwid_intervention_count"] * np.random.uniform(0.7, 0.98))
        
        # 分配年龄结构（存活病例）
        data = self._distribute_age_structure(data, "survival")
        
        # 分配年龄结构（新报告病例）
        data = self._distribute_age_structure(data, "new")
        
        return data
    
    def _distribute_age_structure(self, data, prefix):
        """分配年龄结构"""
        total_key = f"{prefix}_total" if prefix == "survival" else "new_cases_total"
        total = data[total_key]
        
        # 年龄分布权重（20-49岁为主）
        age_weights = np.array([
            0.005,  # <15
            0.01,   # 15-19
            0.08,   # 20-24
            0.15,   # 25-29
            0.18,   # 30-34
            0.16,   # 35-39
            0.14,   # 40-44
            0.12,   # 45-49
            0.08,   # 50-54
            0.05,   # 55-59
            0.03,   # 60-64
            0.02,   # 65-69
            0.01    # 70+
        ])
        
        # 添加随机扰动
        age_weights = age_weights * np.random.uniform(0.7, 1.3, len(age_weights))
        age_weights = age_weights / age_weights.sum()
        
        # 分配到各年龄段
        age_groups = [
            "0_14", "15_19", "20_24", "25_29", "30_34", "35_39",
            "40_44", "45_49", "50_54", "55_59", "60_64", "65_69", "70_plus"
        ]
        
        for i, age_group in enumerate(age_groups):
            key = f"{prefix}_age_{age_group}"
            data[key] = int(total * age_weights[i])
        
        return data
    
    def _flatten_to_dataframe(self, data_list):
        """将嵌套数据展平为 DataFrame"""
        return pd.DataFrame(data_list)
    
    def _generate_risk_labels(self, df):
        """
        生成风险等级标签（1-5）
        基于多个指标的综合评分
        """
        
        # 标准化各指标到 0-1
        df_norm = df.copy()
        
        # 疾病指标（权重：40%）
        disease_score = (
            0.4 * self._normalize(df['prevalence_rate']) +
            0.3 * self._normalize(df['new_cases_total'] / df['population_total']) +
            0.3 * self._normalize(df['survival_homosexual_ratio'])  # 高风险传播途径
        )
        
        # 防控指标（权重：30%，反向）
        prevention_score = 1 - (
            0.4 * self._normalize(df['treatment_coverage_rate']) +
            0.3 * self._normalize(df['testing_coverage_rate']) +
            0.3 * self._normalize(df['fsw_intervention_count'] / (df['fsw_estimated_size'] + 1))
        )
        
        # 资源指标（权重：20%，反向）
        resource_score = 1 - (
            0.4 * self._normalize(df['public_health_doctors_per_1000']) +
            0.3 * self._normalize(df['medical_institutions'] / (df['population_total'] / 100000)) +
            0.3 * self._normalize(df['testing_institutions'] / (df['population_total'] / 100000))
        )
        
        # 社会经济指标（权重：10%，反向）
        socioeconomic_score = 1 - (
            0.5 * self._normalize(df['gdp_per_capita']) +
            0.5 * self._normalize(df['urbanization_rate'])
        )
        
        # 综合评分
        total_score = (
            0.40 * disease_score +
            0.30 * prevention_score +
            0.20 * resource_score +
            0.10 * socioeconomic_score
        )
        
        # 转换为 1-5 等级
        df['risk_score'] = total_score
        df['risk_level'] = pd.cut(
            total_score,
            bins=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
            labels=[1, 2, 3, 4, 5],
            include_lowest=True
        ).astype(int)
        
        return df
    
    def _normalize(self, series):
        """Min-Max 标准化到 0-1"""
        min_val = series.min()
        max_val = series.max()
        if max_val == min_val:
            return pd.Series(np.zeros(len(series)))
        return (series - min_val) / (max_val - min_val)
    
    def save_data(self, df, data_list, output_dir='data/mock'):
        """保存数据"""
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存 CSV（用于模型训练）
        csv_path = os.path.join(output_dir, f'hiv_risk_data_{self.data_year}.csv')
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"✓ CSV 数据已保存: {csv_path}")
        
        # 保存 JSON（用于 API 测试）
        json_path = os.path.join(output_dir, f'hiv_risk_data_{self.data_year}.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data_list, f, ensure_ascii=False, indent=2)
        print(f"✓ JSON 数据已保存: {json_path}")
        
        # 保存数据统计
        stats = self._generate_statistics(df)
        stats_path = os.path.join(output_dir, 'data_statistics.txt')
        with open(stats_path, 'w', encoding='utf-8') as f:
            f.write(stats)
        print(f"✓ 数据统计已保存: {stats_path}")
        
        return csv_path, json_path
    
    def _generate_statistics(self, df):
        """生成数据统计信息"""
        stats = f"""
HIV 风险评估模拟数据统计
{'='*60}

数据概况:
- 区县数量: {len(df)}
- 数据年份: {self.data_year}
- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

风险等级分布:
{df['risk_level'].value_counts().sort_index().to_string()}

关键指标统计:
- 平均流行率: {df['prevalence_rate'].mean():.6f}
- 平均治疗覆盖率: {df['treatment_coverage_rate'].mean():.2%}
- 平均检测覆盖率: {df['testing_coverage_rate'].mean():.2%}
- 平均人均GDP: {df['gdp_per_capita'].mean():.0f} 元

人口规模分布:
- 最小: {df['population_total'].min():,}
- 最大: {df['population_total'].max():,}
- 平均: {df['population_total'].mean():,.0f}

{'='*60}
"""
        return stats


def main():
    """主函数"""
    print("="*60)
    print("HIV 风险评估模拟数据生成器")
    print("="*60)
    print()
    
    # 创建生成器
    generator = HIVDataGenerator(
        n_regions=200,  # 生成200个区县的数据
        data_year=2024,
        random_seed=42
    )
    
    print("正在生成数据...")
    df, data_list = generator.generate_complete_dataset()
    
    print(f"✓ 生成完成: {len(df)} 条记录")
    print()
    
    # 保存数据
    print("正在保存数据...")
    csv_path, json_path = generator.save_data(df, data_list)
    
    print()
    print("="*60)
    print("数据生成完成！")
    print("="*60)
    print()
    print(f"CSV 文件: {csv_path}")
    print(f"JSON 文件: {json_path}")
    print()
    print("下一步: 运行 python models/model_trainer.py 训练模型")
    print()


if __name__ == '__main__':
    main()
