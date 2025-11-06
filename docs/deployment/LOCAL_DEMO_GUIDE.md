# HIV风险评估模型 - 本地演示指南

## 🎯 快速演示流程

本文档提供完整的本地演示命令，所有命令都可以直接复制粘贴运行。

---

## 💡 重要提示

### 中文显示问题

如果使用 `python3 -m json.tool` 会将中文显示为Unicode编码（如 `\u6781\u4f4e\u98ce\u9669`）。

**解决方法**：使用以下命令正确显示中文：

```bash
# ❌ 错误方式（中文显示为编码）
curl http://localhost:5000/v1/predict ... | python3 -m json.tool

# ✅ 正确方式（正确显示中文）
curl http://localhost:5000/v1/predict ... | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2, ensure_ascii=False))"
```

**简化方法**：创建一个别名

```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
alias json='python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2, ensure_ascii=False))"'

# 使用别名
curl http://localhost:5000/v1/predict ... | json
```

---

## 📋 演示前准备

### 1. 检查环境

```bash
# 检查Python版本（需要3.9+）
python3 --version

# 检查conda是否安装
conda --version

# 检查当前目录
pwd
# 应该在项目根目录：.../hiv_project/hiv_risk_model
```

### 2. 创建Python环境

```bash
# 创建conda环境
conda create -n hivenv python=3.9 -y

# 激活环境
conda activate hivenv

# 安装依赖
pip install -r requirements.txt

# 验证安装
pip list | grep -E "flask|numpy|pandas|scikit-learn|shap"
```

---

## 🚀 演示流程

### 方式1: 使用API服务（推荐）

#### 步骤1: 启动API服务

```bash
# 在第一个终端窗口启动API
cd hiv_project/hiv_risk_model
conda activate hivenv
python3 api/app.py
```

**预期输出**:
```
 * Running on http://0.0.0.0:5000
 * Model loaded successfully
 * Enhanced model enabled: True
```

#### 步骤2: 测试API（在新终端）

**方式A: 使用快速测试脚本（推荐）**

```bash
# 打开新终端，进入项目目录
cd hiv_project/hiv_risk_model

# 运行快速测试脚本（自动测试所有功能，正确显示中文）
./quick_test.sh
```

**方式B: 手动测试各个接口**

```bash
# 打开新终端，进入项目目录
cd hiv_project/hiv_risk_model

# 1. 健康检查
curl http://localhost:5000/health

# 2. 获取模型信息（显示中文）
curl http://localhost:5000/v1/model/info | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2, ensure_ascii=False))"

# 3. 基础预测（显示中文）
curl -X POST http://localhost:5000/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "features": {
      "存活数": 1000,
      "感染率": 0.5,
      "治疗覆盖率": 85.0,
      "新报告": 50,
      "人口数": 500000
    }
  }' | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2, ensure_ascii=False))"

# 4. 增强预测（含特征贡献度，显示中文）
curl -X POST http://localhost:5000/v1/predict \
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
  }' | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2, ensure_ascii=False))"

# 5. 增强预测（含注意力权重，显示中文）
curl -X POST http://localhost:5000/v1/predict \
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
  }' | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2, ensure_ascii=False))"

# 6. 获取特征重要性（显示中文）
curl http://localhost:5000/v1/model/feature_importance?top_k=10 | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2, ensure_ascii=False))"

# 7. 批量预测（显示中文）
curl -X POST http://localhost:5000/v1/predict/batch \
  -H "Content-Type: application/json" \
  -d '{
    "samples": [
      {"存活数": 1000, "感染率": 0.5, "治疗覆盖率": 85.0},
      {"存活数": 2000, "感染率": 0.3, "治疗覆盖率": 90.0},
      {"存活数": 1500, "感染率": 0.4, "治疗覆盖率": 88.0}
    ]
  }' | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2, ensure_ascii=False))"
```

---

### 方式2: 使用Python脚本

#### 演示1: 基础预测

```bash
# 创建演示脚本
cat > demo_basic.py << 'EOF'
from models.predictor import HIVRiskPredictor

# 初始化预测器
predictor = HIVRiskPredictor('saved_models/final_model_3to5.pkl')

# 准备测试数据
features = {
    '存活数': 1000,
    '感染率': 0.5,
    '治疗覆盖率': 85.0,
    '新报告': 50,
    '人口数': 500000
}

# 进行预测
result = predictor.predict_single(features)

# 显示结果
print("\n" + "="*60)
print("  基础预测演示")
print("="*60)
print(f"\n风险等级: {result['risk_level_5']} - {result['risk_description']}")
print(f"风险分数: {result['risk_score']:.2f}")
print(f"置信度: {result['confidence_percent']}")
print("\n" + "="*60)
EOF

# 运行演示
python3 demo_basic.py
```

