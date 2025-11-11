"""
特征处理辅助函数

注意：函数名必须与导入语句完全匹配
"""
from typing import Dict, Any


def build_feature_vector(
    infection_rate: float,
    survival_count: int,
    new_reports: int,
    additional_features: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    构建 110 维特征向量
    
    Args:
        infection_rate: 感染率
        survival_count: 存活数
        new_reports: 新报告数
        additional_features: 其他特征（可选）
    
    Returns:
        完整的特征字典
    """
    import math
    
    # 辅助函数：将None或NaN转换为0
    def safe_float(value, default=0.0):
        if value is None or (isinstance(value, float) and math.isnan(value)):
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def safe_int(value, default=0):
        if value is None or (isinstance(value, float) and math.isnan(value)):
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    # 基础特征（确保没有NaN）
    features = {
        "infection_rate": safe_float(infection_rate),
        "survival_count": safe_int(survival_count),
        "new_reports": safe_int(new_reports),
    }
    
    # 合并其他特征，并清理NaN值
    if additional_features:
        for key, value in additional_features.items():
            if isinstance(value, (int, float)):
                features[key] = safe_float(value)
            elif isinstance(value, str):
                features[key] = value
            elif value is None:
                features[key] = 0.0
            else:
                features[key] = value
    
    # 填充缺失特征的默认值
    default_features = {
        "treatment_coverage": 0.0,
        "testing_coverage": 0.0,
        "prevention_coverage": 0.0,
        "population": 0,
        "gdp_per_capita": 0.0,
        "healthcare_facilities": 0,
        "education_level": 0.0,
        "urbanization_rate": 0.0,
    }
    
    for key, default_value in default_features.items():
        if key not in features:
            features[key] = default_value
    
    return features


def get_feature_explanation(feature_name: str) -> str:
    """
    获取特征的医学意义说明
    
    Args:
        feature_name: 特征名称
    
    Returns:
        医学解释文本
    """
    explanations = {
        "infection_rate": "HIV infection rate indicates disease prevalence in the population",
        "survival_count": "Number of people living with HIV reflects treatment effectiveness",
        "new_reports": "New reported cases indicate recent transmission trends",
        "treatment_coverage": "Percentage of HIV+ individuals receiving antiretroviral therapy",
        "testing_coverage": "Percentage of population tested for HIV",
        "prevention_coverage": "Coverage of HIV prevention programs",
        "population": "Total population size affects disease spread dynamics",
        "gdp_per_capita": "Economic status correlates with healthcare access",
        "healthcare_facilities": "Number of healthcare facilities affects treatment availability",
        "education_level": "Education level impacts awareness and prevention behaviors",
        "urbanization_rate": "Urban areas may have different transmission patterns",
    }
    
    return explanations.get(
        feature_name, 
        "Medical significance to be determined"
    )


def validate_feature_data(features: Dict[str, Any]) -> tuple[bool, str]:
    """
    验证特征数据的有效性
    
    Args:
        features: 特征字典
    
    Returns:
        (是否有效, 错误消息)
    """
    # 检查必需特征
    required_features = ["infection_rate", "survival_count", "new_reports"]
    
    for feature in required_features:
        if feature not in features:
            return False, f"Missing required feature: {feature}"
        
        # 检查数值范围
        value = features[feature]
        if not isinstance(value, (int, float)):
            return False, f"Feature {feature} must be a number"
        
        if value < 0:
            return False, f"Feature {feature} cannot be negative"
    
    return True, ""
