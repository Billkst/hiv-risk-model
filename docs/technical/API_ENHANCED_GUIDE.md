# HIV风险评估API - 增强功能使用指南

**版本**: 1.1  
**更新日期**: 2025-11-04

---

## 🆕 新增功能

### 1. 特征贡献度分析

在预测结果中查看每个特征对风险评估的贡献，帮助理解模型决策。

### 2. 全局特征重要性

获取模型中最重要的特征排名，了解哪些因素对风险评估影响最大。

---

## 📡 API端点

### 1. 单样本预测（增强版）

**端点**: `POST /v1/predict`

**新增参数**:
- `include_contributions` (boolean, 可选): 是否包含特征贡献度分析，默认 `false`

**请求示例**:

```bash
curl -X POST http://localhost:5000/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "features": {
      "存活数": 1200,
      "新报告": 80,
      "感染率": 0.12,
      "治疗覆盖率": 92.0,
      "病毒抑制比例": 88.0
    },
    "include_contributions": true
  }'
```

**响应示例**:

```json
{
  "success": true,
  "prediction": {
    "risk_level": 3,
    "risk_description": "中等风险",
    "risk_score": 52.3,
    "confidence": 0.85,
    "confidence_percent": "85.00%"
  },
  "feature_contributions": {
    "base_value": 0.0,
    "prediction": 3.0,
    "method": "fast_approximate",
    "top_positive": [
      {
        "feature": "存活数",
        "value": 1200.0,
        "contribution": 0.38
      },
      {
        "feature": "新报告",
        "value": 80.0,
        "contribution": 0.29
      }
    ],
    "top_negative": [
      {
        "feature": "治疗覆盖率",
        "value": 92.0,
        "contribution": -0.22
      }
    ],
    "all_contributions": [...]
  },
  "timestamp": "2025-11-04T08:00:00"
}
```

**字段说明**:

- `base_value`: 基准预测值（所有区县的平均风险）
- `prediction`: 当前样本的预测值
- `method`: 计算方法（fast_approximate = 快速近似）
- `top_positive`: Top 5 正贡献特征（增加风险的因素）
- `top_negative`: Top 5 负贡献特征（降低风险的因素）
- `all_contributions`: 所有110个特征的贡献值数组

---

### 2. 全局特征重要性（新增）

**端点**: `GET /v1/model/feature_importance`

**查询参数**:
- `top_k` (integer, 可选): 返回Top K个特征，默认 `20`，范围 `1-110`

**请求示例**:

```bash
curl "http://localhost:5000/v1/model/feature_importance?top_k=10"
```

**响应示例**:

```json
{
  "success": true,
  "top_k": 10,
  "total_features": 110,
  "feature_importance": [
    {
      "rank": 1,
      "feature": "存活数",
      "importance": 0.1985,
      "importance_normalized": 19.85
    },
    {
      "rank": 2,
      "feature": "新报告",
      "importance": 0.1812,
      "importance_normalized": 18.12
    },
    {
      "rank": 3,
      "feature": "病载小于50占现存活比例",
      "importance": 0.0705,
      "importance_normalized": 7.05
    }
  ],
  "timestamp": "2025-11-04T08:00:00"
}
```

**字段说明**:

- `rank`: 重要性排名
- `feature`: 特征名称
- `importance`: 重要性分数（绝对值）
- `importance_normalized`: 归一化百分比

---

## 💻 使用示例

### Python

```python
import requests
import json

BASE_URL = "http://localhost:5000"

# 1. 基础预测（向后兼容）
response = requests.post(f"{BASE_URL}/v1/predict", json={
    "features": {
        "存活数": 1200,
        "新报告": 80,
        "感染率": 0.12,
        "治疗覆盖率": 92.0
    }
})
result = response.json()
print(f"风险等级: {result['prediction']['risk_level']}")
print(f"风险描述: {result['prediction']['risk_description']}")

# 2. 增强预测（含特征贡献度）
response = requests.post(f"{BASE_URL}/v1/predict", json={
    "features": {
        "存活数": 1200,
        "新报告": 80,
        "感染率": 0.12,
        "治疗覆盖率": 92.0
    },
    "include_contributions": True  # 启用特征贡献度
})
result = response.json()

# 查看预测结果
pred = result['prediction']
print(f"\n风险等级: {pred['risk_level']} - {pred['risk_description']}")
print(f"风险分数: {pred['risk_score']:.2f}")
print(f"置信度: {pred['confidence_percent']}")

# 查看特征贡献度
if 'feature_contributions' in result:
    contrib = result['feature_contributions']
    
    print(f"\nTop 5 正贡献特征（增加风险）:")
    for f in contrib['top_positive']:
        print(f"  {f['feature']:30s}: {f['value']:8.2f} → +{f['contribution']:7.4f}")
    
    print(f"\nTop 5 负贡献特征（降低风险）:")
    for f in contrib['top_negative']:
        print(f"  {f['feature']:30s}: {f['value']:8.2f} → {f['contribution']:7.4f}")

# 3. 获取全局特征重要性
response = requests.get(f"{BASE_URL}/v1/model/feature_importance?top_k=10")
importance = response.json()

print(f"\nTop 10 最重要特征:")
for f in importance['feature_importance']:
    print(f"  {f['rank']:2d}. {f['feature']:30s}: {f['importance']:7.4f} ({f['importance_normalized']:5.2f}%)")
```

### JavaScript

