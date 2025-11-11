"""
统一错误处理模块

提供一致的错误响应格式和用户友好的错误消息
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class PluginError(Exception):
    """插件基础错误类"""
    def __init__(self, message: str, error_code: str = "PLUGIN_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ValidationError(PluginError):
    """参数验证错误"""
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR")


class ModelError(PluginError):
    """模型相关错误"""
    def __init__(self, message: str):
        super().__init__(message, "MODEL_ERROR")


class DataError(PluginError):
    """数据处理错误"""
    def __init__(self, message: str):
        super().__init__(message, "DATA_ERROR")


def format_error_response(error: Exception, include_details: bool = False) -> dict:
    """
    格式化错误响应
    
    Args:
        error: 异常对象
        include_details: 是否包含详细信息（用于调试）
    
    Returns:
        dict: 格式化的错误响应
    """
    if isinstance(error, PluginError):
        response = {
            "error": True,
            "error_code": error.error_code,
            "message": error.message
        }
    else:
        response = {
            "error": True,
            "error_code": "UNEXPECTED_ERROR",
            "message": "An unexpected error occurred. Please try again or contact support."
        }
    
    if include_details:
        response["details"] = str(error)
        response["type"] = type(error).__name__
    
    return response


def get_user_friendly_message(error: Exception) -> str:
    """
    获取用户友好的错误消息
    
    Args:
        error: 异常对象
    
    Returns:
        str: 用户友好的错误消息
    """
    if isinstance(error, ValidationError):
        return f"Input validation failed: {error.message}"
    
    elif isinstance(error, ModelError):
        return f"Model error: {error.message}. Please ensure the model is properly configured."
    
    elif isinstance(error, DataError):
        return f"Data processing error: {error.message}. Please check your input data format."
    
    elif isinstance(error, FileNotFoundError):
        return "Required model file not found. Please ensure the plugin is properly installed."
    
    elif isinstance(error, ValueError):
        return f"Invalid value: {str(error)}. Please check your input parameters."
    
    elif isinstance(error, KeyError):
        return f"Missing required field: {str(error)}. Please provide all required parameters."
    
    elif isinstance(error, TypeError):
        return f"Type error: {str(error)}. Please check the data types of your parameters."
    
    else:
        return f"An unexpected error occurred: {str(error)}. Please contact support if this persists."


def log_error(error: Exception, context: Optional[dict] = None):
    """
    记录错误日志
    
    Args:
        error: 异常对象
        context: 错误上下文信息
    """
    error_msg = f"Error: {type(error).__name__}: {str(error)}"
    
    if context:
        error_msg += f" | Context: {context}"
    
    logger.error(error_msg, exc_info=True)


def validate_required_params(params: dict, required_fields: list[str]) -> None:
    """
    验证必需参数
    
    Args:
        params: 参数字典
        required_fields: 必需字段列表
    
    Raises:
        ValidationError: 如果缺少必需参数
    """
    missing_fields = []
    
    for field in required_fields:
        if field not in params or params[field] is None or params[field] == "":
            missing_fields.append(field)
    
    if missing_fields:
        raise ValidationError(
            f"Missing required parameters: {', '.join(missing_fields)}"
        )


def validate_numeric_range(
    value: float, 
    min_value: Optional[float] = None, 
    max_value: Optional[float] = None,
    param_name: str = "value"
) -> None:
    """
    验证数值范围
    
    Args:
        value: 要验证的值
        min_value: 最小值（可选）
        max_value: 最大值（可选）
        param_name: 参数名称
    
    Raises:
        ValidationError: 如果值超出范围
    """
    if min_value is not None and value < min_value:
        raise ValidationError(
            f"{param_name} must be at least {min_value}, got {value}"
        )
    
    if max_value is not None and value > max_value:
        raise ValidationError(
            f"{param_name} must be at most {max_value}, got {value}"
        )


def validate_json_format(json_str: str, param_name: str = "data") -> dict:
    """
    验证JSON格式
    
    Args:
        json_str: JSON字符串
        param_name: 参数名称
    
    Returns:
        dict: 解析后的JSON对象
    
    Raises:
        ValidationError: 如果JSON格式无效
    """
    import json
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValidationError(
            f"Invalid JSON format for {param_name}: {str(e)}"
        )


def safe_execute(func, *args, error_message: str = "Operation failed", **kwargs):
    """
    安全执行函数，捕获并处理错误
    
    Args:
        func: 要执行的函数
        *args: 位置参数
        error_message: 错误消息前缀
        **kwargs: 关键字参数
    
    Returns:
        函数执行结果或None（如果出错）
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"{error_message}: {str(e)}", exc_info=True)
        return None
