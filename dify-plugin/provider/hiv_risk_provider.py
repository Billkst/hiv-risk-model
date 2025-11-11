"""
HIV Risk Provider 实现

负责验证插件凭证和模型文件完整性
"""
from typing import Any
import os

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError


class HIVRiskProvider(ToolProvider):
    """
    HIV 风险评估工具提供者
    
    负责验证模型文件是否可以正常加载
    """
    
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        """
        验证凭证：检查模型文件是否可以正常加载
        
        由于模型已打包到插件中，这里主要验证模型文件的完整性
        
        Args:
            credentials: 凭证字典（本插件无需凭证）
        
        Raises:
            ToolProviderCredentialValidationError: 验证失败时抛出
        """
        try:
            # 获取模型文件路径（相对于插件根目录）
            model_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'models',
                'final_model_3to5.pkl'
            )
            
            scaler_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'models',
                'scaler.pkl'
            )
            
            # 检查文件是否存在
            if not os.path.exists(model_path):
                raise ToolProviderCredentialValidationError(
                    f"Model file not found: {model_path}. "
                    f"Please ensure the model is properly packaged."
                )
            
            if not os.path.exists(scaler_path):
                raise ToolProviderCredentialValidationError(
                    f"Scaler file not found: {scaler_path}. "
                    f"Please ensure the scaler is properly packaged."
                )
            
            # 尝试加载模型（验证文件完整性）
            try:
                from utils.model_loader import ModelLoader
                model_loader = ModelLoader()
                model_loader.load_model(model_path)
                print("✓ Model validation successful")
                
            except Exception as e:
                raise ToolProviderCredentialValidationError(
                    f"Failed to load model: {str(e)}. "
                    f"The model file may be corrupted."
                )
                    
        except ToolProviderCredentialValidationError:
            # 重新抛出已知的验证错误
            raise
        except Exception as e:
            # 捕获其他未预期的错误
            raise ToolProviderCredentialValidationError(
                f"Credential validation failed: {str(e)}"
            )
