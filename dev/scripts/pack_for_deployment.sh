#!/bin/bash

# HIV风险评估模型 - 正确的部署打包脚本
# 只打包运行服务必需的文件，不包含训练数据

echo "=========================================="
echo "  HIV风险评估模型 - 部署打包"
echo "=========================================="
echo ""

# 创建时间戳
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PACKAGE_NAME="hiv_risk_deployment_${TIMESTAMP}"

echo "📦 创建部署包: $PACKAGE_NAME"
echo ""

# 创建临时目录
mkdir -p $PACKAGE_NAME

# ============================================
# 1. 打包必需的代码文件
# ============================================
echo "[1/6] 📝 复制代码文件..."

mkdir -p $PACKAGE_NAME/api
mkdir -p $PACKAGE_NAME/models

cp api/app.py $PACKAGE_NAME/api/
echo "  ✓ api/app.py"

cp models/predictor.py $PACKAGE_NAME/models/
echo "  ✓ models/predictor.py"

# ============================================
# 2. 打包模型权重文件（最重要！）
# ============================================
echo ""
echo "[2/6] 🎯 复制模型权重..."

mkdir -p $PACKAGE_NAME/saved_models

if [ -f "saved_models/final_model_3to5.pkl" ]; then
    cp saved_models/final_model_3to5.pkl $PACKAGE_NAME/saved_models/
    SIZE=$(ls -lh saved_models/final_model_3to5.pkl | awk '{print $5}')
    echo "  ✓ saved_models/final_model_3to5.pkl ($SIZE)"
else
    echo "  ❌ 错误: 模型文件不存在！"
    exit 1
fi

# ============================================
# 3. 打包配置文件
# ============================================
echo ""
echo "[3/6] ⚙️  复制配置文件..."

cp requirements.txt $PACKAGE_NAME/
echo "  ✓ requirements.txt"

cp Dockerfile $PACKAGE_NAME/
echo "  ✓ Dockerfile"

cp docker-compose.yml $PACKAGE_NAME/
echo "  ✓ docker-compose.yml"

if [ -f ".dockerignore" ]; then
    cp .dockerignore $PACKAGE_NAME/
    echo "  ✓ .dockerignore"
fi

# ============================================
# 4. 打包文档
# ============================================
echo ""
echo "[4/6] 📚 复制文档..."

mkdir -p $PACKAGE_NAME/docs

cp README.md $PACKAGE_NAME/docs/ 2>/dev/null && echo "  ✓ README.md"
cp DEPLOYMENT.md $PACKAGE_NAME/docs/ 2>/dev/null && echo "  ✓ DEPLOYMENT.md"
cp API_DOCUMENTATION.md $PACKAGE_NAME/docs/ 2>/dev/null && echo "  ✓ API_DOCUMENTATION.md"
cp QUICK_START.md $PACKAGE_NAME/docs/ 2>/dev/null && echo "  ✓ QUICK_START.md"
cp WHAT_TO_SUBMIT.md $PACKAGE_NAME/docs/ 2>/dev/null && echo "  ✓ WHAT_TO_SUBMIT.md"

# ============================================
# 5. 创建启动说明
# ============================================
echo ""
echo "[5/6] 📋 创建启动说明..."

cat > $PACKAGE_NAME/启动说明.txt << 'EOF'
# HIV风险评估模型 - 启动说明

## 快速启动

### 方式1: 使用Docker Compose (推荐)
```bash
docker-compose up -d
```

### 方式2: 使用Docker
```bash
# 构建镜像
docker build -t hiv-risk-api:1.0.0 .

# 运行容器
docker run -d \
  --name hiv-risk-api \
  -p 5000:5000 \
  -v $(pwd)/saved_models:/app/saved_models:ro \
  --restart unless-stopped \
  hiv-risk-api:1.0.0
```

### 方式3: 直接运行
```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python api/app.py

# 或使用Gunicorn (生产环境)
gunicorn --bind 0.0.0.0:5000 --workers 4 api.app:app
```

## 验证服务

```bash
# 健康检查
curl http://localhost:5000/health

# 预期响应
{
  "status": "healthy",
  "model_loaded": true,
  "timestamp": "..."
}
```

## 平台配置参数

- 启动命令: gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 api.app:app
- 健康检查URL: http://localhost:5000/health
- 端口: 5000
- CPU: 2核心
- 内存: 2GB
- 磁盘: 500MB

