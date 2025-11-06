"""
增强版API测试脚本
测试特征贡献度和特征重要性功能
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def print_section(title):
    """打印分隔线"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def test_health():
    """测试健康检查"""
    print_section("测试1: 健康检查")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"✗ 请求失败: {e}")
        return False

def test_model_info():
    """测试模型信息"""
    print_section("测试2: 模型信息")
    
    try:
        response = requests.get(f"{BASE_URL}/v1/model/info", timeout=5)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"模型名称: {data.get('model_name')}")
            print(f"模型版本: {data.get('model_version')}")
            print(f"特征数量: {data.get('feature_count')}")
            print(f"特征贡献度: {'启用' if data.get('features_contributions_enabled') else '禁用'}")
            return True
        return False
    except Exception as e:
        print(f"✗ 请求失败: {e}")
        return False

def test_predict_basic():
    """测试基础预测（不含特征贡献度）"""
    print_section("测试3: 基础预测（向后兼容）")
    
    features = {
        "存活数": 1200,
        "新报告": 80,
        "感染率": 0.12,
        "治疗覆盖率": 92.0,
        "病毒抑制比例": 88.0
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/v1/predict",
            headers={"Content-Type": "application/json"},
            json={"features": features},
            timeout=10
        )
        elapsed_ms = (time.time() - start_time) * 1000
        
        print(f"状态码: {response.status_code}")
        print(f"响应时间: {elapsed_ms:.2f} ms")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            pred = data.get('prediction', {})
            print(f"\n预测结果:")
            print(f"  风险等级: {pred.get('risk_level')} - {pred.get('risk_description')}")
            print(f"  风险分数: {pred.get('risk_score'):.2f}")
            print(f"  置信度: {pred.get('confidence_percent')}")
            print(f"  特征贡献度: {'包含' if 'feature_contributions' in data else '不包含'}")
            
            return True
        return False
    except Exception as e:
        print(f"✗ 请求失败: {e}")
        return False

def test_predict_with_contributions():
    """测试增强预测（含特征贡献度）"""
    print_section("测试4: 增强预测（含特征贡献度）")
    
    features = {
        "存活数": 1200,
        "新报告": 80,
        "感染率": 0.12,
        "治疗覆盖率": 92.0,
        "病毒抑制比例": 88.0,
        "筛查人数": 120000,
        "暗娼规模": 800
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/v1/predict",
            headers={"Content-Type": "application/json"},
            json={
                "features": features,
                "include_contributions": True  # 启用特征贡献度
            },
            timeout=10
        )
        elapsed_ms = (time.time() - start_time) * 1000
        
        print(f"状态码: {response.status_code}")
        print(f"响应时间: {elapsed_ms:.2f} ms")
        
        if response.status_code == 200:
            data = response.json()
            
            pred = data.get('prediction', {})
            print(f"\n预测结果:")
            print(f"  风险等级: {pred.get('risk_level')} - {pred.get('risk_description')}")
            print(f"  风险分数: {pred.get('risk_score'):.2f}")
            print(f"  置信度: {pred.get('confidence_percent')}")
            
            if 'feature_contributions' in data:
                contrib = data['feature_contributions']
                print(f"\n特征贡献度分析:")
                print(f"  基准值: {contrib.get('base_value'):.4f}")
                print(f"  预测值: {contrib.get('prediction'):.4f}")
                print(f"  方法: {contrib.get('method')}")
                
                print(f"\n  Top 5 正贡献特征（增加风险）:")
                for f in contrib.get('top_positive', [])[:5]:
                    print(f"    {f['feature']:30s}: {f['value']:8.2f} → +{f['contribution']:7.4f}")
                
                print(f"\n  Top 5 负贡献特征（降低风险）:")
                for f in contrib.get('top_negative', [])[:5]:
                    print(f"    {f['feature']:30s}: {f['value']:8.2f} → {f['contribution']:7.4f}")
            else:
                print("\n⚠️  未包含特征贡献度")
            
            return True
        return False
    except Exception as e:
        print(f"✗ 请求失败: {e}")
        return False