#### 演示2: 增强预测（含特征贡献度）

```bash
# 创建演示脚本
cat > demo_enhanced.py << 'EOF'
from models.predictor import HIVRiskPredictor

# 初始化预测器
predictor = HIVRiskPredictor('saved_models/final_model_3to5.pkl')

# 准备测试数据
features = {
    '存活数': 1200,
    '感染率': 0.12,
    '治疗覆盖率': 92.0,
    '新报告': 80,
    '人口数': 600000
}

# 进行增强预测
result = predictor.predict_single(features, include_contributions=True)

# 显示结果
print("\n" + "="*60)
print("  增强预测演示（含特征贡献度）")
print("="*60)
print(f"\n风险等级: {result['risk_level_5']} - {result['risk_description']}")
print(f"风险分数: {result['risk_score']:.2f}")
print(f"置信度: {result['confidence_percent']}")

if 'feature_contributions' in result:
    print("\n主要风险因素（Top 5正贡献）:")
    for contrib in result['feature_contributions']['top_positive'][:5]:
        print(f"  • {contrib['feature']}: {contrib['value']:.2f} → 贡献度 {contrib['contribution']:.4f}")
    
    print("\n主要保护因素（Top 5负贡献）:")
    for contrib in result['feature_contributions']['top_negative'][:5]:
        print(f"  • {contrib['feature']}: {contrib['value']:.2f} → 贡献度 {contrib['contribution']:.4f}")

print("\n" + "="*60)
EOF

# 运行演示
python3 demo_enhanced.py
```

#### 演示3: 完整增强预测（含注意力权重）

```bash
# 创建演示脚本
cat > demo_full.py << 'EOF'
from models.enhanced_predictor import EnhancedPredictor
import numpy as np

# 初始化增强预测器
predictor = EnhancedPredictor('saved_models/final_model_3to5.pkl')

# 准备测试数据
features = {
    '存活数': 1500,
    '感染率': 0.25,
    '治疗覆盖率': 78.0,
    '新报告': 120,
    '人口数': 800000
}

# 进行完整预测
result = predictor.predict_single(
    features, 
    include_contributions=True,
    return_attention=True
)

# 显示结果
print("\n" + "="*60)
print("  完整增强预测演示（DG-DAA）")
print("="*60)
print(f"\n风险等级: {result['risk_level_5']} - {result['risk_description']}")
print(f"风险分数: {result['risk_score']:.2f}")
print(f"置信度: {result['confidence_percent']}")

if 'feature_contributions' in result:
    print("\n主要风险因素（Top 5）:")
    for contrib in result['feature_contributions']['top_positive'][:5]:
        print(f"  • {contrib['feature']}: {contrib['value']:.2f} → 贡献度 {contrib['contribution']:.4f}")

if 'attention_weights' in result:
    print("\n模型关注重点（Top 10特征）:")
    for item in result['attention_weights']['top_10_features']:
        print(f"  • {item['feature']}: 权重 {item['weight']:.4f}")

print("\n" + "="*60)
EOF

# 运行演示
python3 demo_full.py
```

#### 演示4: 批量预测

```bash
# 创建演示脚本
cat > demo_batch.py << 'EOF'
from models.predictor import HIVRiskPredictor

# 初始化预测器
predictor = HIVRiskPredictor('saved_models/final_model_3to5.pkl')

# 准备多个区县的数据
samples = [
    {'存活数': 1000, '感染率': 0.5, '治疗覆盖率': 85.0, '新报告': 50},
    {'存活数': 2000, '感染率': 0.3, '治疗覆盖率': 90.0, '新报告': 80},
    {'存活数': 1500, '感染率': 0.4, '治疗覆盖率': 88.0, '新报告': 65},
    {'存活数': 800, '感染率': 0.6, '治疗覆盖率': 75.0, '新报告': 40},
    {'存活数': 3000, '感染率': 0.2, '治疗覆盖率': 95.0, '新报告': 100},
]

# 批量预测
results = predictor.predict_batch(samples)

# 显示结果
print("\n" + "="*60)
print("  批量预测演示（5个区县）")
print("="*60)
for i, result in enumerate(results, 1):
    print(f"\n区县{i}:")
    print(f"  风险等级: {result['risk_level_5']} - {result['risk_description']}")
    print(f"  风险分数: {result['risk_score']:.2f}")
    print(f"  置信度: {result['confidence_percent']}")

print("\n" + "="*60)
EOF

# 运行演示
python3 demo_batch.py
```

