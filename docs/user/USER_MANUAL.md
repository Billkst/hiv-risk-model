# HIV风险评估模型 - 用户手册

## 📋 目录

1. [系统介绍](#系统介绍)
2. [快速上手](#快速上手)
3. [功能详解](#功能详解)
4. [实际应用](#实际应用)
5. [常见问题](#常见问题)
6. [技术支持](#技术支持)

---

## 系统介绍

### 什么是HIV风险评估模型？

HIV风险评估模型是一个基于人工智能的智能决策支持系统，专为疾控部门设计，用于评估不同区县的HIV传播风险等级。

### 系统特点

- 🎯 **准确性高**: 采用先进的机器学习算法，预测准确率超过89%
- 🔍 **可解释性强**: 提供详细的风险因素分析和特征贡献度
- ⚡ **响应快速**: 单次预测响应时间<50ms
- 🌐 **易于集成**: 提供标准的RESTful API接口
- 📊 **可视化丰富**: 支持多种图表和报告格式

### 适用对象

- 疾控中心工作人员
- 公共卫生决策者
- 流行病学研究人员
- 卫生政策制定者

### 风险等级说明

系统将风险分为5个等级：

| 等级 | 分数范围 | 描述 | 建议措施 |
|------|---------|------|---------|
| **1级** | 0-20 | 极低风险 | 维持常规监测 |
| **2级** | 20-40 | 低风险 | 保持现有防控措施 |
| **3级** | 40-60 | 中等风险 | 加强监测和干预 |
| **4级** | 60-80 | 高风险 | 重点防控和资源投入 |
| **5级** | 80-100 | 极高风险 | 紧急干预和全面防控 |

---

## 快速上手

### 第一步：访问系统

系统提供Web API接口，可通过以下方式访问：

```
基础地址: http://your-server:5000
API版本: v1
```

### 第二步：健康检查

首先验证系统是否正常运行：

```bash
curl http://your-server:5000/health
```

正常响应：
```json
{
  "status": "healthy",
  "model_loaded": true,
  "timestamp": "2025-11-04T10:00:00.000000"
}
```

### 第三步：获取系统信息

了解系统版本和功能：

```bash
curl http://your-server:5000/v1/model/info
```

### 第四步：进行第一次预测

使用示例数据进行预测：

```bash
curl -X POST http://your-server:5000/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "features": {
      "存活数": 1000,
      "感染率": 0.5,
      "治疗覆盖率": 85.0,
      "新报告": 50,
      "人口数": 500000
    }
  }'
```

---

## 功能详解

### 1. 基础风险预测

**功能说明**: 根据输入的区县特征数据，预测HIV传播风险等级。

**输入参数**:
- `features`: 包含110个特征的字典（至少提供关键特征）

**输出结果**:
- `risk_level`: 风险等级（1-5级）
- `risk_description`: 风险描述
- `risk_score`: 风险分数（0-100）
- `confidence`: 预测置信度

**使用示例**:

```python
import requests

response = requests.post('http://your-server:5000/v1/predict', json={
    'features': {
        '存活数': 1000,
        '感染率': 0.5,
        '治疗覆盖率': 85.0,
        # ... 其他特征
    }
})

result = response.json()
print(f"风险等级: {result['prediction']['risk_level']}")
print(f"风险描述: {result['prediction']['risk_description']}")
print(f"风险分数: {result['prediction']['risk_score']:.2f}")
```

### 2. 特征贡献度分析

**功能说明**: 分析每个特征对预测结果的贡献程度，帮助理解风险成因。

**启用方法**: 在预测请求中添加 `"include_contributions": true`

**输出结果**:
- `top_positive`: Top 5增加风险的特征
- `top_negative`: Top 5降低风险的特征
- `all_contributions`: 所有110个特征的贡献值

**使用示例**:

```python
response = requests.post('http://your-server:5000/v1/predict', json={
    'features': features,
    'include_contributions': True
})

result = response.json()
print("主要风险因素:")
for contrib in result['feature_contributions']['top_positive']:
    print(f"  {contrib['feature']}: {contrib['contribution']:.2f}")
```

**解读说明**:
- **正贡献值**: 该特征增加了风险
- **负贡献值**: 该特征降低了风险
- **贡献值大小**: 表示影响程度

### 3. 注意力权重分析（增强功能）

**功能说明**: 显示AI模型在不同疫情阶段关注的重点特征。

**启用方法**: 在预测请求中添加 `"include_attention": true` 和 `"use_enhanced": true`

**输出结果**:
- `top_10_features`: 模型最关注的10个特征
- `weights`: 所有特征的注意力权重

**权重解读**:
- **权重>1.0**: 模型给予该特征更多关注
- **权重=1.0**: 正常关注水平
- **权重<1.0**: 模型给予该特征较少关注

### 4. 批量预测

**功能说明**: 同时预测多个区县的风险等级。

**使用场景**: 
- 省级疾控中心评估所有区县
- 定期风险评估报告
- 大规模筛查

**使用示例**:

```python
samples = [
    {'存活数': 1000, '感染率': 0.5, ...},  # 区县A
    {'存活数': 2000, '感染率': 0.3, ...},  # 区县B
    {'存活数': 1500, '感染率': 0.4, ...},  # 区县C
]

response = requests.post('http://your-server:5000/v1/predict/batch', json={
    'samples': samples
})

result = response.json()
for i, pred in enumerate(result['predictions']):
    print(f"区县{i+1}: 风险等级{pred['risk_level']}")
```

### 5. 全局特征重要性

**功能说明**: 查看模型认为最重要的特征排名。

**使用场景**:
- 了解模型决策依据
- 指导数据收集重点
- 政策制定参考

**使用示例**:

```python
response = requests.get('http://your-server:5000/v1/model/feature_importance?top_k=10')
result = response.json()

print("最重要的10个特征:")
for item in result['feature_importance']:
    print(f"  {item['rank']}. {item['feature']}: {item['importance_normalized']:.2f}%")
```

---

## 实际应用

### 应用场景1：日常风险监测

**背景**: 疾控中心需要定期评估辖区内各区县的HIV传播风险。

**操作流程**:
1. 收集各区县的疫情数据
2. 使用批量预测接口评估所有区县
3. 根据风险等级制定防控策略
4. 生成风险评估报告

### 应用场景2：风险因素深度分析

**背景**: 某区县风险等级较高，需要分析具体的风险因素。

**操作流程**:
1. 获取该区县的详细数据
2. 使用增强预测功能
3. 分析特征贡献度和注意力权重
4. 制定针对性干预措施

**示例代码**:

```python
# 获取详细分析
response = requests.post('http://your-server:5000/v1/predict', json={
    'features': county_features,
    'include_contributions': True,
    'include_attention': True
})

result = response.json()
print(f"风险等级: {result['prediction']['risk_level']}")
print(f"风险分数: {result['prediction']['risk_score']:.2f}")

print("\n主要风险因素:")
for contrib in result['feature_contributions']['top_positive']:
    print(f"  {contrib['feature']}: {contrib['value']} (贡献度: {contrib['contribution']:.2f})")

print("\n模型关注重点:")
for item in result['attention_weights']['top_10_features']:
    print(f"  {item['feature']}: 权重 {item['weight']:.2f}")
```

### 应用场景3：政策效果评估

**背景**: 实施某项防控政策后，评估政策效果。

**操作流程**:
1. 收集政策实施前后的数据
2. 分别进行风险预测
3. 对比风险等级变化
4. 分析关键指标改善情况

---

## 常见问题

### Q1: 如何理解风险等级？

**A**: 风险等级分为1-5级：
- **1-2级**: 风险较低，维持常规防控措施
- **3级**: 中等风险，需要加强监测和干预
- **4-5级**: 高风险，需要紧急干预和重点防控

### Q2: 特征贡献度如何解读？

**A**: 特征贡献度表示该特征对预测结果的影响：
- **正值**: 该特征增加了风险等级
- **负值**: 该特征降低了风险等级
- **绝对值大小**: 表示影响程度

例如：`存活数: +2.5` 表示存活数这个特征使风险等级增加了2.5。

### Q3: 注意力权重有什么意义？

**A**: 注意力权重反映模型在不同情况下的关注重点：
- **权重>1.0**: 模型认为该特征在当前情况下更重要
- **权重<1.0**: 模型认为该特征在当前情况下不太重要

这有助于理解模型的决策逻辑。

### Q4: 为什么同样的数据预测结果不同？

**A**: 可能的原因：
1. 使用了不同的模型版本（基础模型 vs 增强模型）
2. 输入数据有细微差别
3. 系统配置不同

建议检查：
- 模型版本信息（`/v1/model/info`）
- 输入数据格式
- 环境变量配置

### Q5: 如何提高预测准确性？

**A**: 建议：
1. **数据质量**: 确保输入数据准确、完整
2. **使用增强模型**: 设置 `"use_enhanced": true`
3. **定期更新**: 使用最新的疫情数据
4. **多指标参考**: 结合特征贡献度和注意力权重分析

### Q6: 批量预测有数量限制吗？

**A**: 建议：
- 单次批量预测不超过1000个样本
- 大量数据可分批处理
- 注意服务器内存和响应时间

### Q7: 如何处理缺失数据？

**A**: 系统会自动处理缺失数据：
- 数值型特征：使用0填充
- 分类型特征：使用默认值

建议尽量提供完整数据以获得最佳预测效果。

### Q8: 预测结果可以保存吗？

**A**: 系统不会自动保存预测结果，建议：
1. 客户端保存预测结果
2. 建立本地数据库记录
3. 定期导出历史数据

---

## 技术支持

### 联系方式

- **技术支持邮箱**: support@example.com
- **问题反馈**: 请通过系统管理员提交
- **紧急联系**: 7×24小时技术支持热线

### 常用资源

- 📋 [API文档](API_DOCUMENTATION.md) - 详细的接口说明
- 💻 [使用示例](API_USAGE_EXAMPLES.md) - 代码示例
- 🚀 [部署指南](DEPLOYMENT_GUIDE.md) - 系统部署
- 🔧 [交付清单](DELIVERY_CHECKLIST.md) - 部署检查

### 版本更新

- 系统会定期更新，增加新功能和改进性能
- 重要更新会提前通知用户
- 提供版本升级指导和支持

---

**用户手册版本**: 1.0.0  
**最后更新**: 2025-11-04  
**适用系统版本**: v1.1.0
