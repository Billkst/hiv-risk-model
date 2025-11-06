#!/bin/bash

# HIV风险评估模型 - 部署包准备脚本
# 用于打包所有需要提交给公司平台的文件

echo "=========================================="
echo "  HIV风险评估模型 - 部署包准备"
echo "=========================================="

# 创建部署目录
DEPLOY_DIR="deployment_package_$(date +%Y%m%d_%H%M%S)"
echo "创建部署目录: $DEPLOY_DIR"
mkdir -p $DEPLOY_DIR

# 1. 复制模型权重文件
echo ""
echo "[1/7] 复制模型权重文件..."
mkdir -p $DEPLOY_DIR/saved_models
cp saved_models/final_model_3to5.pkl $DEPLOY_DIR/saved_models/
echo "✓ 模型文件: $(ls -lh saved_models/final_model_3to5.pkl | awk '{print $5}')"

# 2. 复制代码文件
echo ""
echo "[2/7] 复制代码文件..."
mkdir -p $DEPLOY_DIR/api
mkdir -p $DEPLOY_DIR/models
cp api/app.py $DEPLOY_DIR/api/
cp models/predictor.py $DEPLOY_DIR/models/
echo "✓ API服务文件"
echo "✓ 预测器文件"

# 3. 复制配置文件
echo ""
echo "[3/7] 复制配置文件..."
cp requirements.txt $DEPLOY_DIR/
cp Dockerfile $DEPLOY_DIR/
cp docker-compose.yml $DEPLOY_DIR/
cp .dockerignore $DEPLOY_DIR/
echo "✓ 依赖配置"
echo "✓ Docker配置"

# 4. 复制文档
echo ""
echo "[4/7] 复制文档..."
cp README.md $DEPLOY_DIR/
cp DEPLOYMENT.md $DEPLOY_DIR/
cp API_DOCUMENTATION.md $DEPLOY_DIR/
cp QUICK_START.md $DEPLOY_DIR/
echo "✓ README"
echo "✓ 部署文档"
echo "✓ API文档"
echo "✓ 快速开始指南"

# 5. 复制测试脚本
echo ""
echo "[5/7] 复制测试脚本..."
cp test_api.py $DEPLOY_DIR/
echo "✓ API测试脚本"

# 6. 构建Docker镜像
echo ""
echo "[6/7] 构建Docker镜像..."
docker build -t hiv-risk-api:1.0.0 . > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ Docker镜像构建成功"
    
    # 导出Docker镜像
    echo "  导出Docker镜像..."
    docker save hiv-risk-api:1.0.0 -o $DEPLOY_DIR/hiv-risk-api-1.0.0.tar
    echo "  ✓ 镜像文件: $(ls -lh $DEPLOY_DIR/hiv-risk-api-1.0.0.tar | awk '{print $5}')"
else
    echo "⚠ Docker镜像构建失败（可选）"
fi

# 7. 创建部署说明文件
echo ""
echo "[7/7] 创建部署说明..."
cat > $DEPLOY_DIR/SUBMIT_CHECKLIST.md << 'EOF'
# 提交清单

## 📦 文件列表

### 1. 模型权重文件
- [x] `saved_models/final_model_3to5.pkl` (1.13 MB)

### 2. 代码文件
- [x] `api/app.py` - API服务主文件
- [x] `models/predictor.py` - 预测器类

### 3. 配置文件
- [x] `requirements.txt` - Python依赖
- [x] `Dockerfile` - Docker镜像配置
- [x] `docker-compose.yml` - Docker编排配置
- [x] `.dockerignore` - Docker构建忽略文件

### 4. Docker镜像
- [x] `hiv-risk-api-1.0.0.tar` (~500MB)

### 5. 文档
- [x] `README.md` - 项目总览
- [x] `DEPLOYMENT.md` - 部署文档
- [x] `API_DOCUMENTATION.md` - API接口文档
- [x] `QUICK_START.md` - 快速开始指南

### 6. 测试工具
- [x] `test_api.py` - API测试脚本

---

## 🚀 平台配置信息

### 启动命令
```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 api.app:app
```

### Docker启动命令
```bash
docker run -d \
  --name hiv-risk-api \
  -p 5000:5000 \
  -v /path/to/saved_models:/app/saved_models:ro \
  --restart unless-stopped \
  hiv-risk-api:1.0.0
```

### 环境变量
```
PORT=5000
HOST=0.0.0.0
WORKERS=4
```

### 健康检查URL
```
http://localhost:5000/health
```

### 资源配置
- CPU: 2核心
- 内存: 2GB
- 磁盘: 500MB

### 端口映射
- 容器端口: 5000
- 主机端口: 5000 (可调整)

---

## 📡 API端点

- 健康检查: `GET /health`
- 模型信息: `GET /v1/model/info`
- 单样本预测: `POST /v1/predict`
- 批量预测: `POST /v1/predict/batch`

---

## ✅ 验证步骤

1. 解压部署包
2. 加载Docker镜像: `docker load -i hiv-risk-api-1.0.0.tar`
3. 启动服务: `docker-compose up -d`
4. 健康检查: `curl http://localhost:5000/health`
5. 运行测试: `python test_api.py`

---

## 📞 技术支持

如有问题，请联系技术支持团队。

**准备时间**: $(date)
**版本**: 1.0.0
EOF

echo "✓ 部署说明文件"

# 8. 创建压缩包
echo ""
echo "创建压缩包..."
tar -czf ${DEPLOY_DIR}.tar.gz $DEPLOY_DIR
echo "✓ 压缩包: ${DEPLOY_DIR}.tar.gz"

# 显示摘要
echo ""
echo "=========================================="
echo "  部署包准备完成！"
echo "=========================================="
echo ""
echo "部署目录: $DEPLOY_DIR"
echo "压缩包: ${DEPLOY_DIR}.tar.gz"
echo ""
echo "文件清单:"
echo "  - 模型权重: saved_models/final_model_3to5.pkl"
echo "  - Docker镜像: hiv-risk-api-1.0.0.tar"
echo "  - 代码文件: api/, models/"
echo "  - 配置文件: requirements.txt, Dockerfile, etc."
echo "  - 文档: README.md, DEPLOYMENT.md, etc."
echo ""
echo "下一步:"
echo "  1. 查看部署说明: cat $DEPLOY_DIR/SUBMIT_CHECKLIST.md"
echo "  2. 提交压缩包: ${DEPLOY_DIR}.tar.gz"
echo "  3. 或提交目录: $DEPLOY_DIR/"
echo ""
echo "=========================================="
