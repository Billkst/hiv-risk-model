"""
批量预测工具实现

注意：一个文件只能有一个 Tool 子类
"""
from collections.abc import Generator
from typing import Any
import json
import logging
import io
import pandas as pd

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from dify_plugin.config.logger_format import plugin_logger_handler

# 设置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(plugin_logger_handler)


class BatchPredictionTool(Tool):
    """
    批量HIV风险预测工具（含特征贡献度分析）
    
    支持CSV和JSON格式的批量输入
    """
    
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        """
        执行批量预测
        
        参数处理遵循最佳实践：
        - 必需参数使用 .get() 并提供默认值
        - 可选参数使用 try-except 处理
        """
        try:
            # 1. 获取数据列表（支持字符串或直接的列表/字典）
            data_list_input = tool_parameters.get("data_list", "")
            
            if not data_list_input:
                yield self.create_text_message("Error: data_list is required.")
                return
            
            # 检查输入类型
            logger.info(f"Received data_list type: {type(data_list_input)}")
            
            # 如果已经是列表或字典，直接使用
            if isinstance(data_list_input, (list, dict)):
                data_list_str = json.dumps(data_list_input, ensure_ascii=False)
                logger.info(f"Converted Python object to JSON string, length: {len(data_list_str)}")
            elif isinstance(data_list_input, str):
                data_list_str = data_list_input
                logger.info(f"Received JSON string, length: {len(data_list_str)}")
            else:
                yield self.create_text_message(f"Error: Unsupported data_list type: {type(data_list_input)}")
                return
            
            # 2. 获取可选参数
            try:
                batch_size = int(tool_parameters.get("batch_size", 10))
            except (ValueError, TypeError):
                batch_size = 10
            
            try:
                include_progress = tool_parameters.get("include_progress", True)
                if isinstance(include_progress, str):
                    include_progress = include_progress.lower() == "true"
            except (ValueError, TypeError):
                include_progress = True
            
            logger.info(f"Processing batch prediction with batch_size: {batch_size}")
            logger.info(f"Tool parameters keys: {list(tool_parameters.keys())}")
            logger.info(f"Data string preview (first 200 chars): {data_list_str[:200]}")
            
            # 3. 解析JSON数组
            try:
                # 尝试修复可能被截断的JSON
                data_list_str = data_list_str.strip()
                original_length = len(data_list_str)
                
                logger.info(f"Received data_list length: {original_length} characters")
                
                # 修复 nan 值（JSON 不支持 nan，需要替换为 null）
                import re
                data_list_str = re.sub(r'\bnan\b', 'null', data_list_str)
                data_list_str = re.sub(r'\bNaN\b', 'null', data_list_str)
                data_list_str = re.sub(r'\bNAN\b', 'null', data_list_str)
                
                # 检查是否被截断
                was_truncated = False
                if not data_list_str.endswith(']'):
                    was_truncated = True
                    # 如果JSON被截断，尝试找到最后一个完整的对象
                    last_complete_obj = data_list_str.rfind('}')
                    if last_complete_obj != -1:
                        data_list_str = data_list_str[:last_complete_obj + 1] + ']'
                        logger.warning(f"JSON truncated at {original_length} chars, recovered {data_list_str.count('{')} objects")
                
                counties_data = json.loads(data_list_str)
                
                if was_truncated:
                    yield self.create_text_message(
                        f"⚠️ Warning: Input data was truncated (received {original_length} chars). "
                        f"Successfully recovered {len(counties_data)} complete county records. "
                        f"Some data may be missing due to Dify parameter size limits."
                    )
                
                # 确保是列表
                if not isinstance(counties_data, list):
                    counties_data = [counties_data]
                    
            except json.JSONDecodeError as e:
                yield self.create_text_message(
                    f"Error: Invalid JSON format for data_list: {str(e)}\nData length: {len(data_list_str)}\nLast 200 chars: {data_list_str[-200:]}"
                )
                return
            
            if not counties_data:
                yield self.create_text_message("Error: data_list is empty.")
                return
            
            logger.info(f"Received {len(counties_data)} counties for batch prediction")
            
            # 5. 加载模型
            from models.enhanced_predictor import EnhancedPredictor
            from utils.feature_processor import build_feature_vector, get_feature_explanation
            import os
            
            base_dir = os.path.dirname(os.path.dirname(__file__))
            model_path = os.path.join(base_dir, 'models', 'final_model_3to5.pkl')
            
            # 检查模型文件是否存在
            if not os.path.exists(model_path):
                logger.error(f"Model file not found at: {model_path}")
                logger.error(f"Base directory: {base_dir}")
                logger.error(f"Directory contents: {os.listdir(base_dir) if os.path.exists(base_dir) else 'base_dir not found'}")
                yield self.create_text_message(
                    f"Error: Model file not found. Please ensure the plugin is properly packaged with the model file."
                )
                return
            
            logger.info(f"Loading model from: {model_path}")
            
            predictor = EnhancedPredictor(
                model_path=model_path,
                enable_attention=True,
                attention_strength=0.3
            )
            
            # 6. 批量预测
            results = []
            total_counties = len(counties_data)
            
            for idx, county_data in enumerate(counties_data):
                try:
                    # 进度反馈
                    if include_progress and (idx + 1) % batch_size == 0:
                        progress_pct = ((idx + 1) / total_counties) * 100
                        yield self.create_text_message(
                            f"Progress: {idx + 1}/{total_counties} ({progress_pct:.1f}%)"
                        )
                    
                    # 提取关键字段（支持中英文字段名）
                    county_name = county_data.get("区县") or county_data.get("county_name", f"县区_{idx+1}")
                    infection_rate = county_data.get("感染率") or county_data.get("infection_rate", 0)
                    survival_count = county_data.get("存活数") or county_data.get("survival_count", 0)
                    new_reports = county_data.get("新报告") or county_data.get("new_reports", 0)
                    
                    # 构建特征向量（使用完整数据）
                    features = build_feature_vector(
                        infection_rate=infection_rate,
                        survival_count=survival_count,
                        new_reports=new_reports,
                        additional_features=county_data  # 传入完整数据
                    )
                    
                    # 执行预测
                    prediction_result = predictor.predict_single(
                        features,
                        return_attention=True,
                        include_contributions=False
                    )
                    
                    # 获取特征贡献度
                    top_10_features = []
                    if 'attention_weights' in prediction_result:
                        attention_data = prediction_result['attention_weights']
                        top_features = attention_data.get('top_10_features', [])
                        
                        for item in top_features:
                            top_10_features.append({
                                "feature_name": item['feature'],
                                "contribution_percentage": float(item['weight'] * 100),
                                "medical_explanation": get_feature_explanation(item['feature'])
                            })
                    
                    # 构建结果
                    risk_level = prediction_result['risk_level_5']
                    risk_score = prediction_result.get('risk_score', risk_level * 20)
                    
                    result = {
                        "county_name": county_name,
                        "risk_level": risk_level,
                        "risk_score": float(risk_score),
                        "confidence": prediction_result.get('confidence', 0.85),
                        "risk_description": prediction_result.get('risk_description', ''),
                        "key_features": {
                            "infection_rate": infection_rate,
                            "survival_count": survival_count,
                            "new_reports": new_reports
                        },
                        "top_10_contributing_features": top_10_features
                    }
                    
                    results.append(result)
                    
                except Exception as e:
                    error_county_name = county_data.get("区县") or county_data.get("county_name", f"县区_{idx+1}")
                    logger.error(f"Error predicting for county {error_county_name}: {e}")
                    results.append({
                        "county_name": error_county_name,
                        "error": str(e)
                    })
            
            logger.info(f"Batch prediction completed: {len(results)} results")
            
            # 7. 构建汇总结果
            summary = self._generate_summary(results)
            
            final_result = {
                "total_counties": total_counties,
                "successful_predictions": len([r for r in results if 'risk_level' in r]),
                "failed_predictions": len([r for r in results if 'error' in r]),
                "summary": summary,
                "predictions": results
            }
            
            # 8. 返回结果
            yield self.create_json_message(final_result)
            
            # 文本输出
            summary_text = (
                f"Batch Prediction Results:\n"
                f"- Total counties: {final_result['total_counties']}\n"
                f"- Successful: {final_result['successful_predictions']}\n"
                f"- Failed: {final_result['failed_predictions']}\n"
                f"- Average risk level: {summary['average_risk_level']:.2f}\n"
                f"- High risk counties: {summary['high_risk_count']}"
            )
            yield self.create_text_message(summary_text)
            
        except Exception as e:
            # 其他未预期错误
            logger.error(f"Unexpected error in batch prediction: {str(e)}")
            yield self.create_text_message(
                f"Batch prediction failed with unexpected error: {str(e)}"
            )
    

    
    def _generate_summary(self, results: list[dict]) -> dict:
        """
        生成批量预测汇总统计
        
        Args:
            results: 预测结果列表
        
        Returns:
            dict: 汇总统计
        """
        successful_results = [r for r in results if 'risk_level' in r]
        
        if not successful_results:
            return {
                "average_risk_level": 0,
                "risk_distribution": {},
                "high_risk_count": 0,
                "medium_risk_count": 0,
                "low_risk_count": 0
            }
        
        risk_levels = [r['risk_level'] for r in successful_results]
        
        # 风险分布
        risk_distribution = {}
        for level in range(1, 6):
            count = risk_levels.count(level)
            risk_distribution[f"level_{level}"] = count
        
        # 统计
        high_risk_count = sum(1 for r in risk_levels if r >= 4)
        medium_risk_count = sum(1 for r in risk_levels if r == 3)
        low_risk_count = sum(1 for r in risk_levels if r <= 2)
        
        return {
            "average_risk_level": sum(risk_levels) / len(risk_levels),
            "risk_distribution": risk_distribution,
            "high_risk_count": high_risk_count,
            "medium_risk_count": medium_risk_count,
            "low_risk_count": low_risk_count,
            "highest_risk_county": max(successful_results, key=lambda x: x['risk_level'])['county_name'],
            "lowest_risk_county": min(successful_results, key=lambda x: x['risk_level'])['county_name']
        }