```javascript
const BASE_URL = "http://localhost:5000";

// 1. 基础预测
async function basicPredict() {
  const response = await fetch(`${BASE_URL}/v1/predict`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      features: {
        "存活数": 1200,
        "新报告": 80,
        "感染率": 0.12,
        "治疗覆盖率": 92.0
      }
    })
  });
  
  const result = await response.json();
  console.log('风险等级:', result.prediction.risk_level);
  console.log('风险描述:', result.prediction.risk_description);
}

// 2. 增强预测（含特征贡献度）
async function enhancedPredict() {
  const response = await fetch(`${BASE_URL}/v1/predict`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      features: {
        "存活数": 1200,
        "新报告": 80,
        "感染率": 0.12,
        "治疗覆盖率": 92.0
      },
      include_contributions: true  // 启用特征贡献度
    })
  });
  
  const result = await response.json();
  
  // 查看预测结果
  console.log('风险等级:', result.prediction.risk_level);
  console.log('风险分数:', result.prediction.risk_score);
  
  // 查看特征贡献度
  if (result.feature_contributions) {
    console.log('\nTop 5 正贡献特征:');
    result.feature_contributions.top_positive.forEach(f => {
      console.log(`  ${f.feature}: ${f.value} → +${f.contribution}`);
    });
  }
}

// 3. 获取全局特征重要性
async function getFeatureImportance() {
  const response = await fetch(`${BASE_URL}/v1/model/feature_importance?top_k=10`);
  const result = await response.json();
  
  console.log('Top 10 最重要特征:');
  result.feature_importance.forEach(f => {
    console.log(`  ${f.rank}. ${f.feature}: ${f.importance} (${f.importance_normalized}%)`);
  });
}
```

---

## 🎯 应用场景

### 场景1: 理解预测结果

**问题**: 为什么这个区县被评为高风险？

**解决方案**: 使用特征贡献度分析

```python
# 请求时启用 include_contributions=True
result = predict_with_contributions(features)

# 查看Top 5正贡献特征
for f in result['feature_contributions']['top_positive']:
    print(f"{f['feature']}: 贡献度 +{f['contribution']}")

# 输出示例:
# 存活数: 贡献度 +0.82
# 新报告: 贡献度 +0.65
# 感染率: 贡献度 +0.48
```

**结论**: 存活数多、新报告多、感染率高是主要风险因素

---

### 场景2: 制定干预措施

**问题**: 应该优先改善哪些指标？

**解决方案**: 结合特征贡献度和特征重要性

```python
# 1. 查看当前区县的负贡献特征（保护因素）
negative_features = result['feature_contributions']['top_negative']

# 2. 查看全局最重要特征
importance = get_feature_importance(top_k=20)

# 3. 找出重要但贡献不足的特征
# 例如: 治疗覆盖率很重要，但当前区县只有85%
# 建议: 提高治疗覆盖率到95%以上
```

---

### 场景3: 对比不同区县

**问题**: 为什么A区县是低风险，B区县是高风险？

**解决方案**: 对比两个区县的特征贡献度

```python
# 预测A区县
result_A = predict_with_contributions(features_A)

# 预测B区县
result_B = predict_with_contributions(features_B)

# 对比主要差异
compare_contributions(result_A, result_B)

# 输出示例:
# A区县: 治疗覆盖率 98% → -0.35 (降低风险)
# B区县: 治疗覆盖率 85% → -0.15 (降低风险较少)
# 差异: B区县治疗覆盖率不足，应加强
```

---

## ⚡ 性能说明

### 响应时间

- **基础预测**: ~45ms
- **增强预测（含特征贡献度）**: ~47ms
- **特征重要性**: ~1ms

### 性能开销

- 特征贡献度计算开销: +2ms
- 满足实时响应要求 ✅

### 优化建议

1. **按需使用**: 仅在需要解释时启用 `include_contributions=True`
2. **缓存结果**: 全局特征重要性可以缓存，不需要每次请求
3. **批量处理**: 如果需要分析多个样本，考虑批量请求

---

## 🔄 向后兼容

### 默认行为不变

```python
# 旧代码无需修改，仍然正常工作
response = requests.post('/v1/predict', json={'features': {...}})
# 不包含 feature_contributions 字段
```

### 可选启用新功能

```python
# 需要时显式启用
response = requests.post('/v1/predict', json={
    'features': {...},
    'include_contributions': True  # 新增参数
})
# 包含 feature_contributions 字段
```

---

## 📊 输出解读

### 特征贡献度

**正贡献（+）**: 该特征使风险等级升高
- 例如: 存活数 +0.38 → 存活数多导致风险增加

**负贡献（-）**: 该特征使风险等级降低
- 例如: 治疗覆盖率 -0.22 → 治疗覆盖率高降低风险

**贡献度大小**: 影响的强度
- |贡献度| > 0.3: 强影响
- 0.1 < |贡献度| < 0.3: 中等影响
- |贡献度| < 0.1: 弱影响

### 特征重要性

**重要性分数**: 该特征在所有预测中的平均影响

**归一化百分比**: 该特征占总重要性的比例

**Top 10特征**: 对模型预测影响最大的10个因素

---

## 🆘 常见问题

### Q1: 为什么有些特征贡献度为0？

**A**: 该特征的值为0或对当前样本影响很小。

### Q2: 特征贡献度总和等于什么？

**A**: `sum(all_contributions) ≈ prediction - base_value`

### Q3: 如何判断一个区县的主要风险因素？

**A**: 查看 `top_positive` 中贡献度最大的特征。

### Q4: 特征重要性会变化吗？

**A**: 不会，特征重要性是模型训练时确定的，对所有样本相同。

### Q5: 性能开销可以接受吗？

**A**: 是的，仅增加约2ms，满足实时响应要求。

---

## 📞 技术支持

如有问题，请联系：
- 邮箱: [email]
- 文档: 查看 `MODEL_INTERPRETABILITY.md` 了解更多

---

**文档版本**: 1.1  
**最后更新**: 2025-11-04  
**维护者**: 刘俊希
