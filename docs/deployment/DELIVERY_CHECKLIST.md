# HIV风险评估模型 - 交付清单

## 📦 交付物清单

### 1. 核心文件

#### 模型文件
- ✅ `saved_models/final_model_3to5.pkl` (1.1 MB) - 训练好的模型权重
- ✅ `saved_models/model_registry.json` - 模型版本注册表

#### 代码文件
- ✅ `api/app.py` - API服务主程序
- ✅ `models/predictor.py` - 基础预测器
- ✅ `models/enhanced_predictor.py` - 增强预测器（DG-DAA）
- ✅ `models/domain_priors.py` - 领域知识先验
- ✅ `models/feature_contribution_fast.py` - 特征贡献度分析
- ✅ `models/correlation_analyzer.py` - 相关性分析器
- ✅ `models/version_manager.py` - 版本管理器

#### 配置文件
- ✅ `requirements.txt` - Python依赖列表
- ✅ `Dockerfile` - Docker镜像配置
- ✅ `docker-compose.yml` - Docker Compose配置
- ✅ `.dockerignore` - Docker忽略文件

### 2. 文档文件

#### 核心文档
- ✅ `README.md` - 项目说明文档
- ✅ `API_DOCUMENTATION.md` - API接口文档
- ✅ `API_USAGE_EXAMPLES.md` - 使用示例
- ✅ `DEPLOYMENT_GUIDE.md` - 部署指南
- ✅ `DELIVERY_CHECKLIST.md` - 本文档

#### 技术文档
- ✅ `docs/AI_INNOVATION.md` - 技术创新文档（15+页）
- ✅ `docs/IMPLEMENTATION_LOG.md` - 详细实施日志

#### 分析报告
- ✅ `outputs/correlation_analysis/correlation_analysis_report.md` - 相关性分析报告

### 3. 数据文件

- ✅ `data/processed/hiv_data_processed.csv` - 处理后的训练数据（190样本）

### 4. Docker镜像

- ✅ Docker镜像: `hiv-risk-api:v1.1.0`
- ✅ 镜像大小: ~500MB（预估）
- ✅ 包含所有依赖和模型文件

---

## 🚀 快速启动命令

### 方式1: Docker（推荐）

```bash
# 1. 构建镜像
docker build -t hiv-risk-api:v1.1.0 .

# 2. 运行容器
docker run -d -p 5000:5000 \
  -e USE_ENHANCED_MODEL=true \
  -v $(pwd)/logs:/app/logs \
  --name hiv-api \
  hiv-risk-api:v1.1.0

# 3. 查看日志
docker logs -f hiv-api

# 4. 测试
curl http://localhost:5000/health

# 5. 停止容器
docker stop hiv-api

# 6. 删除容器
docker rm hiv-api
```

### 方式2: Docker Compose

```bash
# 1. 启动服务
docker-compose up -d

# 2. 查看日志
docker-compose logs -f

# 3. 测试
curl http://localhost:5000/health

# 4. 停止服务
docker-compose down
```

### 方式3: 本地Python环境

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

---

## 📋 部署前检查

### 1. 文件完整性检查

```bash
# 检查模型文件
ls -lh saved_models/final_model_3to5.pkl
# 应该显示: -rw-r--r-- 1 user user 1.1M

# 检查Python文件
find . -name "*.py" -type f | wc -l
# 应该有15+个Python文件

# 检查文档文件
ls -1 *.md
# 应该显示: README.md, API_DOCUMENTATION.md, 等
```

### 2. 依赖检查

```bash
# 检查requirements.txt
cat requirements.txt

# 应该包含:
# flask>=2.0.0
# flask-cors>=3.0.10
# numpy>=1.21.0
# pandas>=1.3.0
# scikit-learn>=1.0.0
# joblib>=1.1.0
# shap>=0.41.0
```

### 3. Docker环境检查

```bash
# 检查Docker版本
docker --version
# 应该 >= 20.10

# 检查Docker Compose版本
docker-compose --version
# 应该 >= 1.29
```

---

## 🔧 环境变量配置

### 必需环境变量

无（所有变量都有默认值）

### 可选环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| USE_ENHANCED_MODEL | true | 是否启用增强模型（DG-DAA） |
| PORT | 5000 | API服务端口 |
| HOST | 0.0.0.0 | API服务主机 |
| DEBUG | false | 是否启用调试模式 |

### 配置示例

```bash
# 使用基础模型
docker run -d -p 5000:5000 \
  -e USE_ENHANCED_MODEL=false \
  hiv-risk-api:v1.1.0

# 使用不同端口
docker run -d -p 8080:8080 \
  -e PORT=8080 \
  hiv-risk-api:v1.1.0

# 启用调试模式
docker run -d -p 5000:5000 \
  -e DEBUG=true \
  hiv-risk-api:v1.1.0
```

---

## 📦 Docker镜像打包

### 导出镜像

