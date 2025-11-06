# HIV风险评估模型 - Docker镜像
# 版本: v1.1.0
# Python: 3.9

FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    USE_ENHANCED_MODEL=true \
    PORT=5000 \
    HOST=0.0.0.0 \
    DEBUG=false

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY api/ ./api/
COPY models/ ./models/
COPY saved_models/ ./saved_models/
COPY data/ ./data/

# 创建日志目录
RUN mkdir -p logs

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health')" || exit 1

# 启动命令
CMD ["python", "-u", "api/app.py"]