def test_feature_importance():
    """测试全局特征重要性"""
    print_section("测试5: 全局特征重要性")
    
    try:
        # 测试Top 10
        response = requests.get(
            f"{BASE_URL}/v1/model/feature_importance?top_k=10",
            timeout=5
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Top K: {data.get('top_k')}")
            print(f"总特征数: {data.get('total_features')}")
            
            print(f"\nTop 10 最重要特征:")
            for f in data.get('feature_importance', []):
                print(f"  {f['rank']:2d}. {f['feature']:30s}: {f['importance']:7.4f} ({f['importance_normalized']:5.2f}%)")
            
            return True
        return False
    except Exception as e:
        print(f"✗ 请求失败: {e}")
        return False

def test_performance():
    """测试性能对比"""
    print_section("测试6: 性能对比")
    
    features = {
        "存活数": 1000,
        "感染率": 0.5,
        "治疗覆盖率": 85.0
    }
    
    n_requests = 10
    
    # 测试基础预测
    print(f"\n基础预测（不含特征贡献度）- {n_requests}次请求:")
    times_basic = []
    for i in range(n_requests):
        try:
            start = time.time()
            response = requests.post(
                f"{BASE_URL}/v1/predict",
                headers={"Content-Type": "application/json"},
                json={"features": features},
                timeout=10
            )
            elapsed = (time.time() - start) * 1000
            if response.status_code == 200:
                times_basic.append(elapsed)
        except:
            pass
    
    if times_basic:
        print(f"  平均响应时间: {sum(times_basic)/len(times_basic):.2f} ms")
        print(f"  最快: {min(times_basic):.2f} ms")
        print(f"  最慢: {max(times_basic):.2f} ms")
    
    # 测试增强预测
    print(f"\n增强预测（含特征贡献度）- {n_requests}次请求:")
    times_enhanced = []
    for i in range(n_requests):
        try:
            start = time.time()
            response = requests.post(
                f"{BASE_URL}/v1/predict",
                headers={"Content-Type": "application/json"},
                json={"features": features, "include_contributions": True},
                timeout=10
            )
            elapsed = (time.time() - start) * 1000
            if response.status_code == 200:
                times_enhanced.append(elapsed)
        except:
            pass
    
    if times_enhanced:
        print(f"  平均响应时间: {sum(times_enhanced)/len(times_enhanced):.2f} ms")
        print(f"  最快: {min(times_enhanced):.2f} ms")
        print(f"  最慢: {max(times_enhanced):.2f} ms")
    
    if times_basic and times_enhanced:
        overhead = sum(times_enhanced)/len(times_enhanced) - sum(times_basic)/len(times_basic)
        print(f"\n特征贡献度开销: +{overhead:.2f} ms")
        
        if overhead < 50:
            print(f"✓ 性能开销在可接受范围内 (< 50ms)")
            return True
        else:
            print(f"⚠️  性能开销较大 (> 50ms)")
            return False
    
    return False

def main():
    """运行所有测试"""
    print("\n" + "="*80)
    print("  HIV风险评估API - 增强功能测试")
    print("="*80)
    print(f"  目标地址: {BASE_URL}")
    print("="*80)
    
    results = []
    
    # 运行测试
    results.append(("健康检查", test_health()))
    time.sleep(0.5)
    
    results.append(("模型信息", test_model_info()))
    time.sleep(0.5)
    
    results.append(("基础预测", test_predict_basic()))
    time.sleep(0.5)
    
    results.append(("增强预测", test_predict_with_contributions()))
    time.sleep(0.5)
    
    results.append(("特征重要性", test_feature_importance()))
    time.sleep(0.5)
    
    results.append(("性能对比", test_performance()))
    
    # 汇总结果
    print_section("测试结果汇总")
    
    passed = 0
    failed = 0
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n总计: {passed} 通过, {failed} 失败")
    
    if failed == 0:
        print("\n🎉 所有测试通过！增强功能正常工作。")
        return 0
    else:
        print(f"\n⚠️  有 {failed} 个测试失败，请检查服务状态。")
        return 1

if __name__ == "__main__":
    exit(main())
