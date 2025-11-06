#!/usr/bin/env python3
"""
测试注意力权重功能
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from models.enhanced_predictor import EnhancedPredictor

# 初始化增强预测器
print("="*60)
print("测试增强预测器的注意力权重功能")
print("="*60)

predictor = EnhancedPredictor('saved_models/final_model_3to5.pkl')

# 测试数据
features = {
    '存活数': 1500,
    '感染率': 0.25,
    '治疗覆盖率': 78.0,
    '新报告': 120,
    '人口数': 800000
}

print("\n测试1: 基础预测（不含注意力权重）")
print("-"*60)
result1 = predictor.predict_single(features, return_attention=False)
print(f"风险等级: {result1['risk_level_5']} - {result1['risk_description']}")
print(f"风险分数: {result1['risk_score']:.2f}")
print(f"注意力权重: {result1.get('attention_weights', '未请求')}")

print("\n测试2: 增强预测（含注意力权重）")
print("-"*60)
result2 = predictor.predict_single(features, return_attention=True)
print(f"风险等级: {result2['risk_level_5']} - {result2['risk_description']}")
print(f"风险分数: {result2['risk_score']:.2f}")

if result2.get('attention_weights'):
    attn = result2['attention_weights']
    print(f"\n注意力权重:")
    print(f"  特征注意力: {len(attn.get('feature_attention', []))} 个特征")
    print(f"  样本注意力: {attn.get('sample_attention', 'N/A')}")
    
    print(f"\n  Top 10 关注特征:")
    for item in attn.get('top_attended_features', [])[:10]:
        print(f"    {item['feature']:30s}: 权重 {item['weight']:.4f}")
else:
    print("❌ 注意力权重为空")

print("\n测试3: 完整增强预测（含注意力权重和特征贡献度）")
print("-"*60)
result3 = predictor.predict_single(features, return_attention=True, include_contributions=True)
print(f"风险等级: {result3['risk_level_5']} - {result3['risk_description']}")
print(f"风险分数: {result3['risk_score']:.2f}")

if result3.get('attention_weights'):
    print(f"\n✓ 注意力权重已包含")
    attn = result3['attention_weights']
    print(f"  Top 5 关注特征:")
    for item in attn.get('top_attended_features', [])[:5]:
        print(f"    {item['feature']:30s}: 权重 {item['weight']:.4f}")
else:
    print(f"\n❌ 注意力权重为空")

if result3.get('feature_contributions'):
    print(f"\n✓ 特征贡献度已包含")
    contrib = result3['feature_contributions']
    print(f"  Top 3 正贡献特征:")
    for f in contrib['top_positive'][:3]:
        print(f"    {f['feature']:30s}: +{f['contribution']:7.4f}")
else:
    print(f"\n❌ 特征贡献度为空")

print("\n" + "="*60)
print("测试完成")
print("="*60)
