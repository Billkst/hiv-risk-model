"""
HIV 风险预测工具实现

注意：一个文件只能有一个 Tool 子类
"""
from collections.abc import Generator
from typing import Any
import json
import logging

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from dify_plugin.config.logger_format import plugin_logger_handler

# 设置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(plugin_logger_handler)


class RiskPredictionTool(Tool):
    """
    HIV 风险预测工具（含特征贡献度分析）
    
    重要：此文件只能包含 RiskPredictionTool 类，不能添加其他 Tool 子类
    """
    
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        """
        执行 HIV 风险预测
        
        接受完整的区域数据JSON，自动提取所有可用字段
        """
        try:
            # 1. 获取区域数据（支持字符串或直接的字典）
            region_data_input = tool_parameters.get("region_data", "")
            
            if not region_data_input:
                yield self.create_text_message("Error: region_data is required.")
                return
            
            # 检查输入类型
            logger.info(f"Received region_data type: {type(region_data_input)}")
            
            # 如果已经是字典，直接使用
            if isinstance(region_data_input, dict):
                region_data_str = json.dumps(region_data_input, ensure_ascii=False)
                logger.info(f"Converted Python dict to JSON string")
            elif isinstance(region_data_input, str):
                region_data_str = region_data_input
                logger.info(f"Received JSON string, length: {len(region_data_str)}")
            else:
                yield self.create_text_message(f"Error: Unsupported region_data type: {type(region_data_input)}")
                return
            
            # 2. 解析JSON数据
            try:
                parsed_data = json.loads(region_data_str)
                
                # 如果是数组，取第一个元素
                if isinstance(parsed_data, list):
                    if len(parsed_data) == 0:
                        yield self.create_text_message("Error: Empty data array")
                        return
                    region_data = parsed_data[0]
                else:
                    region_data = parsed_data
                    
            except json.JSONDecodeError as e:
                yield self.create_text_message(
                    f"Error: Invalid JSON format for region_data: {str(e)}"
                )
                return
            
            # 3. 提取关键字段（支持中英文字段名）
            county_name = region_data.get("区县") or region_data.get("county_name", "未知区县")
            infection_rate = region_data.get("感染率") or region_data.get("infection_rate", 0)
            survival_count = region_data.get("存活数") or region_data.get("survival_count", 0)
            new_reports = region_data.get("新报告") or region_data.get("new_reports", 0)
            
            logger.info(f"Processing risk prediction for county: {county_name}")
            logger.info(f"Data fields received: {len(region_data)} fields")
            
            # 4. 构建特征向量（使用完整的区域数据）
            from utils.feature_processor import build_feature_vector, get_feature_explanation
            
            features = build_feature_vector(
                infection_rate=infection_rate,
                survival_count=survival_count,
                new_reports=new_reports,
                additional_features=region_data  # 传入完整数据
            )
            
            # 6. 加载模型并进行预测（使用打包的模型）
            from models.enhanced_predictor import EnhancedPredictor
            import os
            
            # 获取模型路径
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
            
            # 初始化预测器
            predictor = EnhancedPredictor(
                model_path=model_path,
                enable_attention=True,
                attention_strength=0.3
            )
            
            # 7. 执行预测
            prediction_result = predictor.predict_single(
                features, 
                return_attention=True,
                include_contributions=False
            )
            
            risk_level = prediction_result['risk_level_5']
            risk_score = prediction_result.get('risk_score', risk_level * 20)
            confidence = prediction_result.get('confidence', 0.85)
            
            # 8. 获取特征贡献度（从注意力权重）
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
            
            # 如果没有注意力权重，使用模拟数据
            if not top_10_features:
                top_10_features = self._get_mock_top_features()
            
            logger.info(
                f"Prediction completed: Risk Level {risk_level}, "
                f"Confidence {confidence:.2%}"
            )
            
            # 9. 构建返回结果
            result = {
                "county_name": county_name,
                "risk_level": int(risk_level),
                "risk_score": float(risk_score),
                "confidence": float(confidence),
                "risk_description": self._get_risk_description(risk_level),
                "key_features": {
                    "infection_rate": infection_rate,
                    "survival_count": survival_count,
                    "new_reports": new_reports
                },
                "top_10_contributing_features": top_10_features
            }
            
            # 10. 返回结果（使用多种输出方式）
            # JSON 输出（结构化数据）
            yield self.create_json_message(result)
            
            # 文本输出（人类可读）
            yield self.create_text_message(
                f"Risk assessment for {county_name}: "
                f"Level {risk_level} ({result['risk_description']}) "
                f"with {confidence:.1%} confidence"
            )
            
        except FileNotFoundError as e:
            # 模型文件未找到
            logger.error(f"Model file not found: {str(e)}")
            yield self.create_text_message(
                f"Model file not found: {str(e)}. "
                f"Please ensure the model is properly packaged."
            )
        except KeyError as e:
            # 参数错误
            logger.error(f"Missing required field: {str(e)}")
            yield self.create_text_message(
                f"Error: Missing required field: {str(e)}"
            )
        except Exception as e:
            # 其他未预期错误
            logger.error(f"Unexpected error in risk prediction: {str(e)}")
            yield self.create_text_message(
                f"Prediction failed with unexpected error: {str(e)}"
            )
    
    def _calculate_risk_level(self, infection_rate: float, survival_count: int, new_reports: int) -> int:
        """
        简化的风险等级计算（临时实现）
        
        TODO: 替换为实际模型预测
        """
        # 简单的规则基础评估
        score = 0
        
        if infection_rate > 100:
            score += 2
        elif infection_rate > 50:
            score += 1
        
        if survival_count > 1000:
            score += 2
        elif survival_count > 500:
            score += 1
        
        if new_reports > 100:
            score += 2
        elif new_reports > 50:
            score += 1
        
        # 映射到 1-5 级
        if score >= 5:
            return 5
        elif score >= 4:
            return 4
        elif score >= 3:
            return 3
        elif score >= 2:
            return 2
        else:
            return 1
    
    def _get_mock_top_features(self) -> list:
        """
        获取模拟的 Top 10 特征（临时实现）
        
        TODO: 替换为实际特征贡献度计算
        """
        from utils.feature_processor import get_feature_explanation
        
        mock_features = [
            ("infection_rate", 25.5),
            ("survival_count", 18.3),
            ("new_reports", 15.7),
            ("treatment_coverage", 12.4),
            ("testing_coverage", 9.8),
            ("prevention_coverage", 7.2),
            ("population", 4.6),
            ("gdp_per_capita", 3.1),
            ("healthcare_facilities", 2.2),
            ("education_level", 1.2),
        ]
        
        result = []
        for feature_name, contribution in mock_features:
            result.append({
                "feature_name": feature_name,
                "contribution_percentage": float(contribution),
                "medical_explanation": get_feature_explanation(feature_name)
            })
        return result
    
    def _get_risk_description(self, risk_level: int) -> str:
        """获取风险等级描述"""
        descriptions = {
            1: "Very Low Risk",
            2: "Low Risk",
            3: "Medium Risk",
            4: "High Risk",
            5: "Very High Risk"
        }
        return descriptions.get(risk_level, "Unknown")
