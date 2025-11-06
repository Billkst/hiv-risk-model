# HIV风险评估模型 - API接口文档

## 📋 目录
- [接口概述](#接口概述)
- [认证方式](#认证方式)
- [接口列表](#接口列表)
- [请求示例](#请求示例)
- [错误码](#错误码)
- [SDK示例](#sdk示例)

---

## 接口概述

### 基础信息
- **Base URL**: `http://<服务器IP>:5000`
- **API版本**: v1
- **数据格式**: JSON
- **字符编码**: UTF-8

### 通用响应格式

**成功响应**:
```json
{
  "success": true,
  "data": { ... },
  "timestamp": "2024-01-01T12:00:00.000000"
}
```

**错误响应**:
```json
{
  "success": false,
  "error": "错误描述",
  "timestamp": "2024-01-01T12:00:00.000000"
}
```

---

## 认证方式

当前版本暂不需要认证。生产环境建议添加以下认证方式之一：

- **API Key**: 在请求头中添加 `X-API-Key`
- **Bearer Token**: 在请求头中添加 `Authorization: Bearer <token>`

---

## 接口列表

### 1. API首页

获取API基本信息和可用端点列表。

**接口地址**: `GET /`

**请求参数**: 无

**响应示例**:
```json
{
  "service": "HIV Risk Assessment API",
  "version": "v1",
  "model_version": "1.0.0",
  "status": "running",
  "endpoints": {
    "health": "/health",
    "predict_single": "/v1/predict",
    "predict_batch": "/v1/predict/batch",
    "model_info": "/v1/model/info"
  }
}
```

---

### 2. 健康检查

检查服务运行状态。

**接口地址**: `GET /health`

**请求参数**: 无

**响应示例**:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "timestamp": "2024-01-01T12:00:00.000000"
}
```

**状态说明**:
- `healthy`: 服务正常
- `unhealthy`: 服务异常
- `model_loaded`: 模型是否已加载

---

### 3. 获取模型信息

获取模型详细信息和特征列表。

**接口地址**: `GET /v1/model/info`

**请求参数**: 无

**响应示例**:
```json
{
  "model_name": "Gradient Boosting",
  "model_version": "1.0.0",
  "feature_count": 110,
  "features": [
    "存活数",
    "感染率",
    "治疗覆盖率",
    "..."
  ],
  "risk_levels": {
    "1": "极低风险 (0-20分)",
    "2": "低风险 (20-40分)",
    "3": "中等风险 (40-60分)",
    "4": "高风险 (60-80分)",
    "5": "极高风险 (80-100分)"
  }
}
```

---

### 4. 单样本预测

对单个区县进行风险评估。

**接口地址**: `POST /v1/predict`

**请求头**:
```
Content-Type: application/json
```

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| features | Object | 是 | 特征字典 |

**features对象包含的字段** (110个特征，以下为主要特征):

| 字段名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| 存活数 | Number | HIV感染者存活人数 | 1000 |
| 感染率 | Number | 感染率(%) | 0.5 |
| 治疗覆盖率 | Number | 治疗覆盖率(%) | 85.0 |
| 30天治疗比例 | Number | 30天内开始治疗的比例(%) | 90.0 |
| 检测比例 | Number | 检测覆盖率(%) | 95.0 |
| 病毒抑制比例 | Number | 病毒抑制率(%) | 92.0 |
| 新报告 | Number | 新报告病例数 | 50 |
| 人口数 | Number | 区县总人口 | 500000 |
| ... | ... | 其他特征 | ... |

**完整特征列表**: 请调用 `/v1/model/info` 接口获取

**请求示例**:
```json
{
  "features": {
    "存活数": 1000,
    "感染率": 0.5,
    "存活_0-": 0.0,
    "存活_5-": 0.0,
    "存活_10-": 0.0,
    "存活_15-": 1.0,
    "存活_20-": 2.5,
    "存活_25-": 5.0,
    "存活_30-": 8.0,
    "存活_35-": 10.0,
    "存活_40-": 12.0,
    "存活_45-": 15.0,
    "存活_50-": 14.0,
    "存活_55-": 12.0,
    "存活_60-": 8.0,
    "存活_65-": 6.0,
    "存活_70-": 4.0,
    "存活_75-": 2.0,
    "存活_80-": 1.0,
    "治疗覆盖率": 85.0,
    "30天治疗比例": 90.0,
    "检测比例": 95.0,
    "病毒抑制比例": 92.0,
    "新报告": 50,
    "人口数": 500000
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "prediction": {
    "risk_level": 3,
    "risk_description": "中等风险",
    "risk_score": 52.34,
    "confidence": 0.9234,
    "confidence_percent": "92.34%"
  },
  "timestamp": "2024-01-01T12:00:00.000000"
}
```

**响应字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| risk_level | Integer | 风险等级 (1-5) |
| risk_description | String | 风险描述 |
| risk_score | Float | 风险分数 (0-100) |
| confidence | Float | 预测置信度 (0-1) |
| confidence_percent | String | 置信度百分比 |

---

### 5. 批量预测

对多个区县进行批量风险评估。

**接口地址**: `POST /v1/predict/batch`

**请求头**:
```
Content-Type: application/json
```

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| samples | Array | 是 | 样本数组，每个元素为特征字典 |

**请求示例**:
```json
{
  "samples": [
    {
      "存活数": 1000,
      "感染率": 0.5,
      "治疗覆盖率": 85.0,
      "30天治疗比例": 90.0,
      "检测比例": 95.0,
      "病毒抑制比例": 92.0,
      "新报告": 50,
      "人口数": 500000
    },
    {
      "存活数": 2000,
      "感染率": 0.3,
      "治疗覆盖率": 90.0,
      "30天治疗比例": 95.0,
      "检测比例": 98.0,
      "病毒抑制比例": 95.0,
      "新报告": 30,
      "人口数": 800000
    }
  ]
}
```

**响应示例**:
```json
{
  "success": true,
  "total": 2,
  "predictions": [
    {
      "index": 0,
      "success": true,
      "risk_level": 3,
      "risk_description": "中等风险",
      "risk_score": 52.34,
      "confidence": 0.9234
    },
    {
      "index": 1,
      "success": true,
      "risk_level": 2,
      "risk_description": "低风险",
      "risk_score": 28.56,
      "confidence": 0.9567
    }
  ],
  "timestamp": "2024-01-01T12:00:00.000000"
}
```

---

## 错误码

| HTTP状态码 | 错误码 | 说明 |
|-----------|--------|------|
| 200 | - | 请求成功 |
| 400 | BAD_REQUEST | 请求参数错误 |
| 404 | NOT_FOUND | 接口不存在 |
| 500 | INTERNAL_ERROR | 服务器内部错误 |
| 503 | SERVICE_UNAVAILABLE | 服务不可用 |

**错误响应示例**:
```json
{
  "success": false,
  "error": "缺少features字段",
  "timestamp": "2024-01-01T12:00:00.000000"
}
```

---

## SDK示例

### Python示例

```python
import requests
import json

# API基础URL
BASE_URL = "http://localhost:5000"

# 1. 健康检查
def health_check():
    response = requests.get(f"{BASE_URL}/health")
    print(response.json())

# 2. 获取模型信息
def get_model_info():
    response = requests.get(f"{BASE_URL}/v1/model/info")
    return response.json()

# 3. 单样本预测
def predict_single(features):
    url = f"{BASE_URL}/v1/predict"
    headers = {"Content-Type": "application/json"}
    data = {"features": features}
    
    response = requests.post(url, headers=headers, json=data)
    return response.json()

# 4. 批量预测
def predict_batch(samples):
    url = f"{BASE_URL}/v1/predict/batch"
    headers = {"Content-Type": "application/json"}
    data = {"samples": samples}
    
    response = requests.post(url, headers=headers, json=data)
    return response.json()

# 使用示例
if __name__ == "__main__":
    # 准备特征数据
    features = {
        "存活数": 1000,
        "感染率": 0.5,
        "治疗覆盖率": 85.0,
        # ... 其他特征
    }
    
    # 单样本预测
    result = predict_single(features)
    print(f"风险等级: {result['prediction']['risk_level']}")
    print(f"风险分数: {result['prediction']['risk_score']}")
    print(f"风险描述: {result['prediction']['risk_description']}")
```

### JavaScript示例

```javascript
// API基础URL
const BASE_URL = "http://localhost:5000";

// 1. 健康检查
async function healthCheck() {
  const response = await fetch(`${BASE_URL}/health`);
  const data = await response.json();
  console.log(data);
}

// 2. 单样本预测
async function predictSingle(features) {
  const response = await fetch(`${BASE_URL}/v1/predict`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ features })
  });
  
  return await response.json();
}

// 3. 批量预测
async function predictBatch(samples) {
  const response = await fetch(`${BASE_URL}/v1/predict/batch`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ samples })
  });
  
  return await response.json();
}

