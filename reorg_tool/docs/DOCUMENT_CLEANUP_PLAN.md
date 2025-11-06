# 文档整理方案

## 📊 当前状态

**根目录MD文档数量**: 32个  
**问题**: 文档过多、重复、位置混乱

---

## 📁 文档分类和整理方案

### 1. 用户文档 → `docs/user/`

**保留并移动**:
- `README.md` → 保留在根目录（主入口）
- `USER_MANUAL.md` → `docs/user/`
- `API_DOCUMENTATION.md` → `docs/user/`
- `API_USAGE_EXAMPLES.md` → `docs/user/`

**重复文档（合并后删除）**:
- `QUICKSTART.md` + `QUICK_START.md` + `QUICK_START_ENHANCED.md` → 合并到 `docs/user/QUICK_START.md`
- `README_ENHANCEMENTS.md` → 合并到 `README.md`

---

### 2. 部署文档 → `docs/deployment/`

**保留并移动**:
- `DEPLOYMENT_GUIDE.md` → `docs/deployment/`
- `LOCAL_DEMO_GUIDE.md` → `docs/deployment/`
- `本地测试启动指南.md` → 合并到 `LOCAL_DEMO_GUIDE.md` 后删除

**重复文档（合并后删除）**:
- `DEPLOYMENT.md` + `DEPLOYMENT_CHECKLIST.md` → 合并到 `DEPLOYMENT_GUIDE.md`
- `DELIVERY_CHECKLIST.md` + `WHAT_TO_SUBMIT.md` + `SUBMISSION_GUIDE.md` → 合并到 `docs/deployment/DELIVERY_GUIDE.md`

---

### 3. 项目文档 → `docs/project/`

**保留并移动**:
- `PROJECT_DELIVERY_SUMMARY.md` → `docs/project/`
- `CORE_DELIVERY_FILES.md` → `docs/project/`

**重复文档（合并后删除）**:
- `PROJECT_STATUS.md` + `PROJECT_SUMMARY.md` → 合并到 `docs/project/PROJECT_STATUS.md`

---

### 4. 临时/开发文档 → `dev/temp/` 或删除

**临时文档（移到dev/temp/）**:
- `FILES_CREATED.md`
- `FIX_SUMMARY.md`
- `FONT_FIX_SUMMARY.md`
- `TEST_ISSUES_RESOLVED.md`
- `UPDATE_LOG.md`
- `RESTART_AND_TEST.md`
- `PHASE2_TEST_GUIDE.md`
- `ATTENTION_VS_CONTRIBUTION.md`

**中文临时文档（移到dev/temp/）**:
- `README_今晚要做的事.md`
- `明天提交清单.md`
- `汇报PPT大纲.md`
- `部署准备情况说明.md`

---

## 🎯 整理后的目录结构

```
hiv_risk_model/
├── README.md                    # 主入口（保留）
├── docs/
│   ├── user/
│   │   ├── USER_MANUAL.md
│   │   ├── API_DOCUMENTATION.md
│   │   ├── API_USAGE_EXAMPLES.md
│   │   └── QUICK_START.md       # 合并3个快速开始文档
│   ├── deployment/
│   │   ├── DEPLOYMENT_GUIDE.md  # 合并部署相关文档
│   │   ├── LOCAL_DEMO_GUIDE.md  # 合并本地测试文档
│   │   └── DELIVERY_GUIDE.md    # 合并交付相关文档
│   ├── technical/
│   │   ├── AI_INNOVATION.md
│   │   └── IMPLEMENTATION_LOG.md
│   └── project/
│       ├── PROJECT_STATUS.md    # 合并项目状态文档
│       ├── PROJECT_DELIVERY_SUMMARY.md
│       └── CORE_DELIVERY_FILES.md
├── dev/
│   └── temp/
│       ├── FILES_CREATED.md
│       ├── FIX_SUMMARY.md
│       ├── FONT_FIX_SUMMARY.md
│       ├── TEST_ISSUES_RESOLVED.md
│       ├── UPDATE_LOG.md
│       ├── RESTART_AND_TEST.md
│       ├── PHASE2_TEST_GUIDE.md
│       ├── ATTENTION_VS_CONTRIBUTION.md
│       └── [中文临时文档...]
└── reorg_tool/
    ├── README.md
    └── docs/
        ├── PROJECT_PROGRESS.md
        ├── NEXT_SESSION.md
        └── FILE_ORGANIZATION.md
```

