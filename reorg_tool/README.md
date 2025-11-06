# 文件重组系统 (File Reorganization System)

一个安全、智能的项目文件重组工具，支持自动分类、依赖分析、符号链接和完整回滚。

## 🎉 项目状态

- **开发进度**: 85% (17/20 任务完成)
- **核心代码**: 100% 完成 ✅
- **测试状态**: 279个单元测试全部通过 ✅
- **系统状态**: 完全可用 🚀
- **重组状态**: ✅ 已成功完成
- **验证状态**: ✅ 全部通过

## ✨ 主要功能

- ✅ **智能文件分类**: 自动识别核心文件、文档、开发文件
- ✅ **依赖分析**: AST解析Python导入，构建依赖图
- ✅ **安全移动**: MD5校验、权限保持、事务日志
- ✅ **符号链接**: 自动创建符号链接保持向后兼容
- ✅ **完整验证**: 验证链接、导入、文件完整性
- ✅ **详细报告**: Markdown格式的重组报告
- ✅ **安全回滚**: 基于事务日志的完整回滚
- ✅ **灵活配置**: YAML配置文件支持
- ✅ **CLI界面**: 用户友好的命令行工具

## 🚀 快速开始

### 1. 初始化配置

```bash
python reorg_tool/reorg.py init
```

这将创建默认配置文件 `.reorg_config.yaml`

### 2. 编辑配置（可选）

```yaml
reorganization:
  project_root: "."
  backup:
    enabled: true
    retention_days: 7
  symbolic_links:
    enabled: true
  dry_run: false
```

### 3. 干运行测试

```bash
python reorg_tool/reorg.py reorganize --dry-run
```

### 4. 执行重组

```bash
python reorg_tool/reorg.py reorganize
```

### 5. 验证结果

```bash
python reorg_tool/reorg.py validate
```

### 6. 如需回滚

```bash
python reorg_tool/reorg.py rollback
```

## 📖 命令参考

### init - 初始化配置

```bash
reorg init [--output PATH]
```

创建默认配置文件。

### reorganize - 执行重组

```bash
reorg reorganize [OPTIONS]

选项:
  --config PATH      配置文件路径
  --dry-run          干运行模式（不实际修改）
  --no-backup        禁用备份
  --project-root PATH 项目根目录
```

### rollback - 回滚重组

```bash
reorg rollback [OPTIONS]

选项:
  --log PATH         事务日志文件路径
  --backup PATH      备份目录路径
  --project-root PATH 项目根目录
```

### validate - 验证结果

```bash
reorg validate [--project-root PATH]
```

验证符号链接、导入和文件完整性。

### report - 生成报告

```bash
reorg report [OPTIONS]

选项:
  --project-root PATH 项目根目录
  --output PATH      报告输出路径
```

## 🏗️ 重组流程

系统执行12个阶段的重组流程：

1. **SCAN** - 扫描项目文件
2. **CLASSIFY** - 智能分类文件
3. **ANALYZE** - 分析依赖关系
4. **BACKUP** - 创建完整备份
5. **CREATE_STRUCTURE** - 创建新目录结构
6. **MOVE_CORE** - 移动核心文件
7. **MOVE_DOCS** - 移动文档文件
8. **MOVE_DEV** - 移动开发文件
9. **CREATE_LINKS** - 创建符号链接
10. **VALIDATE** - 验证结果
11. **CLEANUP** - 清理临时文件
12. **REPORT** - 生成详细报告

## 📁 目标目录结构

```
project/
├── core/              # 核心生产文件
│   ├── api/          # API文件
│   ├── models/       # 模型文件
│   └── data/         # 数据文件
├── config/           # 配置文件
├── docs/             # 文档
│   ├── user/        # 用户文档
│   ├── deployment/  # 部署文档
│   ├── technical/   # 技术文档
│   └── project/     # 项目文档
├── dev/              # 开发文件
│   ├── tests/       # 测试文件
│   ├── scripts/     # 开发脚本
│   ├── utils/       # 工具函数
│   └── temp/        # 临时文件
└── scripts/          # 脚本文件
```

## 🔧 系统架构

### 核心模块

