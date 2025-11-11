"""
相关性分析工具实现

注意：一个文件只能有一个 Tool 子类
"""
from collections.abc import Generator
from typing import Any
import json
import logging
import numpy as np
import pandas as pd
from scipy.stats import pearsonr

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from dify_plugin.config.logger_format import plugin_logger_handler

# 设置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(plugin_logger_handler)


class CorrelationAnalysisTool(Tool):
    """
    相关性分析工具
    
    分析HIV风险因素之间的相关性
    """
    
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        """
        执行相关性分析
        
        参数处理遵循最佳实践：
        - 必需参数使用 .get() 并提供默认值
        - 可选参数使用 try-except 处理
        """
        try:
            # 1. 获取必需参数（支持字符串或直接的列表/字典）
            feature_data_input = tool_parameters.get("feature_data", "")
            
            # 2. 获取可选参数
            try:
                correlation_threshold = float(tool_parameters["correlation_threshold"])
            except (KeyError, ValueError):
                correlation_threshold = 0.5
            
            try:
                p_value_threshold = float(tool_parameters["p_value_threshold"])
            except (KeyError, ValueError):
                p_value_threshold = 0.05
            
            # 3. 验证必需参数
            if not feature_data_input:
                yield self.create_text_message("Error: Feature data is required.")
                return
            
            # 检查输入类型并转换
            logger.info(f"Received feature_data type: {type(feature_data_input)}")
            
            if isinstance(feature_data_input, (list, dict)):
                feature_data_str = json.dumps(feature_data_input, ensure_ascii=False)
                logger.info(f"Converted Python object to JSON string")
            elif isinstance(feature_data_input, str):
                feature_data_str = feature_data_input
                logger.info(f"Received JSON string, length: {len(feature_data_str)}")
            else:
                yield self.create_text_message(f"Error: Unsupported feature_data type: {type(feature_data_input)}")
                return
            
            logger.info(f"Processing correlation analysis with threshold: {correlation_threshold}")
            
            # 4. 解析特征数据
            try:
                feature_data = json.loads(feature_data_str)
            except json.JSONDecodeError as e:
                yield self.create_text_message(
                    f"Error: Invalid JSON format for feature_data: {str(e)}"
                )
                return
            
            # 5. 转换为 DataFrame
            if isinstance(feature_data, dict):
                # 单个样本
                df = pd.DataFrame([feature_data])
            elif isinstance(feature_data, list):
                # 多个样本
                df = pd.DataFrame(feature_data)
            else:
                yield self.create_text_message(
                    "Error: Feature data must be a dictionary or list of dictionaries."
                )
                return
            
            # 6. 计算相关性矩阵
            if len(df) < 2:
                yield self.create_text_message(
                    "Error: At least 2 samples are required for correlation analysis."
                )
                return
            
            # 7. 执行相关性分析
            correlation_results = self._calculate_correlations(
                df, 
                correlation_threshold, 
                p_value_threshold
            )
            
            logger.info(
                f"Correlation analysis completed: "
                f"Found {len(correlation_results['significant_pairs'])} significant pairs"
            )
            
            # 8. 构建返回结果
            result = {
                "total_features": len(df.columns),
                "total_samples": len(df),
                "correlation_threshold": correlation_threshold,
                "p_value_threshold": p_value_threshold,
                "significant_pairs": correlation_results['significant_pairs'],
                "positive_correlations": correlation_results['positive_correlations'],
                "negative_correlations": correlation_results['negative_correlations'],
                "summary": correlation_results['summary']
            }
            
            # 9. 返回结果
            yield self.create_json_message(result)
            
            # 文本输出
            summary_text = (
                f"Correlation Analysis Results:\n"
                f"- Total features: {result['total_features']}\n"
                f"- Significant pairs: {len(result['significant_pairs'])}\n"
                f"- Positive correlations: {len(result['positive_correlations'])}\n"
                f"- Negative correlations: {len(result['negative_correlations'])}"
            )
            yield self.create_text_message(summary_text)
            
        except Exception as e:
            # 其他未预期错误
            logger.error(f"Unexpected error in correlation analysis: {str(e)}")
            yield self.create_text_message(
                f"Correlation analysis failed with unexpected error: {str(e)}"
            )
    
    def _calculate_correlations(
        self, 
        df: pd.DataFrame, 
        threshold: float, 
        p_threshold: float
    ) -> dict:
        """
        计算特征间的相关性
        
        Args:
            df: 特征数据框
            threshold: 相关系数阈值
            p_threshold: p值阈值
        
        Returns:
            dict: 相关性分析结果
        """
        features = df.columns.tolist()
        n_features = len(features)
        
        significant_pairs = []
        positive_correlations = []
        negative_correlations = []
        
        # 计算所有特征对的相关性
        for i in range(n_features):
            for j in range(i + 1, n_features):
                feature1 = features[i]
                feature2 = features[j]
                
                # 获取特征值
                values1 = df[feature1].values
                values2 = df[feature2].values
                
                # 跳过常数特征
                if np.std(values1) == 0 or np.std(values2) == 0:
                    continue
                
                # 计算 Pearson 相关系数
                try:
                    corr_coef, p_value = pearsonr(values1, values2)
                    
                    # 检查是否显著
                    if abs(corr_coef) >= threshold and p_value < p_threshold:
                        pair_info = {
                            "feature1": feature1,
                            "feature2": feature2,
                            "correlation_coefficient": float(corr_coef),
                            "p_value": float(p_value),
                            "correlation_type": "positive" if corr_coef > 0 else "negative",
                            "strength": self._get_correlation_strength(abs(corr_coef))
                        }
                        
                        significant_pairs.append(pair_info)
                        
                        if corr_coef > 0:
                            positive_correlations.append(pair_info)
                        else:
                            negative_correlations.append(pair_info)
                
                except Exception as e:
                    logger.warning(f"Failed to calculate correlation for {feature1} and {feature2}: {e}")
                    continue
        
        # 按相关系数强度排序
        significant_pairs.sort(key=lambda x: abs(x['correlation_coefficient']), reverse=True)
        positive_correlations.sort(key=lambda x: x['correlation_coefficient'], reverse=True)
        negative_correlations.sort(key=lambda x: x['correlation_coefficient'])
        
        # 生成摘要
        summary = {
            "total_pairs_analyzed": n_features * (n_features - 1) // 2,
            "significant_pairs_found": len(significant_pairs),
            "positive_count": len(positive_correlations),
            "negative_count": len(negative_correlations),
            "strongest_positive": positive_correlations[0] if positive_correlations else None,
            "strongest_negative": negative_correlations[0] if negative_correlations else None
        }
        
        return {
            "significant_pairs": significant_pairs[:20],  # 返回前20个
            "positive_correlations": positive_correlations[:10],  # 返回前10个
            "negative_correlations": negative_correlations[:10],  # 返回前10个
            "summary": summary
        }
    
    def _get_correlation_strength(self, abs_corr: float) -> str:
        """
        获取相关性强度描述
        
        Args:
            abs_corr: 相关系数绝对值
        
        Returns:
            str: 强度描述
        """
        if abs_corr >= 0.8:
            return "very_strong"
        elif abs_corr >= 0.6:
            return "strong"
        elif abs_corr >= 0.4:
            return "moderate"
        elif abs_corr >= 0.2:
            return "weak"
        else:
            return "very_weak"
