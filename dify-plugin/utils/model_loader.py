"""
模型加载器 - 单例模式

负责加载和缓存 HIV 风险预测模型
"""
import os
from typing import Optional


class ModelLoader:
    """
    模型加载器（单例模式）
    
    确保模型只加载一次，提高性能
    """
    _instance: Optional['ModelLoader'] = None
    _predictor = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def load_model(self, model_path: str = None):
        """
        加载模型文件
        
        Args:
            model_path: 模型文件路径（可选）
        """
        if self._predictor is not None:
            return  # 已加载，直接返回
        
        if model_path is None:
            # 默认路径
            base_dir = os.path.dirname(os.path.dirname(__file__))
            model_path = os.path.join(base_dir, 'models', 'final_model_3to5.pkl')
        
        # 加载增强预测器
        from models.enhanced_predictor import EnhancedPredictor
        
        self._predictor = EnhancedPredictor(
            model_path=model_path,
            enable_attention=True,
            attention_strength=0.3
        )
        
        print(f"✓ Enhanced predictor loaded from {model_path}")
    
    def get_predictor(self):
        """
        获取预测器实例
        
        Returns:
            EnhancedPredictor 对象
        """
        if self._predictor is None:
            self.load_model()
        
        return self._predictor
