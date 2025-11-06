# 项目目录结构说明

**项目**: HIV Risk Model  
**更新日期**: 2025-11-06  
**版本**: 1.0

---

## 概述

本文档说明HIV Risk Model项目的目录结构，帮助开发者快速了解项目组织方式和文件位置。

---

## 目录结构

```
hiv_risk_model/
├── core/                    # 核心生产代码
│   ├── api/                # API服务
│   ├── models/             # 核心模型
│   └── data/               # 数据文件
├── docs/                    # 所有文档
│   ├── user/               # 用户文档
│   ├── deployment/         # 部署文档
│   ├── technical/          # 技术文档
│   └── project/            # 项目文档
├── dev/                     # 开发文件
│   ├── tests/              # 测试文件
│   ├── scripts/            # 开发脚本
│   ├── utils/              # 工具函数
│   └── temp/               # 临时文件
├── config/                  # 配置文件
├── data/                    # 数据目录
│   ├── raw/                # 原始数据
│   ├── processed/          # 处理后的数据
│   └── mock/               # 模拟数据
├── saved_models/            # 保存的模型
├── outputs/                 # 输出文件
│   ├── visualizations/     # 可视化图表
│   ├── model_evaluation/   # 模型评估结果
│   └── correlation_analysis/ # 相关性分析
├── notebooks/               # Jupyter笔记本
├── reorg_tool/              # 文件重组工具
│   ├── docs/               # 工具文档
│   └── tests/              # 工具测试
├── models/                  # 模型目录（符号链接）
├── api/                     # API目录（符号链接）
├── utils/                   # 工具目录（符号链接）
├── tests/                   # 测试目录（符号链接）
├── README.md                # 项目主文档（符号链接）
├── requirements.txt         # Python依赖
├── Dockerfile               # Docker配置
├── docker-compose.yml       # Docker Compose配置
└── .reorg_config.yaml       # 重组工具配置
```

---

## 目录详解

### core/ - 核心生产代码

存放项目的核心生产代码，这些是系统运行的关键组件。

#### core/api/ (1个文件)
- `app.py` - Flask API主应用，提供HTTP接口

#### core/models/ (14个文件)
核心模型和算法实现：

- `predictor.py` - 基础HIV风险预测器
- `enhanced_predictor.py` - 增强预测器（DG-DAA架构）
- `evaluator.py` - 模型评估器
- `cross_validation.py` - 交叉验证实现
- `model_evaluation.py` - 模型评估工具
- `final_model_trainer.py` - 最终模型训练器
- `feature_engineer.py` - 特征工程
- `feature_contribution_fast.py` - 快速特征贡献分析
- `domain_priors.py` - 领域先验知识
- `data_augmentation.py` - 数据增强
- `synthetic_data_generator.py` - 合成数据生成器
- `correlation_analyzer.py` - 相关性分析器
- `compare_datasets.py` - 数据集比较工具
- `version_manager.py` - 版本管理

#### core/data/
数据文件（如果有）

---

### docs/ - 所有文档

统一存放项目的所有文档，按类型分类。

#### docs/user/ (4个文件)
面向用户的文档：

- `README.md` - 项目主文档
- `API_DOCUMENTATION.md` - API接口文档
- `API_USAGE_EXAMPLES.md` - API使用示例
- `USER_MANUAL.md` - 用户手册

#### docs/deployment/ (7个文件)
部署相关文档：

- `DEPLOYMENT_GUIDE.md` - 部署指南
- `DEPLOYMENT.md` - 部署说明
- `DEPLOYMENT_CHECKLIST.md` - 部署检查清单
- `DELIVERY_CHECKLIST.md` - 交付检查清单
- `LOCAL_DEMO_GUIDE.md` - 本地演示指南
- `SUBMISSION_GUIDE.md` - 提交指南
- `WHAT_TO_SUBMIT.md` - 提交内容说明

#### docs/technical/ (11个文件)
技术文档：

- `IMPLEMENTATION_LOG.md` - 实现日志
- `AI_INNOVATION.md` - AI创新说明
- `API_ENHANCED_GUIDE.md` - API增强指南
- `MODEL_INTERPRETABILITY.md` - 模型可解释性
- `VISUALIZATION_GUIDE.md` - 可视化指南
- `PHASE1_SUMMARY.md` - 第一阶段总结
- `CORE_DELIVERY_FILES.md` - 核心交付文件
- `PROJECT_PROGRESS.md` - 项目进度
- `PROJECT_STATUS.md` - 项目状态
- `PROJECT_SUMMARY.md` - 项目总结
- `PROJECT_DELIVERY_SUMMARY.md` - 项目交付总结

#### docs/project/ (5个文件)
项目管理文档（符号链接到technical/）

---

### dev/ - 开发文件

存放开发过程中使用的文件，不包含在生产部署中。

#### dev/tests/ (20个文件)
测试文件：

- `test_api.py` - API测试
- `test_api_enhanced.py` - 增强API测试
- `test_api_simple.py` - 简单API测试
- `test_attention.py` - 注意力机制测试
- `test_contributions.py` - 特征贡献测试
- `test_chinese_font.py` - 中文字体测试
- `test_augmented_training.py` - 数据增强训练测试
- 以及reorg_tool的测试文件

#### dev/scripts/ (18个文件)
开发和测试脚本：