```bash
# 1. 构建镜像
docker build -t hiv-risk-api:v1.1.0 .

# 2. 导出为tar文件
docker save hiv-risk-api:v1.1.0 -o hiv-risk-api-v1.1.0.tar

# 3. 压缩（可选）
gzip hiv-risk-api-v1.1.0.tar
# 生成: hiv-risk-api-v1.1.0.tar.gz

# 4. 查看文件大小
ls -lh hiv-risk-api-v1.1.0.tar.gz
```

### 导入镜像

```bash
# 1. 解压（如果压缩了）
gunzip hiv-risk-api-v1.1.0.tar.gz

# 2. 导入镜像
docker load -i hiv-risk-api-v1.1.0.tar

# 3. 验证
docker images | grep hiv-risk-api

# 4. 运行
docker run -d -p 5000:5000 hiv-risk-api:v1.1.0
```

---

## 🧪 功能测试

### 1. 健康检查

```bash
curl http://localhost:5000/health

# 预期输出:
# {"status":"healthy","model_loaded":true,"timestamp":"..."}
```

### 2. 模型信息

```bash
curl http://localhost:5000/v1/model/info

# 预期输出:
# {"model_version":"1.1.0","feature_count":110,...}
```

### 3. 基础预测

```bash
curl -X POST http://localhost:5000/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "features": {
      "存活数": 1000,
      "感染率": 0.5,
      "治疗覆盖率": 85.0
    }
  }'

# 预期输出:
# {"success":true,"prediction":{"risk_level":3,...}}
```

### 4. 增强预测（含特征贡献度）

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

# 预期输出:
# {"success":true,"prediction":{...},"feature_contributions":{...}}
```

### 5. 特征重要性

```bash
curl http://localhost:5000/v1/model/feature_importance?top_k=10

# 预期输出:
# {"success":true,"feature_importance":[...]}
```

---

## 📊 性能指标

### 预期性能

| 指标 | 值 |
|------|-----|
| 启动时间 | < 30秒 |
| 单次预测响应时间 | < 50ms |
| 内存占用 | ~500MB |
| CPU占用 | < 10% (空闲时) |
| 并发能力 | 100+ QPS |

### 性能测试

```bash
# 1. 启动时间测试
time docker run --rm hiv-risk-api:v1.1.0 python -c "from models.predictor import HIVRiskPredictor; HIVRiskPredictor('saved_models/final_model_3to5.pkl')"

# 2. 响应时间测试
time curl http://localhost:5000/v1/predict -X POST -H "Content-Type: application/json" -d '{"features":{...}}'

# 3. 并发测试（需要安装ab）
ab -n 1000 -c 10 -p test_data.json -T application/json http://localhost:5000/v1/predict
```

---

## 🔒 安全检查

### 1. 端口安全

```bash
# 确保只暴露必要的端口
docker ps | grep hiv-api
# 应该只看到: 0.0.0.0:5000->5000/tcp
```

### 2. 文件权限

```bash
# 检查模型文件权限
ls -l saved_models/final_model_3to5.pkl
# 应该是: -rw-r--r-- (644)
```

### 3. 环境变量

```bash
# 不要在环境变量中存储敏感信息
# 如需API密钥，使用Docker secrets或配置文件
```

---

## 📝 交付文件打包

### 完整打包

```bash
# 1. 创建交付目录
mkdir -p hiv_delivery_v1.1.0

# 2. 复制必要文件
cp -r api models saved_models data hiv_delivery_v1.1.0/
cp requirements.txt Dockerfile docker-compose.yml .dockerignore hiv_delivery_v1.1.0/
cp README.md API_*.md DEPLOYMENT_GUIDE.md DELIVERY_CHECKLIST.md hiv_delivery_v1.1.0/
cp -r docs hiv_delivery_v1.1.0/

# 3. 打包
tar -czf hiv_delivery_v1.1.0.tar.gz hiv_delivery_v1.1.0/

# 4. 查看大小
ls -lh hiv_delivery_v1.1.0.tar.gz
```

### 仅Docker镜像

```bash
# 导出Docker镜像
docker save hiv-risk-api:v1.1.0 | gzip > hiv-risk-api-v1.1.0.tar.gz
```

---

## 🎯 交付检查清单

### 部署前

- [ ] 所有文件已复制到目标服务器
- [ ] Docker已安装（版本 >= 20.10）
- [ ] Docker Compose已安装（版本 >= 1.29）
- [ ] 端口5000可用
- [ ] 磁盘空间充足（至少2GB）

### 部署中

- [ ] Docker镜像构建成功
- [ ] 容器启动成功
- [ ] 健康检查通过
- [ ] 日志无错误

### 部署后

- [ ] API响应正常
- [ ] 预测功能正常
- [ ] 性能指标达标
- [ ] 文档已交付

---

## 📞 支持信息

### 常见问题

1. **端口被占用**: 修改PORT环境变量或docker-compose.yml中的端口映射
2. **模型加载失败**: 检查saved_models/final_model_3to5.pkl文件是否存在
3. **内存不足**: 增加Docker内存限制或减少worker数量
4. **响应超时**: 检查网络连接和服务器负载

### 联系方式

如有问题，请联系项目组。

---

**文档版本**: 1.0.0  
**最后更新**: 2025-11-04  
**适用版本**: v1.1.0
