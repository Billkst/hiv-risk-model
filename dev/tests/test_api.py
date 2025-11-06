"""
API测试脚本
用于验证API服务是否正常工作
"""

import requests
import json
import time

# API基础URL
BASE_URL = "http://localhost:5000"

def print_section(title):
    """打印分隔线"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_health():
    """测试健康检查"""
    print_section("测试1: 健康检查")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'healthy' and data.get('model_loaded'):
                print("✓ 健康检查通过")
                return True
        
        print("✗ 健康检查失败")
        return False
        
    except Exception as e:
        print(f"✗ 请求失败: {e}")
        return False

def test_model_info():
    """测试获取模型信息"""
    print_section("测试2: 获取模型信息")
    
    try:
        response = requests.get(f"{BASE_URL}/v1/model/info", timeout=5)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"模型名称: {data.get('model_name')}")
            print(f"模型版本: {data.get('model_version')}")
            print(f"特征数量: {data.get('feature_count')}")
            print(f"风险等级: {json.dumps(data.get('risk_levels'), indent=2, ensure_ascii=False)}")
            print("✓ 模型信息获取成功")
            return True
        
        print("✗ 模型信息获取失败")
        return False
        
    except Exception as e:
        print(f"✗ 请求失败: {e}")
        return False

def test_predict_single():
    """测试单样本预测"""
    print_section("测试3: 单样本预测")
    
    # 准备测试数据（简化版，实际需要110个特征）
    features = {
        "存活数": 1000,
        "感染率": 0.5,
        "治疗覆盖率": 85.0,
        "30天治疗比例": 90.0,
        "检测比例": 95.0,
        "病毒抑制比例": 92.0,
        "新报告": 50,
        "人口数": 500000
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/v1/predict",
            headers={"Content-Type": "application/json"},
            json={"features": features},
            timeout=10
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                pred = data.get('prediction', {})
                print(f"\n预测结果:")
                print(f"  风险等级: {pred.get('risk_level')}")
                print(f"  风险描述: {pred.get('risk_description')}")
                print(f"  风险分数: {pred.get('risk_score')}")
                print(f"  置信度: {pred.get('confidence_percent')}")
                print("✓ 单样本预测成功")
                return True
        
        print("✗ 单样本预测失败")
        return False
        
    except Exception as e:
        print(f"✗ 请求失败: {e}")
        return False

def test_predict_batch():
    """测试批量预测"""
    print_section("测试4: 批量预测")
    
    # 准备测试数据
    samples = [
        {
            "存活数": 1000,
            "感染率": 0.5,
            "治疗覆盖率": 85.0,
            "新报告": 50,
            "人口数": 500000
        },
        {
            "存活数": 2000,
            "感染率": 0.3,
            "治疗覆盖率": 90.0,
            "新报告": 30,
            "人口数": 800000
        }
    ]
    
    try:
        response = requests.post(
            f"{BASE_URL}/v1/predict/batch",
            headers={"Content-Type": "application/json"},
            json={"samples": samples},
            timeout=10
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"总样本数: {data.get('total')}")
                print(f"\n预测结果:")
                for pred in data.get('predictions', []):
                    if pred.get('success'):
                        print(f"  样本{pred.get('index')}: "
                              f"等级{pred.get('risk_level')} - "
                              f"{pred.get('risk_description')} "
                              f"(分数: {pred.get('risk_score'):.2f})")
                print("✓ 批量预测成功")
                return True
        
        print("✗ 批量预测失败")
        return False
        
    except Exception as e:
        print(f"✗ 请求失败: {e}")
        return False

def test_performance():
    """测试性能"""
    print_section("测试5: 性能测试")
    
    features = {
        "存活数": 1000,
        "感染率": 0.5,
        "治疗覆盖率": 85.0
    }
    
    n_requests = 10
    times = []
    
    print(f"发送 {n_requests} 个请求...")
    
    for i in range(n_requests):
        try:
            start = time.time()
            response = requests.post(
                f"{BASE_URL}/v1/predict",
                headers={"Content-Type": "application/json"},
                json={"features": features},
                timeout=10
            )
            elapsed = (time.time() - start) * 1000  # 转换为毫秒
            
            if response.status_code == 200:
                times.append(elapsed)
                print(f"  请求 {i+1}: {elapsed:.2f}ms")
        except Exception as e:
            print(f"  请求 {i+1}: 失败 - {e}")
    
    if times:
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"\n性能统计:")
        print(f"  平均响应时间: {avg_time:.2f}ms")
        print(f"  最快响应时间: {min_time:.2f}ms")
        print(f"  最慢响应时间: {max_time:.2f}ms")
        print(f"  成功率: {len(times)}/{n_requests} ({len(times)/n_requests*100:.1f}%)")
        
        if avg_time < 100:
            print("✓ 性能测试通过 (平均响应时间 < 100ms)")
            return True
        else:
            print("⚠ 性能测试警告 (平均响应时间 > 100ms)")
            return True
    
    print("✗ 性能测试失败")
    return False

def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("  HIV风险评估API - 自动化测试")
    print("="*60)
    print(f"  目标地址: {BASE_URL}")
    print("="*60)
    
    results = []
    
    # 运行测试
    results.append(("健康检查", test_health()))
    time.sleep(1)
    
    results.append(("模型信息", test_model_info()))
    time.sleep(1)
    
    results.append(("单样本预测", test_predict_single()))
    time.sleep(1)
    
    results.append(("批量预测", test_predict_batch()))
    time.sleep(1)
    
    results.append(("性能测试", test_performance()))
    
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
        print("\n🎉 所有测试通过！API服务运行正常。")
        return 0
    else:
        print(f"\n⚠️  有 {failed} 个测试失败，请检查服务状态。")
        return 1

if __name__ == "__main__":
    exit(main())