---

## 📊 整理效果

### 整理前
- 根目录：32个MD文档
- docs/目录：部分文档
- 重复文档：至少10个

### 整理后
- 根目录：1个MD文档（README.md）
- docs/user/：4个文档
- docs/deployment/：3个文档
- docs/project/：3个文档
- dev/temp/：12个临时文档
- **减少重复**：从32个减少到约23个（删除9个重复）

---

## 🔧 执行步骤

### 步骤1：创建目录结构
```bash
mkdir -p docs/user docs/deployment docs/project dev/temp
```

### 步骤2：移动用户文档
```bash
mv USER_MANUAL.md docs/user/
mv API_DOCUMENTATION.md docs/user/
mv API_USAGE_EXAMPLES.md docs/user/
```

### 步骤3：合并快速开始文档
- 合并 QUICKSTART.md + QUICK_START.md + QUICK_START_ENHANCED.md
- 创建 docs/user/QUICK_START.md
- 删除原文件

### 步骤4：移动和合并部署文档
- 合并 DEPLOYMENT.md + DEPLOYMENT_CHECKLIST.md → docs/deployment/DEPLOYMENT_GUIDE.md
- 合并 本地测试启动指南.md → LOCAL_DEMO_GUIDE.md
- 合并 DELIVERY_CHECKLIST.md + WHAT_TO_SUBMIT.md + SUBMISSION_GUIDE.md → docs/deployment/DELIVERY_GUIDE.md

### 步骤5：移动项目文档
```bash
mv PROJECT_DELIVERY_SUMMARY.md docs/project/
mv CORE_DELIVERY_FILES.md docs/project/
# 合并 PROJECT_STATUS.md + PROJECT_SUMMARY.md
```

### 步骤6：移动临时文档
```bash
mv FILES_CREATED.md dev/temp/
mv FIX_SUMMARY.md dev/temp/
mv FONT_FIX_SUMMARY.md dev/temp/
mv TEST_ISSUES_RESOLVED.md dev/temp/
mv UPDATE_LOG.md dev/temp/
mv RESTART_AND_TEST.md dev/temp/
mv PHASE2_TEST_GUIDE.md dev/temp/
mv ATTENTION_VS_CONTRIBUTION.md dev/temp/
mv README_今晚要做的事.md dev/temp/
mv 明天提交清单.md dev/temp/
mv 汇报PPT大纲.md dev/temp/
mv 部署准备情况说明.md dev/temp/
mv README_ENHANCEMENTS.md dev/temp/
```

---

## ⚠️ 注意事项

1. **备份**: 执行前先备份整个项目
2. **逐步执行**: 不要一次性执行所有操作
3. **验证链接**: 检查文档中的相互引用
4. **更新README**: 更新主README中的文档链接

---

## 🎯 建议

**在任务8中执行文档整理**:
1. 先完成符号链接模块的实现
2. 然后使用我们自己的重组工具来整理这些文档
3. 这样可以：
   - 测试重组工具的实际效果
   - 保持符号链接的向后兼容
   - 有完整的回滚机制

**或者现在手动整理**:
- 如果你希望立即整理，我可以现在执行
- 但建议等重组工具完成后使用工具自动整理

---

**你的选择**:
1. 现在手动整理这些文档
2. 在任务8-12完成后，使用重组工具自动整理
3. 先继续任务8，稍后再整理文档
