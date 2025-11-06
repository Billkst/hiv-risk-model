# HIV风险评估模型 - 部署文档

## 📋 目录
- [系统要求](#系统要求)
- [文件清单](#文件清单)
- [部署方式](#部署方式)
- [启动命令](#启动命令)
- [健康检查](#健康检查)
- [故障排查](#故障排查)

---

## 系统要求

### 硬件要求
- **CPU**: 2核心或以上
- **内存**: 2GB或以上
- **磁盘**: 500MB可用空间

### 软件要求
- **Python**: 3.9+
- **Docker**: 20.10+ (如使用Docker部署)
- **操作系统**: Linux/Windows/MacOS

---

## 文件清单

### 必需文件

```
hiv_risk_model/
├── api/
│   └── app.py                          # API服务主文件
├── models/
│   └── predictor.py                    # 预测器类
├── saved_models/
│   └── final_model_3to5.pkl           # 模型权重文件 (1.13MB)
├── requirements.txt                    # Python依赖
├── Dockerfile                          # Docker镜像配置
└── docker-compose.yml                  # Docker编排配置
```

### 模型权重文件
- **文件名**: `final_model_3to5.pkl`
- **路径**: `saved_models/final_model_3to5.pkl`
- **大小**: 1.13 MB
- **格式**: Python pickle格式
- **包含内容**:
  - 训练好的Gradient Boosting模型
  - 特征标准化器(Scaler)
  - 特征列名列表
  - 模型元数据

---

## 部署方式

### 方式1: Docker部署 (推荐)

#### 1.1 构建Docker镜像

```bash
# 进入项目目录
cd hiv_project/hiv_risk_model

# 构建镜像
docker build -t hiv-risk-api:1.0.0 .
```

#### 1.2 运行容器

**方式A: 使用docker run**
```bash
docker run -d \
  --name hiv-risk-api \
  -p 5000:5000 \
  -v $(pwd)/saved_models:/app/saved_models:ro \
  --restart unless-stopped \
  hiv-risk-api:1.0.0
```

**方式B: 使用docker-compose (推荐)**
```bash
docker-compose up -d
```

#### 1.3 查看日志
```bash
docker logs -f hiv-risk-api
```

#### 1.4 停止服务
```bash
docker-compose down
# 或
docker stop hiv-risk-api
```

---

### 方式2: 直接部署

#### 2.1 安装依赖

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

#### 2.2 启动服务

**开发模式:**
```bash
python api/app.py
```

**生产模式 (使用Gunicorn):**
```bash
gunicorn --bind 0.0.0.0:5000 \
         --workers 4 \
         --timeout 120 \
         --access-logfile logs/access.log \
         --error-logfile logs/error.log \
         api.app:app
```

---

## 启动命令

### 平台部署启动命令

根据您公司平台的要求，提供以下启动命令选项：

#### Docker启动命令
```bash
docker run -d \
  --name hiv-risk-api \
  -p 5000:5000 \
  -v /path/to/saved_models:/app/saved_models:ro \
  --restart unless-stopped \
  hiv-risk-api:1.0.0
```

#### Python直接启动
```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 api.app:app
```

#### 环境变量配置
```bash
# 端口配置
export PORT=5000

# 主机配置
export HOST=0.0.0.0

# 工作进程数
export WORKERS=4
```

---

## 服务端点

### 基础URL
```
http://<服务器IP>:5000
```

### API端点列表

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | API首页 |
| `/health` | GET | 健康检查 |
| `/v1/model/info` | GET | 模型信息 |
| `/v1/predict` | POST | 单样本预测 |
| `/v1/predict/batch` | POST | 批量预测 |

---

## 健康检查

### 检查命令

```bash
# 使用curl
curl http://localhost:5000/health

# 使用wget
wget -qO- http://localhost:5000/health

# 使用Python
python -c "import requests; print(requests.get('http://localhost:5000/health').json())"
```

### 预期响应

```json
{
  "status": "healthy",
  "model_loaded": true,
  "timestamp": "2024-01-01T12:00:00.000000"
}
```

---

## 性能指标

- **启动时间**: < 10秒
- **单次预测延迟**: < 50ms
- **并发处理能力**: 100+ QPS (4 workers)
- **内存占用**: ~200MB
- **CPU占用**: < 10% (空闲时)

---

## 日志

### 日志位置
- **访问日志**: `logs/access.log`
- **错误日志**: `logs/error.log`
- **Docker日志**: `docker logs hiv-risk-api`

### 日志级别
- INFO: 正常请求
- WARNING: 警告信息
- ERROR: 错误信息

---

## 故障排查

### 问题1: 模型加载失败

**症状**: 启动时提示"模型加载失败"

**解决方案**:
1. 检查模型文件是否存在: `ls -lh saved_models/final_model_3to5.pkl`
2. 检查文件权限: `chmod 644 saved_models/final_model_3to5.pkl`
3. 检查文件完整性: 文件大小应为 1.13MB

### 问题2: 端口被占用

**症状**: 启动时提示"Address already in use"

**解决方案**:
```bash
# 查找占用端口的进程
lsof -i :5000

# 杀死进程
kill -9 <PID>

# 或使用其他端口
export PORT=5001
```

### 问题3: 依赖安装失败

**症状**: pip install 报错

**解决方案**:
```bash
# 升级pip
pip install --upgrade pip

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题4: 预测返回错误

**症状**: API返回500错误

**解决方案**:
1. 检查请求格式是否正确
2. 查看错误日志: `docker logs hiv-risk-api`
3. 确认所有必需特征都已提供

---

## 安全建议

1. **生产环境**:
   - 使用HTTPS
   - 添加API认证(Token/API Key)
   - 限制请求频率
   - 配置防火墙规则

2. **数据安全**:
   - 不要在日志中记录敏感数据
   - 定期备份模型文件
   - 使用只读挂载模型文件

3. **监控**:
   - 配置健康检查
   - 监控CPU/内存使用
   - 设置告警规则

---

## 联系支持

如有问题，请联系技术支持团队。

**文档版本**: 1.0.0  
**最后更新**: 2024-01-01
