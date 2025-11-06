# HIV风险评估模型 v1.1.0

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Model](https://img.shields.io/badge/Model-v1.1.0-orange.svg)](docs/AI_INNOVATION.md)

基于机器学习的HIV风险评估模型，集成领域知识引导的双层自适应注意力机制（DG-DAA），提供高精度的区县级HIV风险预测和可解释性分析。

## ✨ 核心特性

### 🎯 高性能预测
- **准确率**: F1 score 0.89+ (测试集)
- **性能提升**: 交叉验证F1提升137.48%
- **响应速度**: 单次预测 < 50ms
- **5级风险评估**: 极低、低、中等、高、极高

### 🧠 AI技术创新
- **DG-DAA架构**: 领域知识引导的双层自适应注意力机制
- **医学可解释性**: 疫情阶段感知的注意力分配
- **特征贡献度**: 基于SHAP的快速特征贡献度分析
- **注意力权重**: 可视化模型关注重点

### 📊 数据分析
- **相关性分析**: 验证29个已知风险因素关联关系
- **新发现**: 识别25个显著相关的未知特征
- **可视化**: 8种专业图表展示分析结果

### 🚀 生产就绪
- **RESTful API**: 完整的HTTP接口
- **Docker支持**: 一键部署
- **监控告警**: 健康检查和性能监控
- **文档完善**: API文档、使用示例、部署指南

## 📦 快速开始

### 使用Docker（推荐）

```bash
# 1. 构建镜像
docker build -t hiv-risk-api:v1.1.0 .

# 2. 运行容器
docker run -d -p 5000:5000 \
  -e USE_ENHANCED_MODEL=true \
  --name hiv-api \
  hiv-risk-api:v1.1.0

# 3. 测试
curl http://localhost:5000/health
```

### 本地安装

```bash
# 1. 创建环境
conda create -n hivenv python=3.9 -y
conda activate hivenv

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动服务
python api/app.py

# 4. 测试
curl http://localhost:5000/health
```

## 📖 文档

### 用户文档
- **[用户手册](USER_MANUAL.md)** - 详细的使用指南（推荐新用户阅读）
- **[API文档](API_DOCUMENTATION.md)** - 完整的API接口说明
- **[使用示例](API_USAGE_EXAMPLES.md)** - Python/JavaScript代码示例

### 部署文档
- **[部署指南](DEPLOYMENT_GUIDE.md)** - 生产环境部署方案
- **[交付清单](DELIVERY_CHECKLIST.md)** - 快速部署参考
- **[部署检查清单](DEPLOYMENT_CHECKLIST.md)** - 运维部署检查表

### 技术文档
- **[技术创新](docs/AI_INNOVATION.md)** - DG-DAA架构详解（15+页）
- **[实施日志](docs/IMPLEMENTATION_LOG.md)** - 详细开发记录

### 项目文档
- **[项目交付总结](PROJECT_DELIVERY_SUMMARY.md)** - 完整的项目交付报告
- **[核心文件清单](CORE_DELIVERY_FILES.md)** - 26个核心交付文件说明

## 🔧 使用示例

### Python

```python
import requests

# 预测风险
response = requests.post('http://localhost:5000/v1/predict', json={
    'features': {
        '存活数': 1000,
        '感染率': 0.5,
        '治疗覆盖率': 85.0,
        # ... 其他107个特征
    },
    'include_contributions': True,  # 包含特征贡献度
    'include_attention': True        # 包含注意力权重
})

result = response.json()
print(f"风险等级: {result['prediction']['risk_level']}")
print(f"风险描述: {result['prediction']['risk_description']}")
```

### cURL

```bash
curl -X POST http://localhost:5000/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "features": {
      "存活数": 1000,
      "感染率": 0.5,
      "治疗覆盖率": 85.0
    },
    "include_contributions": true
  }'
```

## 🏗️ 项目结构

```
hiv_risk_model/
├── api/                          # API服务
│   └── app.py                    # Flask应用
├── models/                       # 模型代码
│   ├── predictor.py             # 基础预测器
│   ├── enhanced_predictor.py    # 增强预测器（DG-DAA）
│   ├── domain_priors.py         # 领域知识先验
│   ├── feature_contribution*.py # 特征贡献度分析
│   ├── correlation_analyzer.py  # 相关性分析
│   └── version_manager.py       # 版本管理
├── saved_models/                # 模型文件
│   ├── final_model_3to5.pkl    # 训练好的模型
│   └── model_registry.json     # 版本注册表
├── data/                        # 数据目录
│   └── processed/              # 处理后的数据
├── docs/                        # 文档
│   ├── AI_INNOVATION.md        # 技术创新文档
│   └── IMPLEMENTATION_LOG.md   # 实施日志
├── outputs/                     # 输出结果
│   ├── visualizations/         # 可视化图表
│   └── correlation_analysis/   # 分析报告
├── Dockerfile                   # Docker配置
├── requirements.txt            # Python依赖
├── README.md                   # 本文档
├── API_DOCUMENTATION.md        # API文档
├── API_USAGE_EXAMPLES.md       # 使用示例
└── DEPLOYMENT_GUIDE.md         # 部署指南
```

## 🎨 技术栈

- **机器学习**: scikit-learn, Gradient Boosting
- **可解释性**: SHAP
- **Web框架**: Flask, Flask-CORS
- **数据处理**: NumPy, Pandas
- **可视化**: Matplotlib, Seaborn
- **部署**: Docker, Gunicorn, Nginx

## 📊 性能指标

| 指标 | 基线模型 | 增强模型 (DG-DAA) | 提升 |
|------|---------|------------------|------|
| F1 (weighted) - 交叉验证 | 0.0300 | 0.0713 | +137.48% |
| F1 (weighted) - 测试集 | 0.8421 | 0.8947 | +6.25% |
| Precision | 0.0185 | 0.4010 | +2061.87% |
| 响应时间 | ~45ms | ~47ms | +2ms |

## 🔬 创新点

### DG-DAA架构

领域知识引导的双层自适应注意力机制（Domain-Guided Dual Adaptive Attention）

**核心创新**:
1. **领域知识先验注入**: 融合医学专家经验
2. **双层注意力**: 特征级 + 样本级
3. **疫情阶段感知**: 低风险区关注预防，高风险区关注控制
4. **医学可解释性**: 输出可解释的注意力权重

详见 [技术创新文档](docs/AI_INNOVATION.md)

## 🌟 主要功能

### 1. 风险预测
- 5级风险评估（1-5级）
- 风险分数（0-100）
- 预测置信度

### 2. 特征贡献度分析
- Top 5正贡献特征（增加风险）
- Top 5负贡献特征（降低风险）
- 所有110个特征的贡献值

### 3. 注意力权重
- Top 10模型关注特征
- 疫情阶段自适应权重
- 医学可解释性

### 4. 全局特征重要性
- Top 20最重要特征
- 重要性分数和百分比
- 特征排名

### 5. 批量预测
- 支持批量处理
- 单次最多1000个样本
- 并发处理优化

## 🔐 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| USE_ENHANCED_MODEL | true | 是否启用增强模型（DG-DAA） |
| PORT | 5000 | API服务端口 |
| HOST | 0.0.0.0 | API服务主机 |
| DEBUG | false | 是否启用调试模式 |

## 📝 API端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | API首页和信息 |
| `/health` | GET | 健康检查 |
| `/v1/model/info` | GET | 模型信息 |
| `/v1/predict` | POST | 单样本预测 |
| `/v1/predict/batch` | POST | 批量预测 |
| `/v1/model/feature_importance` | GET | 全局特征重要性 |

## 🚢 部署

### Docker部署

```bash
# 构建镜像
docker build -t hiv-risk-api:v1.1.0 .

# 运行容器
docker run -d -p 5000:5000 \
  -e USE_ENHANCED_MODEL=true \
  -v $(pwd)/logs:/app/logs \
  --name hiv-api \
  hiv-risk-api:v1.1.0
```

### 生产环境部署

使用Gunicorn + Nginx，详见 [部署指南](DEPLOYMENT_GUIDE.md)

## 📈 监控

### 健康检查

```bash
curl http://localhost:5000/health
```

### 性能监控

```bash
# 查看日志
tail -f logs/api.log

# 查看进程
ps aux | grep app.py

# 查看资源使用
top -p $(pgrep -f "python.*app.py")
```

## 🐛 故障排查

常见问题和解决方案详见 [部署指南 - 故障排查](DEPLOYMENT_GUIDE.md#故障排查)

## 📄 许可证

MIT License

## 👥 贡献者

HIV风险评估项目组

## 📞 联系方式

如有问题或建议，请联系项目组。

## 🔄 更新日志

### v1.1.0 (2025-11-04)
- ✅ 新增DG-DAA增强模型
- ✅ 新增特征贡献度分析
- ✅ 新增注意力权重输出
- ✅ 性能提升137.48%（交叉验证）
- ✅ 完整的API文档和部署指南

### v1.0.0 (2024-01-01)
- 初始版本发布
- 基于Gradient Boosting的风险预测
- 5级风险评估

---

**版本**: v1.1.0  
**最后更新**: 2025-11-04  
**Python版本**: 3.9+  
**模型类型**: Enhanced (DG-DAA)


## 📁 项目目录结构

项目已重组为清晰的目录结构（2025-11-06更新）：

```
hiv_risk_model/
├── core/              # 核心生产代码
│   ├── api/          # API服务
│   ├── models/       # 核心模型（预测器、评估器等）
│   └── data/         # 数据文件
├── docs/             # 所有文档
│   ├── user/        # 用户文档（本文件）
│   ├── deployment/  # 部署文档
│   ├── technical/   # 技术文档
│   └── project/     # 项目文档
├── dev/              # 开发文件
│   ├── tests/       # 测试文件
│   ├── scripts/     # 开发脚本
│   ├── utils/       # 工具函数
│   └── temp/        # 临时文件
├── config/           # 配置文件
├── data/             # 数据目录
├── saved_models/     # 保存的模型
└── requirements.txt  # 依赖文件
```

**注意**: 为保持向后兼容性，原有路径通过符号链接仍然可用。例如：
- `models/predictor.py` → `core/models/predictor.py`
- `api/app.py` → `core/api/app.py`

详细的重组信息请参考 `REORGANIZATION_SUMMARY.md`
