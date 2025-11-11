#!/usr/bin/env python3
"""
风险因素相关性分析器
分析110个特征与风险等级之间的关联关系
"""

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr
from scipy.stats import chi2_contingency
from sklearn.feature_selection import mutual_info_regression
import warnings
warnings.filterwarnings('ignore')


class RiskFactorCorrelationAnalyzer:
    """
    风险因素相关性分析器
    
    功能：
    1. 分析特征与风险等级的相关性（Pearson, Spearman, 互信息）
    2. 验证已知的正负相关关系
    3. 探索未知特征的潜在关联
    4. 生成分析报告
    """
    
    def __init__(self, data_path='data/processed/hiv_data_processed.csv'):
        """
        初始化分析器
        
        Args:
            data_path: 训练数据路径
        """
        print(f"加载数据: {data_path}")
        self.df = pd.read_csv(data_path)
        
        # 提取特征和标签
        self.y = self.df['risk_level'].values  # 风险等级（1-5）
        
        # 排除非特征列
        exclude_cols = ['区县', 'risk_level', '按方案评定级别', 
                       '预测风险等级_5级', '置信度', '预测风险等级_3级', '风险描述']
        self.feature_columns = [col for col in self.df.columns if col not in exclude_cols]
        
        self.X = self.df[self.feature_columns].values
        self.feature_names = self.feature_columns
        
        print(f"✓ 数据加载完成")
        print(f"  样本数: {len(self.df)}")
        print(f"  特征数: {len(self.feature_columns)}")
        print(f"  风险等级分布: {dict(pd.Series(self.y).value_counts().sort_index())}")
        
        # 初始化特征映射
        self._init_feature_mapping()
    
    def _init_feature_mapping(self):
        """
        初始化特征名称映射
        需求文档中的特征名 → 模型中的特征名
        """
        # 已知正相关特征（13个）
        self.positive_features = {
            '报告感染率': '感染率',
            '存活数': '存活数',
            '年新报告数': '新报告',
            '商业性传播占比': '存活_商业性行为',  # 或 新报告_商业性行为
            '暗娼规模人数': '暗娼规模',
            '男同规模人数': '城市MSM规模',  # 可能需要合并农村MSM规模
            '吸毒人群规模数': '注射吸毒者规模',
            '挡获嫖客人次数': '挡获嫖客人次数',
            '既往阳性嫖客数': '既往阳性嫖客数',
            '嫖客HIV检测阳性率': '嫖客HIV检测阳性率',
            '挡获暗娼人次数': '挡获暗娼人次数',
            '既往阳性暗娼数': '既往阳性暗娼数',
            '暗娼HIV检测阳性率': '暗娼HIV检测阳性率'
        }
        
        # 已知负相关特征（16个）
        self.negative_features = {
            '治疗覆盖率': '治疗覆盖率',
            '治疗成功率': '病毒抑制比例',
            '暗娼年干预人数': '暗娼_月均干预人数',  # 需要×12转换
            '暗娼年首次检测数': '暗娼_HIV检测人数',
            'MSM年干预人数': 'MSM_月均干预人数',  # 需要×12转换
            'MSM年首次检测数': 'MSM_HIV检测人数',
            '吸毒年干预人数': '吸毒者_月均干预人数',  # 需要×12转换
            '吸毒年首次检测数': '吸毒者_HIV检测人数',
            '年检测人次数': '筛查人次数',
            '检测覆盖率': '筛查覆盖率',
            '年检测人数': '筛查人数',
            '人口检测比例': '按人数筛查覆盖率',
            '公安年打击次数': None,  # 需要合并：挡获暗娼人次数 + 挡获嫖客人次数
            '医疗机构数量': '医疗机构总数',
            '检测机构数量': '医疗机构总数',  # 近似
            '公卫医师数/千人': '每千人口卫生技术人员'
        }
        
        print(f"\n✓ 特征映射初始化完成")
        print(f"  已知正相关特征: {len(self.positive_features)}")
        print(f"  已知负相关特征: {len(self.negative_features)}")
    
    def analyze_correlations(self, method='all'):
        """
        多维度相关性分析
        
        Args:
            method: 分析方法
                - 'pearson': Pearson相关系数（线性关系）
                - 'spearman': Spearman相关系数（单调关系）
                - 'mutual_info': 互信息（非线性关系）
                - 'all': 所有方法
        
        Returns:
            dict: 每个特征的相关性分析结果
        """
        print(f"\n开始相关性分析...")
        print(f"  方法: {method}")
        
        results = {}
        
        for i, feature in enumerate(self.feature_names):
            if (i + 1) % 20 == 0:
                print(f"  进度: {i+1}/{len(self.feature_names)}")
            
            feature_values = self.X[:, i]
            
            # 跳过全零或常数特征
            if np.std(feature_values) == 0:
                results[feature] = {
                    'pearson_r': 0.0,
                    'pearson_p': 1.0,
                    'spearman_r': 0.0,
                    'spearman_p': 1.0,
                    'mutual_info': 0.0,
                    'correlation_type': 'constant',
                    'is_significant': False
                }
                continue
            
            result = {}
            
            # 1. Pearson相关系数（线性关系）
            if method in ['pearson', 'all']:
                try:
                    pearson_r, pearson_p = pearsonr(feature_values, self.y)
                    result['pearson_r'] = float(pearson_r)
                    result['pearson_p'] = float(pearson_p)
                except:
                    result['pearson_r'] = 0.0
                    result['pearson_p'] = 1.0
            
            # 2. Spearman相关系数（单调关系）
            if method in ['spearman', 'all']:
                try:
                    spearman_r, spearman_p = spearmanr(feature_values, self.y)
                    result['spearman_r'] = float(spearman_r)
                    result['spearman_p'] = float(spearman_p)
                except:
                    result['spearman_r'] = 0.0
                    result['spearman_p'] = 1.0
            
            # 3. 互信息（非线性关系）
            if method in ['mutual_info', 'all']:
                try:
                    mi_score = mutual_info_regression(
                        feature_values.reshape(-1, 1), 
                        self.y,
                        random_state=42
                    )[0]
                    result['mutual_info'] = float(mi_score)
                except:
                    result['mutual_info'] = 0.0
            
            # 分类相关性类型
            if 'pearson_r' in result and 'pearson_p' in result:
                result['correlation_type'] = self._classify_correlation(
                    result['pearson_r'], 
                    result['pearson_p']
                )
                result['is_significant'] = result['pearson_p'] < 0.05
            
            results[feature] = result
        
        print(f"✓ 相关性分析完成")
        print(f"  分析特征数: {len(results)}")
        
        return results
    
    def _classify_correlation(self, r, p):
        """
        分类相关性类型
        
        Args:
            r: 相关系数
            p: p值
        
        Returns:
            str: 相关性类型
        """
        if p > 0.05:
            return 'not_significant'
        elif r > 0.3:
            return 'positive_strong'
        elif r > 0.1:
            return 'positive_moderate'
        elif r > 0:
            return 'positive_weak'
        elif r < -0.3:
            return 'negative_strong'
        elif r < -0.1:
            return 'negative_moderate'
        elif r < 0:
            return 'negative_weak'
        else:
            return 'negligible'
    
    def verify_known_correlations(self, correlation_results=None):
        """
        验证已知的正负相关关系
        
        Args:
            correlation_results: 相关性分析结果（如果为None则重新计算）
        
        Returns:
            dict: 验证结果
        """
        if correlation_results is None:
            correlation_results = self.analyze_correlations()
        
        print(f"\n开始验证已知关联...")
        
        verification = {
            'positive_verified': [],
            'positive_failed': [],
            'negative_verified': [],
            'negative_failed': [],
            'details': {}
        }
        
        # 验证正相关特征
        print(f"\n验证正相关特征（预期: r > 0）:")
        for req_name, model_name in self.positive_features.items():
            if model_name and model_name in correlation_results:
                result = correlation_results[model_name]
                r = result.get('pearson_r', 0)
                p = result.get('pearson_p', 1)
                
                # 判断是否验证通过
                if r > 0 and p < 0.05:
                    verification['positive_verified'].append(req_name)
                    status = "✓"
                else:
                    verification['positive_failed'].append({
                        'feature': req_name,
                        'model_feature': model_name,
                        'expected': 'positive',
                        'actual_r': r,
                        'p_value': p
                    })
                    status = "✗"
                
                print(f"  {status} {req_name:20s} (r={r:+.3f}, p={p:.4f})")
                verification['details'][req_name] = result
        
        # 验证负相关特征
        print(f"\n验证负相关特征（预期: r < 0）:")
        for req_name, model_name in self.negative_features.items():
            if model_name and model_name in correlation_results:
                result = correlation_results[model_name]
                r = result.get('pearson_r', 0)
                p = result.get('pearson_p', 1)
                
                # 判断是否验证通过
                if r < 0 and p < 0.05:
                    verification['negative_verified'].append(req_name)
                    status = "✓"
                else:
                    verification['negative_failed'].append({
                        'feature': req_name,
                        'model_feature': model_name,
                        'expected': 'negative',
                        'actual_r': r,
                        'p_value': p
                    })
                    status = "✗"
                
                print(f"  {status} {req_name:20s} (r={r:+.3f}, p={p:.4f})")
                verification['details'][req_name] = result
        
        # 统计结果
        total_positive = len(self.positive_features)
        verified_positive = len(verification['positive_verified'])
        total_negative = len(self.negative_features)
        verified_negative = len(verification['negative_verified'])
        
        print(f"\n验证结果汇总:")
        print(f"  正相关特征: {verified_positive}/{total_positive} 通过 ({verified_positive/total_positive*100:.1f}%)")
        print(f"  负相关特征: {verified_negative}/{total_negative} 通过 ({verified_negative/total_negative*100:.1f}%)")
        print(f"  总体通过率: {(verified_positive+verified_negative)/(total_positive+total_negative)*100:.1f}%")
        
        return verification
    
    def get_top_correlations(self, correlation_results, top_k=20, abs_value=True):
        """
        获取Top K个相关性最强的特征
        
        Args:
            correlation_results: 相关性分析结果
            top_k: 返回Top K个
            abs_value: 是否按绝对值排序
        
        Returns:
            list: Top K特征列表
        """
        # 提取相关系数
        correlations = []
        for feature, result in correlation_results.items():
            r = result.get('pearson_r', 0)
            p = result.get('pearson_p', 1)
            if p < 0.05:  # 只考虑显著的
                correlations.append({
                    'feature': feature,
                    'pearson_r': r,
                    'pearson_p': p,
                    'abs_r': abs(r),
                    'correlation_type': result.get('correlation_type', 'unknown')
                })
        
        # 排序
        if abs_value:
            correlations.sort(key=lambda x: x['abs_r'], reverse=True)
        else:
            correlations.sort(key=lambda x: x['pearson_r'], reverse=True)
        
        return correlations[:top_k]
    
    def explore_unknown_features(self, correlation_results):
        """
        探索未知特征的关联关系
        
        Args:
            correlation_results: 相关性分析结果
        
        Returns:
            dict: 未知特征的分析结果
        """
        print(f"\n探索未知特征关联...")
        
        # 获取已知特征列表
        known_features = set(self.positive_features.values()) | set(self.negative_features.values())
        known_features.discard(None)
        
        # 找出未知特征
        unknown_features = [f for f in self.feature_names if f not in known_features]
        
        print(f"  未知特征数: {len(unknown_features)}")
        
        # 分析未知特征
        unknown_results = {}
        significant_unknown = []
        
        for feature in unknown_features:
            if feature in correlation_results:
                result = correlation_results[feature]
                unknown_results[feature] = result
                
                # 识别显著相关的未知特征
                if result.get('is_significant', False):
                    significant_unknown.append({
                        'feature': feature,
                        'pearson_r': result['pearson_r'],
                        'pearson_p': result['pearson_p'],
                        'correlation_type': result['correlation_type']
                    })
        
        # 按相关性强度排序
        significant_unknown.sort(key=lambda x: abs(x['pearson_r']), reverse=True)
        
        print(f"  显著相关的未知特征: {len(significant_unknown)}")
        
        if significant_unknown:
            print(f"\n  Top 10 显著未知特征:")
            for i, item in enumerate(significant_unknown[:10], 1):
                print(f"    {i}. {item['feature']:30s} r={item['pearson_r']:+.3f} (p={item['pearson_p']:.4f})")
        
        return {
            'total_unknown': len(unknown_features),
            'significant_count': len(significant_unknown),
            'significant_features': significant_unknown,
            'all_results': unknown_results
        }
    
    def generate_summary(self, correlation_results, verification_results, unknown_results):
        """
        生成分析摘要
        
        Returns:
            dict: 分析摘要
        """
        summary = {
            'dataset_info': {
                'samples': len(self.df),
                'features': len(self.feature_names),
                'risk_levels': list(np.unique(self.y))
            },
            'known_correlations': {
                'positive_total': len(self.positive_features),
                'positive_verified': len(verification_results['positive_verified']),
                'negative_total': len(self.negative_features),
                'negative_verified': len(verification_results['negative_verified'])
            },
            'unknown_features': {
                'total': unknown_results['total_unknown'],
                'significant': unknown_results['significant_count']
            },
            'top_correlations': self.get_top_correlations(correlation_results, top_k=20)
        }
        
        return summary