#### 演示5: 特征重要性分析

```bash
# 创建演示脚本
cat > demo_importance.py << 'EOF'
from models.predictor import HIVRiskPredictor

# 初始化预测器
predictor = HIVRiskPredictor('saved_models/final_model_3to5.pkl')

# 获取特征重要性
importance = predictor.get_feature_importance(top_k=20)

# 显示结果
print("\n" + "="*60)
print("  全局特征重要性分析（Top 20）")
print("="*60)
print("\n最重要的20个特征:")
for item in importance:
    print(f"  {item['rank']:2d}. {item['feature']:30s} {item['importance']:.4f} ({item['importance_normalized']:.2f}%)")

print("\n" + "="*60)
EOF

# 运行演示
python3 demo_importance.py
```

---

### 方式3: 使用Docker（可选）

```bash
# 1. 构建Docker镜像
docker build -t hiv-risk-api:v1.1.0 .

# 2. 运行容器
docker run -d -p 5000:5000 \
  -e USE_ENHANCED_MODEL=true \
  --name hiv-api \
  hiv-risk-api:v1.1.0

# 3. 查看日志
docker logs -f hiv-api

# 4. 测试（在新终端）
curl http://localhost:5000/health

# 5. 停止容器
docker stop hiv-api

# 6. 删除容器
docker rm hiv-api
```

---

## 📊 演示场景

### 场景1: 低风险区县

```bash
python3 << 'EOF'
from models.enhanced_predictor import EnhancedPredictor

predictor = EnhancedPredictor('saved_models/final_model_3to5.pkl')

# 低风险区县特征
features = {
    '存活数': 500,
    '感染率': 0.1,
    '治疗覆盖率': 95.0,
    '新报告': 20,
    '人口数': 400000,
    '筛查人数': 50000,
    '干预人数': 10000
}

result = predictor.predict_single(features, include_contributions=True, return_attention=True)

print("\n" + "="*60)
print("  场景1: 低风险区县")
print("="*60)
print(f"风险等级: {result['risk_level_5']} - {result['risk_description']}")
print(f"风险分数: {result['risk_score']:.2f}")
print("\n主要保护因素:")
for contrib in result['feature_contributions']['top_negative'][:3]:
    print(f"  • {contrib['feature']}: {contrib['contribution']:.4f}")
print("="*60)
EOF
```

### 场景2: 高风险区县

```bash
python3 << 'EOF'
from models.enhanced_predictor import EnhancedPredictor

predictor = EnhancedPredictor('saved_models/final_model_3to5.pkl')

# 高风险区县特征
features = {
    '存活数': 3000,
    '感染率': 0.8,
    '治疗覆盖率': 65.0,
    '新报告': 200,
    '人口数': 600000,
    '筛查人数': 20000,
    '干预人数': 3000
}

result = predictor.predict_single(features, include_contributions=True, return_attention=True)

print("\n" + "="*60)
print("  场景2: 高风险区县")
print("="*60)
print(f"风险等级: {result['risk_level_5']} - {result['risk_description']}")
print(f"风险分数: {result['risk_score']:.2f}")
print("\n主要风险因素:")
for contrib in result['feature_contributions']['top_positive'][:3]:
    print(f"  • {contrib['feature']}: {contrib['contribution']:.4f}")
print("\n模型关注重点:")
for item in result['attention_weights']['top_10_features'][:5]:
    print(f"  • {item['feature']}: 权重 {item['weight']:.4f}")
print("="*60)
EOF
```

### 场景3: 政策效果对比

```bash
python3 << 'EOF'
from models.predictor import HIVRiskPredictor

predictor = HIVRiskPredictor('saved_models/final_model_3to5.pkl')

# 政策实施前
before = {
    '存活数': 1500,
    '感染率': 0.5,
    '治疗覆盖率': 70.0,
    '新报告': 100
}

# 政策实施后（提高治疗覆盖率）
after = {
    '存活数': 1500,
    '感染率': 0.5,
    '治疗覆盖率': 90.0,
    '新报告': 100
}

result_before = predictor.predict_single(before)
result_after = predictor.predict_single(after)

print("\n" + "="*60)
print("  场景3: 政策效果评估")
print("="*60)
print(f"\n政策前:")
print(f"  风险等级: {result_before['risk_level_5']}")
print(f"  风险分数: {result_before['risk_score']:.2f}")
print(f"\n政策后:")
print(f"  风险等级: {result_after['risk_level_5']}")
print(f"  风险分数: {result_after['risk_score']:.2f}")
print(f"\n变化:")
print(f"  风险等级变化: {result_after['risk_level_5'] - result_before['risk_level_5']}")
print(f"  风险分数变化: {result_after['risk_score'] - result_before['risk_score']:.2f}")
print("="*60)
EOF
```