// 使用示例
const features = {
  "存活数": 1000,
  "感染率": 0.5,
  "治疗覆盖率": 85.0
  // ... 其他特征
};

predictSingle(features).then(result => {
  console.log('风险等级:', result.prediction.risk_level);
  console.log('风险分数:', result.prediction.risk_score);
  console.log('风险描述:', result.prediction.risk_description);
});
```

### cURL示例

```bash
# 1. 健康检查
curl http://localhost:5000/health

# 2. 获取模型信息
curl http://localhost:5000/v1/model/info

# 3. 单样本预测
curl -X POST http://localhost:5000/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "features": {
      "存活数": 1000,
      "感染率": 0.5,
      "治疗覆盖率": 85.0
    }
  }'

# 4. 批量预测
curl -X POST http://localhost:5000/v1/predict/batch \
  -H "Content-Type: application/json" \
  -d '{
    "samples": [
      {"存活数": 1000, "感染率": 0.5},
      {"存活数": 2000, "感染率": 0.3}
    ]
  }'
```

---

## 性能指标

- **响应时间**: < 50ms (单次预测)
- **并发能力**: 100+ QPS
- **批量处理**: 支持单次最多1000个样本

---

## 注意事项

1. **特征完整性**: 确保提供所有110个特征，缺失特征将使用默认值0
2. **数据格式**: 所有数值类型特征应为Number类型
3. **请求大小**: 单次请求建议不超过10MB
4. **超时设置**: 建议设置请求超时时间为30秒

---

## 更新日志

### v1.0.0 (2024-01-01)
- 初始版本发布
- 支持单样本和批量预测
- 提供5级风险评估

---

## 技术支持

如有问题，请联系技术支持团队。

**文档版本**: 1.0.0  
**最后更新**: 2024-01-01