def main():
    """
    演示相关性分析器的使用
    """
    print("="*80)
    print("  HIV风险因素相关性分析器 - 演示")
    print("="*80)
    
    # 1. 初始化分析器
    analyzer = RiskFactorCorrelationAnalyzer('data/processed/hiv_data_processed.csv')
    
    # 2. 执行相关性分析
    print("\n" + "="*80)
    print("  步骤1: 多维度相关性分析")
    print("="*80)
    correlation_results = analyzer.analyze_correlations(method='all')
    
    # 3. 验证已知关联
    print("\n" + "="*80)
    print("  步骤2: 验证已知正负相关关系")
    print("="*80)
    verification_results = analyzer.verify_known_correlations(correlation_results)
    
    # 4. 探索未知特征
    print("\n" + "="*80)
    print("  步骤3: 探索未知特征关联")
    print("="*80)
    unknown_results = analyzer.explore_unknown_features(correlation_results)
    
    # 5. 生成摘要
    print("\n" + "="*80)
    print("  步骤4: 生成分析摘要")
    print("="*80)
    summary = analyzer.generate_summary(correlation_results, verification_results, unknown_results)
    
    print(f"\n数据集信息:")
    print(f"  样本数: {summary['dataset_info']['samples']}")
    print(f"  特征数: {summary['dataset_info']['features']}")
    print(f"  风险等级: {summary['dataset_info']['risk_levels']}")
    
    print(f"\n已知关联验证:")
    print(f"  正相关: {summary['known_correlations']['positive_verified']}/{summary['known_correlations']['positive_total']} 通过")
    print(f"  负相关: {summary['known_correlations']['negative_verified']}/{summary['known_correlations']['negative_total']} 通过")
    
    print(f"\n未知特征探索:")
    print(f"  未知特征总数: {summary['unknown_features']['total']}")
    print(f"  显著相关: {summary['unknown_features']['significant']}")
    
    print(f"\nTop 10 相关性最强特征:")
    for i, item in enumerate(summary['top_correlations'][:10], 1):
        print(f"  {i}. {item['feature']:30s} r={item['pearson_r']:+.3f} ({item['correlation_type']})")
    
    print("\n" + "="*80)
    print("✓ 分析完成")
    print("="*80)
    
    return analyzer, correlation_results, verification_results, unknown_results


if __name__ == '__main__':
    analyzer, correlation_results, verification_results, unknown_results = main()