## 文档位置

- 部署文档: docs/DEPLOYMENT.md
- API文档: docs/API_DOCUMENTATION.md
- 快速开始: docs/QUICK_START.md

## 技术支持

如有问题，请查看文档或联系技术支持。
EOF

echo "  ✓ 启动说明.txt"

# ============================================
# 6. 创建文件清单
# ============================================
echo ""
echo "[6/6] 📄 创建文件清单..."

cat > $PACKAGE_NAME/文件清单.txt << EOF
# 部署包文件清单

生成时间: $(date)
包名称: $PACKAGE_NAME

## 目录结构

$(tree -L 2 $PACKAGE_NAME 2>/dev/null || find $PACKAGE_NAME -type f | sort)

## 文件说明

### 代码文件
- api/app.py              : API服务主文件
- models/predictor.py     : 预测器类

### 模型文件
- saved_models/final_model_3to5.pkl : 模型权重 (1.13MB)

### 配置文件
- requirements.txt        : Python依赖
- Dockerfile             : Docker镜像配置
- docker-compose.yml     : Docker编排配置

### 文档
- docs/README.md         : 项目说明
- docs/DEPLOYMENT.md     : 部署文档
- docs/API_DOCUMENTATION.md : API接口文档
- docs/QUICK_START.md    : 快速开始
- docs/WHAT_TO_SUBMIT.md : 提交说明

### 说明文件
- 启动说明.txt          : 快速启动指南
- 文件清单.txt          : 本文件

## 文件大小统计

总大小: $(du -sh $PACKAGE_NAME | awk '{print $1}')

各部分大小:
- 代码: $(du -sh $PACKAGE_NAME/api $PACKAGE_NAME/models 2>/dev/null | awk '{sum+=$1} END {print sum}')KB
- 模型: $(du -sh $PACKAGE_NAME/saved_models 2>/dev/null | awk '{print $1}')
- 配置: $(du -sh $PACKAGE_NAME/*.txt $PACKAGE_NAME/Dockerfile $PACKAGE_NAME/docker-compose.yml 2>/dev/null | awk '{sum+=$1} END {print sum}')KB
- 文档: $(du -sh $PACKAGE_NAME/docs 2>/dev/null | awk '{print $1}')

## 注意事项

✅ 已包含: 运行服务必需的所有文件
❌ 未包含: 训练数据、开发工具、测试代码

这个包可以直接部署到生产环境！
EOF

echo "  ✓ 文件清单.txt"

# ============================================
# 7. 创建压缩包
# ============================================
echo ""
echo "📦 创建压缩包..."

tar -czf ${PACKAGE_NAME}.tar.gz $PACKAGE_NAME
PACKAGE_SIZE=$(ls -lh ${PACKAGE_NAME}.tar.gz | awk '{print $5}')

echo "  ✓ ${PACKAGE_NAME}.tar.gz ($PACKAGE_SIZE)"

# ============================================
# 8. 显示摘要
# ============================================
echo ""
echo "=========================================="
echo "  ✅ 打包完成！"
echo "=========================================="
echo ""
echo "📦 部署包信息:"
echo "  - 目录: $PACKAGE_NAME/"
echo "  - 压缩包: ${PACKAGE_NAME}.tar.gz"
echo "  - 大小: $PACKAGE_SIZE"
echo ""
echo "📁 包含文件:"
echo "  ✓ API服务代码"
echo "  ✓ 预测器代码"
echo "  ✓ 模型权重 (1.13MB)"
echo "  ✓ 配置文件"
echo "  ✓ 完整文档"
echo "  ✓ 启动说明"
echo ""
echo "❌ 不包含:"
echo "  ✗ 训练数据 (data/)"
echo "  ✗ 开发工具 (utils/)"
echo "  ✗ 测试代码 (tests/)"
echo "  ✗ Jupyter笔记本"
echo ""
echo "📋 下一步:"
echo "  1. 查看文件: ls -lh $PACKAGE_NAME/"
echo "  2. 查看清单: cat $PACKAGE_NAME/文件清单.txt"
echo "  3. 查看说明: cat $PACKAGE_NAME/启动说明.txt"
echo "  4. 提交压缩包: ${PACKAGE_NAME}.tar.gz"
echo ""
echo "=========================================="