---

## 🔍 性能测试

### 测试响应时间

```bash
# 测试单次预测响应时间
python3 << 'EOF'
import time
from models.predictor import HIVRiskPredictor

predictor = HIVRiskPredictor('saved_models/final_model_3to5.pkl')
features = {'存活数': 1000, '感染率': 0.5, '治疗覆盖率': 85.0}

# 预热
for _ in range(10):
    predictor.predict_single(features)

# 测试
times = []
for _ in range(100):
    start = time.time()
    predictor.predict_single(features)
    times.append((time.time() - start) * 1000)

print(f"\n响应时间统计（100次）:")
print(f"  平均: {sum(times)/len(times):.2f} ms")
print(f"  最小: {min(times):.2f} ms")
print(f"  最大: {max(times):.2f} ms")
EOF
```

### 测试批量预测性能

```bash
# 测试批量预测性能
python3 << 'EOF'
import time
from models.predictor import HIVRiskPredictor

predictor = HIVRiskPredictor('saved_models/final_model_3to5.pkl')

# 准备100个样本
samples = [{'存活数': 1000 + i*10, '感染率': 0.5, '治疗覆盖率': 85.0} 
           for i in range(100)]

start = time.time()
results = predictor.predict_batch(samples)
elapsed = (time.time() - start) * 1000

print(f"\n批量预测性能（100个样本）:")
print(f"  总时间: {elapsed:.2f} ms")
print(f"  平均每样本: {elapsed/100:.2f} ms")
print(f"  吞吐量: {100/(elapsed/1000):.2f} 样本/秒")
EOF
```

---

## 📝 演示笔记

### 关键演示点

1. **基础功能**:
   - 5级风险评估
   - 快速响应（<50ms）
   - 高准确率（F1 0.89+）

2. **增强功能**:
   - 特征贡献度分析
   - 注意力权重输出
   - 医学可解释性

3. **技术创新**:
   - DG-DAA架构
   - 领域知识融合
   - 疫情阶段感知

4. **实用性**:
   - 批量预测
   - 政策效果评估
   - 实时监控

### 演示技巧

1. **先展示基础功能**，让观众理解系统能做什么
2. **再展示增强功能**，突出技术创新
3. **最后展示实际场景**，说明应用价值
4. **对比演示**，展示性能提升

### 常见问题准备

Q: 为什么需要110个特征？
A: 这些特征涵盖了人口学、疫情、防控、高危人群等多个维度，确保预测的全面性和准确性。

Q: 模型如何保证可解释性？
A: 通过特征贡献度和注意力权重，可以清楚地看到哪些因素影响了预测结果。

Q: 响应时间为什么这么快？
A: 使用了快速近似算法，在保证准确性的同时优化了计算效率。

Q: 如何处理缺失数据？
A: 系统会自动使用合理的默认值填充，但建议提供完整数据以获得最佳预测效果。

---

## �️ 重要：代码更新后需要重启

如果你更新了代码（如修复了特征贡献度功能），需要重启API服务：

```bash
# 1. 停止当前运行的API（在API终端按 Ctrl+C）

# 2. 重新启动API
python3 api/app.py
```

---

## 🛠️ 故障排查

### 问题1: 模块导入错误

```bash
# 如果出现 "No module named 'xxx'" 错误
pip install -r requirements.txt

# 检查环境
conda activate hivenv
python3 -c "import flask, numpy, pandas, sklearn, shap; print('All modules OK')"
```

### 问题2: 模型文件找不到

```bash
# 检查模型文件
ls -lh saved_models/final_model_3to5.pkl

# 如果文件不存在，检查当前目录
pwd
# 应该在 .../hiv_project/hiv_risk_model
```

### 问题3: API端口被占用

```bash
# 检查端口占用
lsof -i :5000

# 杀死占用进程
kill -9 <PID>

# 或使用其他端口
PORT=5001 python3 api/app.py
```

---

## 📞 演示支持

如果演示过程中遇到问题：

1. 检查Python环境是否正确激活
2. 检查依赖是否完整安装
3. 检查模型文件是否存在
4. 查看错误日志获取详细信息

---

**演示指南版本**: 1.0.0  
**项目版本**: v1.1.0  
**最后更新**: 2025-11-04
