#!/bin/bash
# 快速测试脚本 - 正确显示中文

API_URL="http://localhost:5000"

# 定义JSON格式化函数（支持中文）
json_format() {
    python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2, ensure_ascii=False))"
}

echo "========================================================================"
echo "  HIV风险评估API - 快速测试"
echo "========================================================================"

# 1. 健康检查
echo ""
echo "1. 健康检查"
echo "------------------------------------------------------------------------"
curl -s $API_URL/health | json_format

# 2. 模型信息
echo ""
echo "2. 模型信息"
echo "------------------------------------------------------------------------"
curl -s $API_URL/v1/model/info | json_format

# 3. 基础预测
echo ""
echo "3. 基础预测"
echo "------------------------------------------------------------------------"
curl -s -X POST $API_URL/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "features": {
      "存活数": 1000,
      "感染率": 0.5,
      "治疗覆盖率": 85.0,
      "新报告": 50,
      "人口数": 500000
    }
  }' | json_format

# 4. 增强预测（含特征贡献度）
echo ""
echo "4. 增强预测（含特征贡献度）"
echo "------------------------------------------------------------------------"
curl -s -X POST $API_URL/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "features": {
      "存活数": 1200,
      "感染率": 0.12,
      "治疗覆盖率": 92.0,
      "新报告": 80,
      "人口数": 600000
    },
    "include_contributions": true
  }' | json_format

# 5. 增强预测（含注意力权重）
echo ""
echo "5. 增强预测（含注意力权重）"
echo "------------------------------------------------------------------------"
curl -s -X POST $API_URL/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "features": {
      "存活数": 1500,
      "感染率": 0.25,
      "治疗覆盖率": 78.0,
      "新报告": 120,
      "人口数": 800000
    },
    "include_contributions": true,
    "include_attention": true,
    "use_enhanced": true
  }' | json_format

# 6. 特征重要性
echo ""
echo "6. 特征重要性（Top 10）"
echo "------------------------------------------------------------------------"
curl -s "$API_URL/v1/model/feature_importance?top_k=10" | json_format

# 7. 批量预测
echo ""
echo "7. 批量预测（3个样本）"
echo "------------------------------------------------------------------------"
curl -s -X POST $API_URL/v1/predict/batch \
  -H "Content-Type: application/json" \
  -d '{
    "samples": [
      {"存活数": 1000, "感染率": 0.5, "治疗覆盖率": 85.0},
      {"存活数": 2000, "感染率": 0.3, "治疗覆盖率": 90.0},
      {"存活数": 1500, "感染率": 0.4, "治疗覆盖率": 88.0}
    ]
  }' | json_format

echo ""
echo "========================================================================"
echo "  ✓ 测试完成"
echo "========================================================================"
