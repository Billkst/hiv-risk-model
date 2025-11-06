# 文件重组工具使用指南

**版本**: 1.0.0  
**更新日期**: 2025-11-06

---

## 目录

1. [简介](#简介)
2. [快速开始](#快速开始)
3. [详细使用](#详细使用)
4. [配置说明](#配置说明)
5. [常见场景](#常见场景)
6. [故障排除](#故障排除)
7. [最佳实践](#最佳实践)

---

## 简介

文件重组工具是一个安全、智能的项目文件重组系统，可以帮助你：

- 🗂️ 自动整理混乱的项目文件
- 📁 创建清晰的目录结构
- 🔗 使用符号链接保持向后兼容
- 💾 提供完整的备份和回滚机制
- ✅ 验证重组结果的正确性

### 核心特性

- **智能分类**: 自动识别核心文件、文档、开发文件
- **依赖分析**: 分析Python导入和文件路径依赖
- **安全移动**: MD5校验、权限保持、事务日志
- **符号链接**: 自动创建链接保持兼容性
- **完整验证**: 验证链接、导入、文件完整性
- **详细报告**: 生成Markdown格式的重组报告
- **安全回滚**: 基于事务日志的完整回滚

---

## 快速开始

### 1. 安装依赖

```bash
# 安装PyYAML
conda install -y pyyaml
# 或
pip install pyyaml
```

### 2. 初始化配置

```bash
cd your_project
python path/to/reorg_tool/reorg.py init
```

这将创建默认配置文件 `.reorg_config.yaml`

### 3. 干运行测试

在实际重组前，先运行干运行模式查看计划：

```bash
python path/to/reorg_tool/reorg.py reorganize --dry-run
```

### 4. 执行重组

确认计划无误后，执行实际重组：

```bash
python path/to/reorg_tool/reorg.py reorganize
```

### 5. 验证结果

```bash
python path/to/reorg_tool/reorg.py validate
```

---

## 详细使用

### 命令概览

```bash
reorg <command> [options]
```

可用命令：
- `init` - 创建默认配置文件
- `reorganize` - 执行文件重组
- `rollback` - 回滚重组
- `validate` - 验证重组结果
- `report` - 生成重组报告

### init - 初始化配置

创建默认配置文件。

**语法**:
```bash
reorg init [--output PATH]
```

**选项**:
- `--output PATH`: 配置文件输出路径（默认: `.reorg_config.yaml`）

**示例**:
```bash
# 创建默认配置
reorg init

# 指定输出路径
reorg init --output my_config.yaml
```

### reorganize - 执行重组

执行文件重组操作。

**语法**:
```bash
reorg reorganize [OPTIONS]
```

**选项**:
- `--config PATH`: 配置文件路径
- `--dry-run`: 干运行模式（不实际修改）
- `--no-backup`: 禁用备份
- `--project-root PATH`: 项目根目录

**示例**:
```bash
# 使用默认配置
reorg reorganize

# 干运行模式
reorg reorganize --dry-run

# 使用自定义配置
reorg reorganize --config my_config.yaml

# 指定项目根目录
reorg reorganize --project-root /path/to/project

# 禁用备份（不推荐）
reorg reorganize --no-backup
```

### rollback - 回滚重组

回滚之前的重组操作。

**语法**:
```bash
reorg rollback [OPTIONS]
```

**选项**:
- `--log PATH`: 事务日志文件路径
- `--backup PATH`: 备份目录路径
- `--project-root PATH`: 项目根目录

**示例**:
```bash
# 使用默认日志和备份
reorg rollback

# 指定日志文件
reorg rollback --log .reorg_transaction_log.json

# 指定备份目录
reorg rollback --backup /path/to/backup

# 指定项目根目录
reorg rollback --project-root /path/to/project
```

### validate - 验证结果

验证重组结果的正确性。

**语法**:
```bash
reorg validate [--project-root PATH]
```

**选项**:
- `--project-root PATH`: 项目根目录

**示例**:
```bash
# 验证当前目录
reorg validate

# 验证指定目录
reorg validate --project-root /path/to/project
```

### report - 生成报告

生成重组报告。

**语法**:
```bash
reorg report [OPTIONS]
```

**选项**:
- `--project-root PATH`: 项目根目录
- `--output PATH`: 报告输出路径

**示例**:
```bash
# 生成默认报告
reorg report

# 指定输出路径
reorg report --output my_report.md

# 指定项目根目录
reorg report --project-root /path/to/project
```

---

## 配置说明

### 配置文件格式

配置文件使用YAML格式：

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

### 配置项说明

#### project_root
- **类型**: 字符串
- **默认值**: "."
- **说明**: 项目根目录路径

#### backup.enabled
- **类型**: 布尔值
- **默认值**: true
- **说明**: 是否启用备份

#### backup.path
- **类型**: 字符串或null
- **默认值**: null
- **说明**: 备份目录路径，null表示自动生成

#### backup.retention_days
- **类型**: 整数
- **默认值**: 7
- **说明**: 备份保留天数

#### symbolic_links.enabled
- **类型**: 布尔值
- **默认值**: true
- **说明**: 是否创建符号链接

#### symbolic_links.use_relative_paths
- **类型**: 布尔值
- **默认值**: true
- **说明**: 是否使用相对路径（推荐）

#### dry_run
- **类型**: 布尔值
- **默认值**: false
- **说明**: 是否为干运行模式

#### auto_confirm_deletes
- **类型**: 布尔值
- **默认值**: false
- **说明**: 是否自动确认删除操作

#### preserve_timestamps
- **类型**: 布尔值
- **默认值**: true
- **说明**: 是否保持文件时间戳

#### logging.level
- **类型**: 字符串
- **可选值**: "DEBUG", "INFO", "WARNING", "ERROR"
- **默认值**: "INFO"
- **说明**: 日志级别

---

## 常见场景

### 场景1: 首次重组项目

```bash
# 1. 进入项目目录
cd your_project

# 2. 初始化配置
python /path/to/reorg_tool/reorg.py init

# 3. 编辑配置文件（可选）
vim .reorg_config.yaml

# 4. 干运行测试
python /path/to/reorg_tool/reorg.py reorganize --dry-run

# 5. 查看计划，确认无误

# 6. 执行重组
python /path/to/reorg_tool/reorg.py reorganize

# 7. 验证结果
python /path/to/reorg_tool/reorg.py validate
```

### 场景2: 重组出现问题需要回滚

```bash
# 1. 执行回滚
python /path/to/reorg_tool/reorg.py rollback

# 2. 验证回滚结果
python /path/to/reorg_tool/reorg.py validate

# 3. 检查项目是否恢复正常
```

### 场景3: 自定义重组配置

```bash
# 1. 创建自定义配置
python /path/to/reorg_tool/reorg.py init --output custom_config.yaml

# 2. 编辑配置文件
vim custom_config.yaml

# 修改示例：
# - 禁用符号链接
# - 更改备份路径
# - 调整日志级别

# 3. 使用自定义配置执行重组
python /path/to/reorg_tool/reorg.py reorganize --config custom_config.yaml
```

### 场景4: 仅生成报告不执行重组

```bash
# 1. 干运行模式
python /path/to/reorg_tool/reorg.py reorganize --dry-run

# 2. 生成报告
python /path/to/reorg_tool/reorg.py report --output analysis_report.md

# 3. 查看报告
cat analysis_report.md
```

---

## 故障排除

### 问题1: 符号链接创建失败

**症状**: 
```
Error: Failed to create symbolic link
```

**原因**: 
- Windows系统需要管理员权限
- 文件系统不支持符号链接

**解决方案**:
```bash
# Windows: 以管理员身份运行
# 或在配置中禁用符号链接
symbolic_links:
  enabled: false
```

### 问题2: 导入失败

**症状**:
```
ImportError: cannot import name 'xxx'
```

**原因**:
- 符号链接未正确创建
- Python路径配置问题

**解决方案**:
```bash
# 1. 验证符号链接
python /path/to/reorg_tool/reorg.py validate

# 2. 检查符号链接
ls -la models/

# 3. 如果链接损坏，执行回滚
python /path/to/reorg_tool/reorg.py rollback
```

### 问题3: 权限不足

**症状**:
```
PermissionError: [Errno 13] Permission denied
```

**原因**:
- 文件或目录权限不足

**解决方案**:
```bash
# 检查文件权限
ls -la

# 修改权限（如需要）
chmod -R u+w .

# 或使用sudo（不推荐）
sudo python /path/to/reorg_tool/reorg.py reorganize
```

### 问题4: 磁盘空间不足

**症状**:
```
OSError: [Errno 28] No space left on device
```

**原因**:
- 备份需要额外空间

**解决方案**:
```bash
# 1. 检查磁盘空间
df -h

# 2. 清理不需要的文件

# 3. 或禁用备份（不推荐）
python /path/to/reorg_tool/reorg.py reorganize --no-backup
```

### 问题5: 配置文件错误

**症状**:
```
yaml.scanner.ScannerError: ...
```

**原因**:
- YAML格式错误

**解决方案**:
```bash
# 1. 检查YAML语法
python -c "import yaml; yaml.safe_load(open('.reorg_config.yaml'))"

# 2. 或重新生成配置
python /path/to/reorg_tool/reorg.py init --output .reorg_config.yaml
```

---

## 最佳实践

### 1. 重组前的准备

✅ **DO**:
- 提交所有未提交的代码到版本控制
- 确保有足够的磁盘空间
- 先在测试环境中尝试
- 使用干运行模式预览计划
- 通知团队成员

❌ **DON'T**:
- 在生产环境直接重组
- 禁用备份功能
- 跳过干运行测试
- 在有未保存工作时重组

### 2. 配置建议

✅ **推荐配置**:
```yaml
backup:
  enabled: true  # 始终启用备份
  retention_days: 7  # 保留足够长的时间

symbolic_links:
  enabled: true  # 保持向后兼容
  use_relative_paths: true  # 使用相对路径

auto_confirm_deletes: false  # 手动确认删除
preserve_timestamps: true  # 保持时间戳
```

### 3. 执行流程

推荐的执行流程：

1. **准备阶段**
   - 备份代码到版本控制
   - 初始化配置
   - 编辑配置（如需要）

2. **测试阶段**
   - 干运行模式
   - 查看计划
   - 确认无误

3. **执行阶段**
   - 执行重组
   - 观察输出
   - 记录任何警告

4. **验证阶段**
   - 运行验证命令
   - 检查符号链接
   - 测试导入
   - 运行测试套件

5. **确认阶段**
   - 确认功能正常
   - 通知团队
   - 更新文档

### 4. 回滚策略

何时需要回滚：
- 验证失败
- 导入错误
- 功能异常
- 团队反馈问题

回滚步骤：
```bash
# 1. 立即执行回滚
python /path/to/reorg_tool/reorg.py rollback

# 2. 验证回滚结果
python /path/to/reorg_tool/reorg.py validate

# 3. 测试功能
# 运行测试套件

# 4. 分析问题
# 查看日志和报告

# 5. 修复问题后重试
```

### 5. 维护建议

定期维护：
- 清理旧备份（超过保留期）
- 检查符号链接状态
- 更新文档中的路径引用
- 监控磁盘空间使用

长期规划：
- 逐步更新代码使用新路径
- 考虑移除符号链接
- 持续优化目录结构

---

## 附录

### A. 目录结构模板

重组后的标准目录结构：

```
project/
├── core/              # 核心生产代码
│   ├── api/          # API服务
│   ├── models/       # 核心模型
│   └── data/         # 数据文件
├── docs/             # 所有文档
│   ├── user/        # 用户文档
│   ├── deployment/  # 部署文档
│   ├── technical/   # 技术文档
│   └── project/     # 项目文档
├── dev/              # 开发文件
│   ├── tests/       # 测试文件
│   ├── scripts/     # 开发脚本
│   ├── utils/       # 工具函数
│   └── temp/        # 临时文件
├── config/           # 配置文件
└── scripts/          # 生产脚本
```

### B. 常用命令速查

```bash
# 初始化
reorg init

# 干运行
reorg reorganize --dry-run

# 执行重组
reorg reorganize

# 验证
reorg validate

# 回滚
reorg rollback

# 生成报告
reorg report

# 查看帮助
reorg --help
reorg <command> --help
```

### C. 相关文档

- **README**: `../README.md`
- **验证报告**: `VALIDATION_REPORT.md`
- **集成测试报告**: `INTEGRATION_TEST_REPORT.md`
- **项目进度**: `PROJECT_PROGRESS.md`

---

**文档版本**: 1.0.0  
**最后更新**: 2025-11-06  
**维护者**: Kiro AI Assistant
