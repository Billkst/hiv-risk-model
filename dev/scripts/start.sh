#!/bin/bash
# HIV风险评估API - 快速启动脚本
# 版本: v1.1.0

set -e

echo "========================================================================"
echo "  HIV风险评估API - 快速启动"
echo "========================================================================"

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

echo "✓ Docker已安装"

# 检查docker-compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "⚠️  docker-compose未安装，将使用docker命令"
    USE_COMPOSE=false
else
    echo "✓ docker-compose已安装"
    USE_COMPOSE=true
fi

# 检查模型文件
if [ ! -f "saved_models/final_model_3to5.pkl" ]; then
    echo "❌ 模型文件不存在: saved_models/final_model_3to5.pkl"
    exit 1
fi

echo "✓ 模型文件存在"

# 构建镜像
echo ""
echo "步骤1: 构建Docker镜像..."
docker build -t hiv-risk-api:v1.1.0 .

if [ $? -eq 0 ]; then
    echo "✓ 镜像构建成功"
else
    echo "❌ 镜像构建失败"
    exit 1
fi

# 停止旧容器（如果存在）
echo ""
echo "步骤2: 清理旧容器..."
if docker ps -a | grep -q hiv-api; then
    docker stop hiv-api 2>/dev/null || true
    docker rm hiv-api 2>/dev/null || true
    echo "✓ 旧容器已清理"
else
    echo "✓ 无需清理"
fi

# 启动容器
echo ""
echo "步骤3: 启动服务..."

if [ "$USE_COMPOSE" = true ]; then
    docker-compose up -d
else
    docker run -d -p 5000:5000 \
      -e USE_ENHANCED_MODEL=true \
      -v $(pwd)/logs:/app/logs \
      --name hiv-api \
      hiv-risk-api:v1.1.0
fi

# 等待服务启动
echo ""
echo "步骤4: 等待服务启动..."
sleep 5

# 健康检查
echo ""
echo "步骤5: 健康检查..."
for i in {1..10}; do
    if curl -s http://localhost:5000/health > /dev/null 2>&1; then
        echo "✓ 服务启动成功"
        break
    else
        if [ $i -eq 10 ]; then
            echo "❌ 服务启动失败"
            echo ""
            echo "查看日志:"
            docker logs hiv-api
            exit 1
        fi
        echo "  等待中... ($i/10)"
        sleep 2
    fi
done

# 显示服务信息
echo ""
echo "========================================================================"
echo "  ✓ HIV风险评估API已成功启动"
echo "========================================================================"
echo ""
echo "  服务地址: http://localhost:5000"
echo "  API文档: http://localhost:5000/"
echo "  健康检查: http://localhost:5000/health"
echo ""
echo "  查看日志: docker logs -f hiv-api"
echo "  停止服务: docker stop hiv-api"
echo "  重启服务: docker restart hiv-api"
echo ""
echo "========================================================================"

# 测试API
echo ""
echo "测试API..."
curl -s http://localhost:5000/ | python3 -m json.tool | head -20

echo ""
echo "✓ 启动完成！"
