#!/usr/bin/env python3
"""
测试特征贡献度功能
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from models.enhanced_predictor import EnhancedPredictor

# 初始化增强预测器
print("="*60)
print("测试增强预测器的特征贡献度功能")
print("="*60)

predictor = EnhancedPredictor('saved_models/final_model_3to5.pkl')

# 测试数据
features = {
    '存活数': 1200,
    '感染率': 0.12,
    '治疗覆盖率': 92.0,
    '新报告': 80,
    '人口数': 600000
}

print("\n测试1: 基础预测（不含特征贡献度）")
print("-"*60)
result1 = predictor.predict_single(features, include_contributions=False)
print(f"风险等级: {result1['risk_level_5']} - {result1['risk_description']}")
print(f"风险分数: {result1['risk_score']:.2f}")
print(f"特征贡献度: {result1.get('feature_contributions', '未请求')}")

print("\n测试2: 增强预测（含特征贡献度）")
print("-"*60)
result2 = predictor.predict_single(features, include_contributions=True)
print(f"风险等级: {result2['risk_level_5']} - {result2['risk_description']}")
print(f"风险分数: {result2['risk_score']:.2f}")

if result2.get('feature_contributions'):
    contrib = result2['feature_contributions']
    print(f"\n特征贡献度分析:")
    print(f"  基准值: {contrib['base_value']:.4f}")
    print(f"  预测值: {contrib['prediction']:.4f}")
    
    print(f"\n  Top 5 正贡献特征（增加风险）:")
    for f in contrib['top_positive']:
        print(f"    {f['feature']:30s}: {f['value']:8.2f} → +{f['contribution']:7.4f}")
    
    print(f"\n  Top 5 负贡献特征（降低风险）:")
    for f in contrib['top_negative']:
        print(f"    {f['feature']:30s}: {f['value']:8.2f} → {f['contribution']:7.4f}")
else:
    print("❌ 特征贡献度为空")

print("\n测试3: 完整增强预测（含注意力权重）")
print("-"*60)
result3 = predictor.predict_single(features, return_attention=True, include_contributions=True)
print(f"风险等级: {result3['risk_level_5']} - {result3['risk_description']}")
print(f"风险分数: {result3['risk_score']:.2f}")

if result3.get('attention_weights'):
    print(f"\n注意力权重（Top 10特征）:")
    attn_weights = result3['attention_weights']
    
    # 使用正确的键名 'top_10_features'
    if 'top_10_features' in attn_weights:
        for item in attn_weights['top_10_features'][:5]:
            print(f"  {item['feature']:30s}: 权重 {item['weight']:.4f}")
    else:
        print(f"  ⚠️ 注意力权重格式不符合预期，可用键: {list(attn_weights.keys())}")

if result3.get('feature_contributions'):
    print(f"\n✓ 特征贡献度已包含")
else:
    print(f"\n❌ 特征贡献度为空")

print("\n" + "="*60)
print("测试完成")
print("="*60)
