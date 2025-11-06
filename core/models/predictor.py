"""
预测接口
加载训练好的模型进行预测
"""

import numpy as np
import pandas as pd
import joblib
import os


class HIVRiskPredictor:
    """HIV 风险预测器"""
    
    def __init__(self, model_path='saved_models/final_model_3to5.pkl', 
                 enable_contributions=True):
        """
        加载模型
        
        Args:
            model_path: 模型文件路径
            enable_contributions: 是否启用特征贡献度分析（默认True）
        """
        print(f"加载模型: {model_path}")
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"模型文件不存在: {model_path}")
        
        model_info = joblib.load(model_path)
        
        self.model = model_info['model']
        self.scaler = model_info['scaler']
        self.model_name = model_info['model_name']
        self.feature_columns = model_info['feature_columns']
        self.infection_rate_idx = model_info.get('infection_rate_idx')
        
        # 初始化特征贡献度分析器
        self.enable_contributions = enable_contributions
        self.contribution_analyzer = None
        
        if enable_contributions:
            try:
                # 尝试不同的导入路径
                try:
                    from models.feature_contribution_fast import FastFeatureContributionAnalyzer
                except ImportError:
                    from feature_contribution_fast import FastFeatureContributionAnalyzer
                
                # 使用空数据初始化（不需要训练数据）
                self.contribution_analyzer = FastFeatureContributionAnalyzer(
                    self.model, 
                    self.feature_columns,
                    X_train=None
                )
                print(f"✓ 特征贡献度分析器已启用")
            except Exception as e:
                print(f"⚠️  特征贡献度分析器初始化失败: {e}")
                self.enable_contributions = False
        
        print(f"✓ 模型加载成功")
        print(f"  模型类型: {self.model_name}")
        print(f"  特征数: {len(self.feature_columns)}")
        print(f"  特征贡献度: {'启用' if self.enable_contributions else '禁用'}")
    
    def predict(self, X, return_details=False):
        """
        预测风险等级
        
        Args:
            X: 特征矩阵 (numpy array 或 pandas DataFrame)
            return_details: 是否返回详细信息
        
        Returns:
            如果 return_details=False: 返回5级预测结果
            如果 return_details=True: 返回字典，包含5级预测、风险分数、置信度、3级预测、概率分布
        """
        # 转换为 numpy array
        if isinstance(X, pd.DataFrame):
            X = X.values
        
        # 标准化
        X_scaled = self.scaler.transform(X)
        
        # 3级预测
        y_pred_3 = self.model.predict(X_scaled)
        y_proba = self.model.predict_proba(X_scaled)
        
        # 映射到5级（包含风险分数）
        y_pred_5, confidence, risk_scores = self._map_3_to_5_levels(y_pred_3, y_proba, X)
        
        if return_details:
            return {
                'risk_level_5': y_pred_5,
                'risk_scores': risk_scores,
                'confidence': confidence,
                'risk_level_3': y_pred_3,
                'probabilities': y_proba
            }
        else:
            return y_pred_5
    
    def predict_single(self, features_dict, include_contributions=False):
        """
        预测单个样本
        
        Args:
            features_dict: 特征字典，键为特征名，值为特征值
            include_contributions: 是否包含特征贡献度分析（默认False，向后兼容）
        
        Returns:
            预测结果字典
        """
        # 构建特征向量
        X = np.zeros((1, len(self.feature_columns)))
        
        for i, col in enumerate(self.feature_columns):
            if col in features_dict:
                X[0, i] = features_dict[col]
            else:
                print(f"⚠️  缺少特征: {col}，使用默认值 0")
        
        # 预测
        result = self.predict(X, return_details=True)
        
        # 格式化输出
        risk_level_5 = int(result['risk_level_5'][0])
        risk_score = float(result['risk_scores'][0])
        confidence = float(result['confidence'][0])
        risk_level_3 = int(result['risk_level_3'][0])
        proba = result['probabilities'][0]
        
        # 风险等级描述
        risk_descriptions = {
            1: "极低风险",
            2: "低风险",
            3: "中等风险",
            4: "高风险",
            5: "极高风险"
        }
        
        output = {
            'risk_level_5': risk_level_5,
            'risk_description': risk_descriptions[risk_level_5],
            'risk_score': risk_score,
            'confidence': confidence,
            'confidence_percent': f"{confidence*100:.2f}%",
            'risk_level_3': risk_level_3,
            'probabilities_3level': {
                '等级1': float(proba[0]),
                '等级2': float(proba[1]),
                '等级3': float(proba[2])
            }
        }
        
        # 添加特征贡献度分析（如果启用）
        if include_contributions and self.enable_contributions and self.contribution_analyzer:
            try:
                contrib_result = self.contribution_analyzer.explain_single(X, top_k=10)
                output['feature_contributions'] = self.contribution_analyzer.format_for_api(
                    contrib_result, 
                    top_k=5
                )
            except Exception as e:
                print(f"⚠️  特征贡献度计算失败: {e}")
                output['feature_contributions'] = None
        
        return output
    
    def _map_3_to_5_levels(self, y_pred_3level, y_proba, X_original=None):
        """将3级预测映射到5级，并计算风险分数"""
        n_samples = len(y_pred_3level)
        y_pred_5level = np.zeros(n_samples, dtype=int)
        confidence = np.zeros(n_samples)
        risk_scores = np.zeros(n_samples)
        
        for i in range(n_samples):
            pred_class = int(y_pred_3level[i])
            prob = y_proba[i]
            max_prob = prob[pred_class - 1]
            
            # 获取感染率（用于辅助判断）
            infection_rate = None
            if X_original is not None and self.infection_rate_idx is not None:
                infection_rate = X_original[i, self.infection_rate_idx]
            
            # 计算连续风险分数（0-100）
            # 使用概率分布计算期望值，然后映射到0-100分
            # P(低风险) * 10 + P(中风险) * 50 + P(高风险) * 90
            base_score = prob[0] * 10 + prob[1] * 50 + prob[2] * 90
            
            # 添加基于感染率的调整
            if infection_rate is not None:
                # 感染率越高，分数越高
                infection_adjustment = min(15, infection_rate * 20)  # 最多增加15分
                base_score += infection_adjustment
            
            # 添加基于置信度的微调
            # 置信度越低，分数越接近中间值50
            confidence_factor = max_prob
            base_score = base_score * confidence_factor + 50 * (1 - confidence_factor)
            
            # 确保分数在0-100范围内
            base_score = np.clip(base_score, 0, 100)
            
            # 根据连续分数直接映射到5级（这是关键改变！）
            if base_score < 20:
                y_pred_5level[i] = 1  # 极低风险 (0-20分)
            elif base_score < 40:
                y_pred_5level[i] = 2  # 低风险 (20-40分)
            elif base_score < 60:
                y_pred_5level[i] = 3  # 中等风险 (40-60分)
            elif base_score < 80:
                y_pred_5level[i] = 4  # 高风险 (60-80分)
            else:
                y_pred_5level[i] = 5  # 极高风险 (80-100分)
            
            # 保存分数和置信度
            risk_scores[i] = base_score
            confidence[i] = max_prob
        
        return y_pred_5level, confidence, risk_scores
    
    def get_feature_importance(self, top_k=20):
        """
        获取全局特征重要性
        
        Args:
            top_k: 返回Top K个最重要的特征（默认20）
        
        Returns:
            特征重要性列表
        """
        if not self.enable_contributions or not self.contribution_analyzer:
            print("⚠️  特征贡献度分析器未启用")
            return None
        
        try:
            importance = self.contribution_analyzer.get_global_importance()
            return importance[:top_k]
        except Exception as e:
            print(f"⚠️  获取特征重要性失败: {e}")
            return None
    
    def batch_predict_from_csv(self, csv_path, output_path=None):
        """
        从CSV文件批量预测
        
        Args:
            csv_path: 输入CSV文件路径
            output_path: 输出CSV文件路径（可选）
        
        Returns:
            包含预测结果的DataFrame
        """
        print(f"\n批量预测: {csv_path}")
        
        # 读取数据
        df = pd.read_csv(csv_path)
        print(f"✓ 读取 {len(df)} 个样本")
        
        # 提取特征
        X = df[self.feature_columns].values
        
        # 预测
        result = self.predict(X, return_details=True)
        
        # 添加预测结果到DataFrame
        df['预测风险等级_5级'] = result['risk_level_5']
        df['风险分数'] = np.round(result['risk_scores'], 2)  # 保留2位小数
        df['置信度'] = np.round(result['confidence'], 4)
        df['预测风险等级_3级'] = result['risk_level_3']
        
        # 添加风险描述
        risk_descriptions = {
            1: "极低风险",
            2: "低风险",
            3: "中等风险",
            4: "高风险",
            5: "极高风险"
        }
        df['风险描述'] = df['预测风险等级_5级'].map(risk_descriptions)
        
        # 保存结果
        if output_path:
            df.to_csv(output_path, index=False, encoding='utf-8-sig')
            print(f"✓ 预测结果已保存: {output_path}")
        
        # 统计
        print(f"\n预测结果统计（5级风险划分）:")
        print("=" * 70)
        for level in range(1, 6):
            if level in df['预测风险等级_5级'].values:
                count = (df['预测风险等级_5级'] == level).sum()
                pct = count / len(df) * 100
                desc = risk_descriptions[level]
                score_range = df[df['预测风险等级_5级'] == level]['风险分数']
                min_score = score_range.min()
                max_score = score_range.max()
                avg_score = score_range.mean()
                print(f"  等级{level} - {desc:8s}: {count:3d} 个区县 ({pct:5.1f}%)")
                print(f"           风险分数范围: {min_score:5.2f} - {max_score:5.2f} (平均: {avg_score:5.2f})")
            else:
                desc = risk_descriptions[level]
                print(f"  等级{level} - {desc:8s}: 0 个区县 (0.0%)")
        print("=" * 70)
        
        return df


