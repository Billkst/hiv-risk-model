"""
HIV风险评估模型 API服务
提供RESTful API接口用于模型预测
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import pandas as pd
import joblib
import os
import sys
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.predictor import HIVRiskPredictor
from models.enhanced_predictor import EnhancedPredictor

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 配置Flask返回中文而不是Unicode编码
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_MIMETYPE'] = 'application/json; charset=utf-8'

# 全局变量
predictor = None
enhanced_predictor = None
MODEL_VERSION = "1.1.0"  # 更新到v1.1（包含DG-DAA增强）
API_VERSION = "v1"
USE_ENHANCED_MODEL = os.environ.get('USE_ENHANCED_MODEL', 'true').lower() == 'true'

def load_model():
    """加载模型"""
    global predictor, enhanced_predictor
    try:
        model_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'saved_models/final_model_3to5.pkl'
        )
        
        # 加载基础预测器（向后兼容）
        predictor = HIVRiskPredictor(model_path=model_path, enable_contributions=True)
        print(f"✓ 基础模型加载成功: {model_path}")
        
        # 加载增强预测器（DG-DAA）
        if USE_ENHANCED_MODEL:
            try:
                enhanced_predictor = EnhancedPredictor(
                    model_path=model_path,
                    enable_attention=True,
                    attention_strength=0.3
                )
                print(f"✓ 增强模型加载成功 (DG-DAA, attention_strength=0.3)")
            except Exception as e:
                print(f"⚠ 增强模型加载失败，使用基础模型: {e}")
                enhanced_predictor = None
        else:
            print(f"ℹ 增强模型未启用（USE_ENHANCED_MODEL=false）")
        
        return True
    except Exception as e:
        print(f"✗ 模型加载失败: {e}")
        return False


@app.route('/', methods=['GET'])
def home():
    """API首页"""
    response = jsonify({
        'service': 'HIV Risk Assessment API',
        'version': API_VERSION,
        'model_version': MODEL_VERSION,
        'model_type': 'Enhanced (DG-DAA)' if (USE_ENHANCED_MODEL and enhanced_predictor) else 'Baseline',
        'status': 'running',
        'endpoints': {
            'health': '/health',
            'predict_single': f'/{API_VERSION}/predict',
            'predict_batch': f'/{API_VERSION}/predict/batch',
            'model_info': f'/{API_VERSION}/model/info',
            'feature_importance': f'/{API_VERSION}/model/feature_importance'
        },
        'new_features': {
            'feature_contributions': 'Add "include_contributions": true to /v1/predict',
            'attention_weights': 'Add "include_attention": true to /v1/predict (Enhanced model only)',
            'feature_importance': 'GET /v1/model/feature_importance?top_k=10'
        },
        'enhancements': {
            'dg_daa': 'Domain-Guided Dual Adaptive Attention mechanism',
            'performance_improvement': 'F1 score +137.48% (cross-validation)',
            'medical_interpretability': 'Stage-aware attention weights'
        }
    })
    
    # 添加版本信息到响应头
    response.headers['X-Model-Version'] = MODEL_VERSION
    response.headers['X-API-Version'] = API_VERSION
    response.headers['X-Model-Type'] = 'Enhanced' if (USE_ENHANCED_MODEL and enhanced_predictor) else 'Baseline'
    
    return response


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': predictor is not None,
        'timestamp': datetime.now().isoformat()
    })


@app.route(f'/{API_VERSION}/model/info', methods=['GET'])
def model_info():
    """获取模型信息"""
    if predictor is None:
        return jsonify({'error': '模型未加载'}), 500
    
    response_data = {
        'model_name': predictor.model_name if hasattr(predictor, 'model_name') else 'HIV Risk Predictor',
        'model_version': MODEL_VERSION,
        'api_version': API_VERSION,
        'feature_count': len(predictor.feature_columns) if hasattr(predictor, 'feature_columns') else 110,
        'features': predictor.feature_columns if hasattr(predictor, 'feature_columns') else [],
        'risk_levels': {
            '1': '极低风险 (0-20分)',
            '2': '低风险 (20-40分)',
            '3': '中等风险 (40-60分)',
            '4': '高风险 (60-80分)',
            '5': '极高风险 (80-100分)'
        },
        'capabilities': {
            'feature_contributions': True,
            'attention_weights': USE_ENHANCED_MODEL and enhanced_predictor is not None,
            'enhanced_model': USE_ENHANCED_MODEL and enhanced_predictor is not None
        },
        'enhancements': {
            'dg_daa_enabled': USE_ENHANCED_MODEL and enhanced_predictor is not None,
            'attention_strength': 0.3 if (USE_ENHANCED_MODEL and enhanced_predictor) else None,
            'performance_improvement': {
                'cross_validation_f1': '+137.48%',
                'test_set_f1': '+6.25%'
            } if (USE_ENHANCED_MODEL and enhanced_predictor) else None
        }
    }
    
    response = jsonify(response_data)
    response.headers['X-Model-Version'] = MODEL_VERSION
    response.headers['X-API-Version'] = API_VERSION
    
    return response


@app.route(f'/{API_VERSION}/model/feature_importance', methods=['GET'])
def feature_importance():
    """
    获取全局特征重要性
    
    查询参数:
    - top_k: 返回Top K个特征（默认20）
    
    示例: /v1/model/feature_importance?top_k=10
    """
    if predictor is None:
        return jsonify({'error': '模型未加载'}), 500
    
    try:
        # 获取top_k参数
        top_k = request.args.get('top_k', default=20, type=int)
        
        # 限制范围
        top_k = max(1, min(top_k, 110))  # 1-110之间
        
        # 获取特征重要性
        importance = predictor.get_feature_importance(top_k=top_k)
        
        if importance is None:
            return jsonify({
                'success': False,
                'error': '特征贡献度分析器未启用'
            }), 400
        
        return jsonify({
            'success': True,
            'top_k': top_k,
            'total_features': len(predictor.feature_columns),
            'feature_importance': importance,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route(f'/{API_VERSION}/predict', methods=['POST'])
def predict_single():
    """
    单个样本预测
    
    请求体示例:
    {
        "features": {
            "存活数": 1000,
            "感染率": 0.5,
            "治疗覆盖率": 85.0,
            ...
        },
        "include_contributions": false,  // 可选，是否包含特征贡献度分析
        "include_attention": false,      // 可选，是否包含注意力权重（仅增强模型）
        "use_enhanced": true             // 可选，是否使用增强模型（默认true）
    }
    """
    if predictor is None:
        return jsonify({'error': '模型未加载'}), 500
    
    try:
        data = request.get_json()
        
        if 'features' not in data:
            return jsonify({'error': '缺少features字段'}), 400
        
        features = data['features']
        
        # 解析可选参数（默认False，向后兼容）
        include_contributions = data.get('include_contributions', False)
        include_attention = data.get('include_attention', False)
        use_enhanced = data.get('use_enhanced', True)
        
        # 选择使用哪个模型
        active_predictor = predictor
        model_type = 'baseline'
        
        if use_enhanced and USE_ENHANCED_MODEL and enhanced_predictor:
            active_predictor = enhanced_predictor
            model_type = 'enhanced'
        
        # 预测
        if model_type == 'enhanced' and (include_attention or include_contributions):
            # 使用增强模型，可能需要注意力权重和/或特征贡献度
            result = active_predictor.predict_single(
                features, 
                return_attention=include_attention,
                include_contributions=include_contributions
            )
        else:
            # 基础预测或不需要增强功能
            if hasattr(active_predictor, 'predict_single'):
                result = active_predictor.predict_single(features, include_contributions=include_contributions)
            else:
                # 兜底
                result = {'risk_level_5': 0, 'risk_description': 'Unknown', 'risk_score': 0, 'confidence': 0}
        
        # 构建响应
        response_data = {
            'success': True,
            'prediction': {
                'risk_level': result.get('risk_level_5', result.get('risk_level', 0)),
                'risk_description': result.get('risk_description', 'Unknown'),
                'risk_score': result.get('risk_score', 0),
                'confidence': result.get('confidence', 0),
                'confidence_percent': result.get('confidence_percent', '0%')
            },
            'model_info': {
                'version': MODEL_VERSION,
                'type': model_type
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # 添加特征贡献度（如果请求）
        if include_contributions and 'feature_contributions' in result:
            response_data['feature_contributions'] = result['feature_contributions']
        
        # 添加注意力权重（如果请求且可用）
        if include_attention and 'attention_weights' in result:
            attn = result['attention_weights']
            response_data['attention_weights'] = {
                'top_10_features': attn.get('top_10_features', []),
                'all_features': attn.get('all_features', []),  # 所有特征的权重（带名称）
                'summary': {
                    'total_features': len(attn.get('all_features', [])),
                    'top_10_avg_weight': sum(f['weight'] for f in attn.get('top_10_features', [])[:10]) / 10 if attn.get('top_10_features') else 0
                }
            }
        
        # 创建响应并添加版本头
        response = jsonify(response_data)
        response.headers['X-Model-Version'] = MODEL_VERSION
        response.headers['X-Model-Type'] = model_type
        
        return response
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc() if app.debug else None
        }), 500


@app.route(f'/{API_VERSION}/predict/batch', methods=['POST'])
def predict_batch():
    """
    批量预测
    
    请求体示例:
    {
        "samples": [
            {"存活数": 1000, "感染率": 0.5, ...},
            {"存活数": 2000, "感染率": 0.3, ...}
        ]
    }
    """
    if predictor is None:
        return jsonify({'error': '模型未加载'}), 500
    
    try:
        data = request.get_json()
        
        if 'samples' not in data:
            return jsonify({'error': '缺少samples字段'}), 400
        
        samples = data['samples']
        
        if not isinstance(samples, list):
            return jsonify({'error': 'samples必须是数组'}), 400
        
        # 批量预测
        results = []
        for idx, sample in enumerate(samples):
            try:
                result = predictor.predict_single(sample)
                results.append({
                    'index': idx,
                    'success': True,
                    'risk_level': result['risk_level_5'],
                    'risk_description': result['risk_description'],
                    'risk_score': result['risk_score'],
                    'confidence': result['confidence']
                })
            except Exception as e:
                results.append({
                    'index': idx,
                    'success': False,
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'total': len(samples),
            'predictions': results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({'error': '接口不存在'}), 404


@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    return jsonify({'error': '服务器内部错误'}), 500


if __name__ == '__main__':
    # 加载模型
    if not load_model():
        print("警告: 模型加载失败，API可能无法正常工作")
    
    # 启动服务
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'
    
    print(f"\n{'='*70}")
    print(f"  HIV风险评估API服务启动")
    print(f"{'='*70}")
    print(f"  地址: http://{host}:{port}")
    print(f"  API版本: {API_VERSION}")
    print(f"  模型版本: {MODEL_VERSION}")
    print(f"  模型类型: {'Enhanced (DG-DAA)' if (USE_ENHANCED_MODEL and enhanced_predictor) else 'Baseline'}")
    print(f"  增强功能: {'启用' if (USE_ENHANCED_MODEL and enhanced_predictor) else '禁用'}")
    print(f"{'='*70}")
    print(f"\n  新功能:")
    print(f"    - 特征贡献度分析: include_contributions=true")
    if USE_ENHANCED_MODEL and enhanced_predictor:
        print(f"    - 注意力权重: include_attention=true")
        print(f"    - DG-DAA增强: 性能提升137.48% (交叉验证)")
    print(f"\n  环境变量:")
    print(f"    - USE_ENHANCED_MODEL={USE_ENHANCED_MODEL}")
    print(f"    - DEBUG={debug}")
    print(f"{'='*70}\n")
    
    app.run(host=host, port=port, debug=debug)
