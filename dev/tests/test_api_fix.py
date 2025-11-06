#!/usr/bin/env python3
"""
测试API修复
"""

import requests
import json

API_URL = "http://localhost:5000"

def test_basic_predict():
    """测试基础预测"""
    print("\n" + "="*60)
    print("测试1: 基础预测（不含特征贡献度）")
    print("="*60)
    
    response = requests.post(f"{API_URL}/v1/predict", json={
        "features": {
            "存活数": 1000,
            "感染率": 0.5,
            "治疗覆盖率": 85.0,
            "新报告": 50,
            "人口数": 500000
        }
    })
    
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    return response.status_code == 200

def test_predict_with_contributions():
    """测试含特征贡献度的预测"""
    print("\n" + "="*60)
    print("测试2: 增强预测（含特征贡献度）")
    print("="*60)
    
    response = requests.post(f"{API_URL}/v1/predict", json={
        "features": {
            "存活数": 1200,
            "感染率": 0.12,
            "治疗覆盖率": 92.0,
            "新报告": 80,
            "人口数": 600000
        },
        "include_contributions": True
    })
    
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    return response.status_code == 200

def test_predict_with_attention():
    """测试含注意力权重的预测"""
    print("\n" + "="*60)
    print("测试3: 完整增强预测（含注意力权重）")
    print("="*60)
    
    response = requests.post(f"{API_URL}/v1/predict", json={
        "features": {
            "存活数": 1500,
            "感染率": 0.25,
            "治疗覆盖率": 78.0,
            "新报告": 120,
            "人口数": 800000
        },
        "include_contributions": True,
        "include_attention": True,
        "use_enhanced": True
    })
    
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    return response.status_code == 200

def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("API修复测试")
    print("="*60)
    
    # 检查API是否运行
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code != 200:
            print("❌ API未运行，请先启动API服务")
            print("   运行: python3 api/app.py")
            return
    except Exception as e:
        print(f"❌ 无法连接到API: {e}")
        print("   请先启动API服务: python3 api/app.py")
        return
    
    print("✓ API正在运行")
    
    # 运行测试
    results = []
    results.append(("基础预测", test_basic_predict()))
    results.append(("含特征贡献度", test_predict_with_contributions()))
    results.append(("含注意力权重", test_predict_with_attention()))
    
    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    for name, passed in results:
        status = "✓ 通过" if passed else "❌ 失败"
        print(f"{name:20s}: {status}")
    
    all_passed = all(r[1] for r in results)
    print("\n" + "="*60)
    if all_passed:
        print("✓ 所有测试通过！")
    else:
        print("❌ 部分测试失败")
    print("="*60)

if __name__ == '__main__':
    main()