def demo():
    """演示预测功能"""
    print("\n" + "=" * 80)
    print("HIV 风险预测演示")
    print("=" * 80)
    
    # 加载预测器
    predictor = HIVRiskPredictor()
    
    # 示例1: 批量预测
    print("\n" + "=" * 80)
    print("示例1: 批量预测")
    print("=" * 80)
    
    df_result = predictor.batch_predict_from_csv(
        'data/processed/hiv_data_processed.csv',
        'data/processed/hiv_predictions.csv'
    )
    
    # 显示前10个预测结果
    print(f"\n前10个预测结果:")
    cols_to_show = ['预测风险等级_5级', '风险描述', '置信度', '预测风险等级_3级']
    print(df_result[cols_to_show].head(10).to_string(index=False))
    
    # 示例2: 单个样本预测（不含特征贡献度）
    print("\n" + "=" * 80)
    print("示例2: 单个样本预测（基础版）")
    print("=" * 80)
    
    # 构建示例特征
    sample_features = {col: 0 for col in predictor.feature_columns}
    sample_features['存活数'] = 1000
    sample_features['感染率'] = 0.5
    sample_features['治疗覆盖率'] = 85.0
    
    result = predictor.predict_single(sample_features, include_contributions=False)
    
    print(f"\n预测结果:")
    print(f"  5级风险等级: {result['risk_level_5']} - {result['risk_description']}")
    print(f"  风险分数: {result['risk_score']:.2f}")
    print(f"  置信度: {result['confidence_percent']}")
    print(f"  3级风险等级: {result['risk_level_3']}")
    print(f"  3级概率分布:")
    for level, prob in result['probabilities_3level'].items():
        print(f"    {level}: {prob:.4f}")
    
    # 示例3: 单个样本预测（含特征贡献度）
    print("\n" + "=" * 80)
    print("示例3: 单个样本预测（增强版 - 含特征贡献度）")
    print("=" * 80)
    
    result_enhanced = predictor.predict_single(sample_features, include_contributions=True)
    
    print(f"\n预测结果:")
    print(f"  5级风险等级: {result_enhanced['risk_level_5']} - {result_enhanced['risk_description']}")
    print(f"  风险分数: {result_enhanced['risk_score']:.2f}")
    print(f"  置信度: {result_enhanced['confidence_percent']}")
    
    if 'feature_contributions' in result_enhanced and result_enhanced['feature_contributions']:
        contrib = result_enhanced['feature_contributions']
        print(f"\n特征贡献度分析:")
        print(f"  基准值: {contrib['base_value']:.4f}")
        print(f"  预测值: {contrib['prediction']:.4f}")
        
        print(f"\n  Top 5 正贡献特征（增加风险）:")
        for f in contrib['top_positive']:
            print(f"    {f['feature']:30s}: {f['value']:8.2f} → +{f['contribution']:7.4f}")
        
        print(f"\n  Top 5 负贡献特征（降低风险）:")
        for f in contrib['top_negative']:
            print(f"    {f['feature']:30s}: {f['value']:8.2f} → {f['contribution']:7.4f}")
    
    # 示例4: 全局特征重要性
    print("\n" + "=" * 80)
    print("示例4: 全局特征重要性（Top 10）")
    print("=" * 80)
    
    importance = predictor.get_feature_importance(top_k=10)
    if importance:
        print(f"\nTop 10 最重要特征:")
        for f in importance:
            print(f"  {f['rank']:2d}. {f['feature']:30s}: {f['importance']:7.4f} ({f['importance_normalized']:5.2f}%)")
    
    print("\n" + "=" * 80)
    print("✓ 演示完成")
    print("=" * 80)


if __name__ == '__main__':
    demo()