- **Scanner**: 文件扫描和信息收集
- **Classifier**: 智能文件分类
- **Analyzer**: 依赖关系分析
- **Mover**: 安全文件移动
- **Linker**: 符号链接管理
- **Validator**: 结果验证
- **Reporter**: 报告生成
- **Rollback**: 回滚服务
- **Orchestrator**: 流程编排
- **ConfigLoader**: 配置管理
- **CLI**: 命令行界面

### 支持服务

- **BackupService**: 备份管理
- **TransactionLog**: 事务日志

## 📊 测试覆盖

- **总测试数**: 279个
- **通过率**: 100%
- **测试模块**: 14个核心模块
- **测试类型**: 单元测试、集成测试、错误处理

运行测试：

```bash
cd hiv_project/hiv_risk_model
python -m pytest reorg_tool/tests/ -v
```

## 📝 配置文件示例

```yaml
reorganization:
  # 项目根目录
  project_root: "."
  
  # 备份设置
  backup:
    enabled: true
    path: null  # 自动生成
    retention_days: 7
  
  # 符号链接设置
  symbolic_links:
    enabled: true
    use_relative_paths: true
  
  # 运行模式
  dry_run: false
  auto_confirm_deletes: false
  preserve_timestamps: true
  
  # 日志设置
  logging:
    level: "INFO"
    console: true
    file: true
```

## 🛡️ 安全特性

- ✅ **完整备份**: 重组前自动创建完整备份
- ✅ **事务日志**: 记录所有操作，支持完整回滚
- ✅ **MD5校验**: 文件移动时验证完整性
- ✅ **用户确认**: 危险操作需要用户确认
- ✅ **干运行模式**: 可以先测试不实际修改
- ✅ **符号链接**: 保持向后兼容，不破坏现有代码

## 📚 文档

- **项目进度**: `docs/PROJECT_PROGRESS.md`
- **下次会话指南**: `docs/NEXT_SESSION.md`
- **文件组织说明**: `docs/FILE_ORGANIZATION.md`
- **需求文档**: `../../.kiro/specs/project-file-reorganization/requirements.md`
- **设计文档**: `../../.kiro/specs/project-file-reorganization/design.md`
- **任务列表**: `../../.kiro/specs/project-file-reorganization/tasks.md`

## 🐛 故障排除

### 问题：符号链接创建失败

**Windows用户**: 需要管理员权限创建符号链接。

**解决方案**: 以管理员身份运行命令提示符。

### 问题：导入失败

**原因**: 符号链接可能未正确创建。

**解决方案**: 运行 `reorg validate` 检查链接状态。

### 问题：需要回滚

**解决方案**: 
```bash
reorg rollback
```

或手动从备份恢复：
```bash
cp -r /path/to/backup/* /path/to/project/
```

## 🤝 贡献

项目使用Spec驱动开发方法：

1. 需求定义 (requirements.md)
2. 设计文档 (design.md)
3. 任务分解 (tasks.md)
4. 实现和测试
5. 验证和交付

## 📄 许可证

[待定]

## 🎓 下一步

### 已完成任务 (1-17) ✅

- ✅ **任务1-14**: 核心开发完成
- ✅ **任务15**: 执行实际项目重组
- ✅ **任务16**: 验证重组结果
- ✅ **任务17**: 生成报告和文档

### 剩余任务 (18-20)

- **任务18**: 集成测试和回滚测试
- **任务19**: 用户文档和使用指南
- **任务20**: 最终清理和交付

### 重组成果

- ✅ 新目录结构已创建（core/docs/dev）
- ✅ 92个符号链接保持向后兼容
- ✅ 279个单元测试全部通过
- ✅ 完整备份和回滚机制
- ✅ 详细的验证和重组报告

### 相关文档

- **重组总结**: `../REORGANIZATION_SUMMARY.md`
- **验证报告**: `docs/VALIDATION_REPORT.md`
- **重组结果**: `docs/REORGANIZATION_RESULTS.md`
- **项目进度**: `docs/PROJECT_PROGRESS.md`

---

**项目状态**: 重组成功完成，系统完全可用！🚀

**最后更新**: 2025-11-06