- `evaluate_enhanced_model.py` - 评估增强模型
- `evaluate_with_cv.py` - 交叉验证评估
- `visualize_contributions.py` - 可视化特征贡献
- `visualize_attention_weights.py` - 可视化注意力权重
- `visualize_correlations.py` - 可视化相关性
- `generate_correlation_report.py` - 生成相关性报告
- `verify_data.py` - 验证数据
- `check_model_params.py` - 检查模型参数
- 等等

#### dev/utils/ (5个文件)
开发工具函数：

- `data_generator.py` - 数据生成器
- `merge_medical_data.py` - 医疗数据合并
- `process_real_data.py` - 真实数据处理
- `read_excel.py` - Excel读取工具
- `update_medical_data.py` - 医疗数据更新

#### dev/temp/ (2个文件)
临时文件和修复脚本

---

### config/ - 配置文件

存放项目配置文件。

---

### data/ - 数据目录

存放项目数据文件。

#### data/raw/
原始数据文件

#### data/processed/
处理后的数据文件

#### data/mock/
模拟数据文件

---

### saved_models/ - 保存的模型

存放训练好的模型文件。

---

### outputs/ - 输出文件

存放程序生成的输出文件。

#### outputs/visualizations/
可视化图表

#### outputs/model_evaluation/
模型评估结果

#### outputs/correlation_analysis/
相关性分析结果

---

### notebooks/ - Jupyter笔记本

存放Jupyter笔记本文件，用于数据探索和实验。

---

### reorg_tool/ - 文件重组工具

文件重组系统的源代码和文档。

#### reorg_tool/docs/
工具文档：
- `USER_GUIDE.md` - 使用指南
- `VALIDATION_REPORT.md` - 验证报告
- `INTEGRATION_TEST_REPORT.md` - 集成测试报告
- `PROJECT_PROGRESS.md` - 项目进度

#### reorg_tool/tests/
工具测试文件（279个单元测试）

---

### 符号链接目录

为保持向后兼容性，以下目录通过符号链接指向新位置：

#### models/ → core/models/
模型文件的符号链接

#### api/ → core/api/
API文件的符号链接

#### utils/ → dev/utils/
工具函数的符号链接

#### tests/ → dev/tests/
测试文件的符号链接

---

## 文件查找指南

### 如何找到特定类型的文件

#### 核心代码
- **位置**: `core/`
- **示例**: 预测器、评估器、API

#### 文档
- **位置**: `docs/`
- **用户文档**: `docs/user/`
- **部署文档**: `docs/deployment/`
- **技术文档**: `docs/technical/`

#### 测试
- **位置**: `dev/tests/`
- **示例**: API测试、模型测试

#### 脚本
- **位置**: `dev/scripts/`
- **示例**: 评估脚本、可视化脚本

#### 数据
- **位置**: `data/`
- **原始数据**: `data/raw/`
- **处理数据**: `data/processed/`

#### 模型
- **位置**: `saved_models/`
- **示例**: 训练好的模型文件

---

## 添加新文件指南

### 添加核心代码

```bash
# 新的模型文件
touch core/models/new_model.py

# 新的API端点
touch core/api/new_endpoint.py
```

### 添加文档

```bash
# 用户文档
touch docs/user/new_guide.md

# 技术文档
touch docs/technical/new_design.md
```

### 添加测试

```bash
# 新的测试文件
touch dev/tests/test_new_feature.py
```

### 添加脚本

```bash
# 新的开发脚本
touch dev/scripts/new_script.py
```

---

## 向后兼容性

### 旧路径仍然可用

由于符号链接的存在，旧的导入路径仍然有效：

```python
# 旧路径（仍然可用）
from models.predictor import HIVRiskPredictor
from api.app import app
import utils.data_generator

# 新路径（推荐）
from core.models.predictor import HIVRiskPredictor
from core.api.app import app
import dev.utils.data_generator
```

### 逐步迁移建议

1. **短期**: 继续使用旧路径（通过符号链接）
2. **中期**: 逐步更新代码使用新路径
3. **长期**: 移除符号链接，完全使用新路径

---

## 目录结构优势

### 1. 清晰的分类

- **core/**: 生产代码
- **docs/**: 文档
- **dev/**: 开发文件

### 2. 易于导航

- 文件按功能分类
- 目录名称直观
- 结构层次清晰

### 3. 便于维护

- 核心代码集中
- 文档统一管理
- 开发文件隔离

### 4. 支持扩展

- 易于添加新模块
- 易于添加新文档
- 易于添加新测试

### 5. 向后兼容

- 符号链接保持兼容
- 旧代码无需修改
- 平滑过渡

---

## 常见问题

### Q: 为什么有两个models目录？

A: `models/`是符号链接，指向`core/models/`。这样旧代码可以继续使用`from models.xxx import`，而新代码可以使用`from core.models.xxx import`。

### Q: 如何知道一个文件是符号链接？

A: 使用`ls -la`命令：
```bash
ls -la models/
# lrwxrwxrwx ... models/predictor.py -> ../core/models/predictor.py
```

### Q: 可以删除符号链接吗？

A: 可以，但需要先更新所有使用旧路径的代码。建议逐步迁移后再删除。

### Q: 新文件应该放在哪里？

A: 
- 核心代码 → `core/`
- 文档 → `docs/`
- 测试 → `dev/tests/`
- 脚本 → `dev/scripts/`

---

## 相关文档

- **项目主文档**: `docs/user/README.md`
- **重组总结**: `REORGANIZATION_SUMMARY.md`
- **重组工具指南**: `reorg_tool/docs/USER_GUIDE.md`

---

**文档版本**: 1.0  
**最后更新**: 2025-11-06  
**维护者**: HIV Risk Model Team
