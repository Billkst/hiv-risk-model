# HIV风险评估模型 - 部署指南

## 📋 目录
- [系统要求](#系统要求)
- [环境准备](#环境准备)
- [安装步骤](#安装步骤)
- [配置说明](#配置说明)
- [启动服务](#启动服务)
- [生产环境部署](#生产环境部署)
- [监控和维护](#监控和维护)
- [故障排查](#故障排查)

---

## 系统要求

### 硬件要求

**最低配置**:
- CPU: 2核
- 内存: 4GB
- 磁盘: 10GB

**推荐配置**:
- CPU: 4核或更多
- 内存: 8GB或更多
- 磁盘: 20GB或更多（用于日志和数据）

### 软件要求

- **操作系统**: Linux (Ubuntu 20.04+, CentOS 7+) 或 macOS
- **Python**: 3.9 或更高版本
- **Conda**: Miniconda 或 Anaconda（推荐）
- **网络**: 需要访问外网（用于安装依赖）

---

## 环境准备

### 1. 安装Conda

```bash
# 下载Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

# 安装
bash Miniconda3-latest-Linux-x86_64.sh

# 初始化
conda init bash
source ~/.bashrc
```

### 2. 创建Python环境

```bash
# 创建虚拟环境
conda create -n hivenv python=3.9 -y

# 激活环境
conda activate hivenv
```

### 3. 安装依赖

```bash
# 进入项目目录
cd hiv_project/hiv_risk_model

# 安装依赖
pip install -r requirements.txt
```

**requirements.txt内容**:
```
flask>=2.0.0
flask-cors>=3.0.10
numpy>=1.21.0
pandas>=1.3.0
scikit-learn>=1.0.0
joblib>=1.1.0
shap>=0.41.0
```

---

## 安装步骤

### 步骤1: 获取代码

```bash
# 克隆或下载项目代码
git clone <repository_url>
cd hiv_project/hiv_risk_model
```

### 步骤2: 验证模型文件

```bash
# 检查模型文件是否存在
ls -lh saved_models/final_model_3to5.pkl

# 应该看到类似输出：
# -rw-r--r-- 1 user user 1.1M Nov 04 16:00 final_model_3to5.pkl
```

### 步骤3: 测试模型加载

```bash
# 测试模型是否能正常加载
python3 -c "
from models.predictor import HIVRiskPredictor
predictor = HIVRiskPredictor('saved_models/final_model_3to5.pkl')
print('✓ 模型加载成功')
"
```



### 步骤4: 测试API服务

```bash
# 启动API服务（测试模式）
python3 api/app.py

# 在另一个终端测试
curl http://localhost:5000/health

# 应该看到：
# {"status":"healthy","model_loaded":true,"timestamp":"..."}
```

---

## 配置说明

### 环境变量配置

创建配置文件 `.env`:

```bash
# API配置
PORT=5000
HOST=0.0.0.0
DEBUG=false

# 模型配置
USE_ENHANCED_MODEL=true
MODEL_VERSION=1.1.0

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/api.log
```

### 加载环境变量

```bash
# 方法1: 使用export
export USE_ENHANCED_MODEL=true
export PORT=5000

# 方法2: 使用.env文件
pip install python-dotenv

# 在app.py中添加：
# from dotenv import load_dotenv
# load_dotenv()
```

---

## 启动服务

### 开发环境启动

```bash
# 激活环境
conda activate hivenv

# 启动服务
python3 api/app.py

# 或使用环境变量
USE_ENHANCED_MODEL=true PORT=5000 python3 api/app.py
```

### 后台运行

```bash
# 使用nohup后台运行
nohup python3 api/app.py > logs/api.log 2>&1 &

# 查看进程
ps aux | grep app.py

# 查看日志
tail -f logs/api.log
```

### 使用systemd管理（推荐）

创建服务文件 `/etc/systemd/system/hiv-api.service`:

```ini
[Unit]
Description=HIV Risk Assessment API Service
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/hiv_project/hiv_risk_model
Environment="PATH=/path/to/conda/envs/hivenv/bin"
Environment="USE_ENHANCED_MODEL=true"
Environment="PORT=5000"
ExecStart=/path/to/conda/envs/hivenv/bin/python3 api/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
# 重新加载systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start hiv-api

# 设置开机自启
sudo systemctl enable hiv-api

# 查看状态
sudo systemctl status hiv-api

# 查看日志
sudo journalctl -u hiv-api -f
```

---

## 生产环境部署

### 使用Gunicorn（推荐）

#### 1. 安装Gunicorn

```bash
pip install gunicorn
```

#### 2. 创建Gunicorn配置文件

创建 `gunicorn_config.py`:

```python
# Gunicorn配置
bind = "0.0.0.0:5000"
workers = 4  # 建议：CPU核心数 * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# 日志
accesslog = "logs/gunicorn_access.log"
errorlog = "logs/gunicorn_error.log"
loglevel = "info"

# 进程管理
daemon = False
pidfile = "logs/gunicorn.pid"

# 性能优化
preload_app = True
max_requests = 1000
max_requests_jitter = 50
```

#### 3. 启动Gunicorn

```bash
# 创建日志目录
mkdir -p logs

# 启动
gunicorn -c gunicorn_config.py api.app:app

# 或使用systemd管理
# 修改ExecStart为：
# ExecStart=/path/to/conda/envs/hivenv/bin/gunicorn -c gunicorn_config.py api.app:app
```

### 使用Nginx反向代理

#### 1. 安装Nginx

```bash
sudo apt-get update
sudo apt-get install nginx
```

#### 2. 配置Nginx

创建 `/etc/nginx/sites-available/hiv-api`:

```nginx
upstream hiv_api {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name your_domain.com;

    # 日志
    access_log /var/log/nginx/hiv-api-access.log;
    error_log /var/log/nginx/hiv-api-error.log;

    # 请求大小限制
    client_max_body_size 10M;

    # 超时设置
    proxy_connect_timeout 30s;
    proxy_send_timeout 30s;
    proxy_read_timeout 30s;

    location / {
        proxy_pass http://hiv_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 健康检查
    location /health {
        proxy_pass http://hiv_api/health;
        access_log off;
    }
}
```

#### 3. 启用配置

```bash
# 创建软链接
sudo ln -s /etc/nginx/sites-available/hiv-api /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启Nginx
sudo systemctl restart nginx
```

### HTTPS配置（使用Let's Encrypt）

```bash
# 安装certbot
sudo apt-get install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your_domain.com

# 自动续期
sudo certbot renew --dry-run
```

---

## 监控和维护

### 日志管理

#### 1. 日志轮转

创建 `/etc/logrotate.d/hiv-api`:

```
/path/to/hiv_project/hiv_risk_model/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 your_user your_group
    sharedscripts
    postrotate
        systemctl reload hiv-api > /dev/null 2>&1 || true
    endscript
}
```

#### 2. 查看日志

```bash
# 实时查看日志
tail -f logs/api.log

# 查看最近100行
tail -n 100 logs/api.log

# 搜索错误
grep ERROR logs/api.log

# 查看systemd日志
sudo journalctl -u hiv-api -n 100
```

### 性能监控

#### 1. 系统资源监控

```bash
# CPU和内存使用
top -p $(pgrep -f "python3 api/app.py")

# 详细信息
htop

# 网络连接
netstat -an | grep :5000
```

#### 2. API性能监控

```bash
# 简单的健康检查脚本
cat > monitor.sh << 'EOF'
#!/bin/bash
while true; do
    response=$(curl -s -w "\n%{http_code}" http://localhost:5000/health)
    status=$(echo "$response" | tail -n 1)
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    if [ "$status" = "200" ]; then
        echo "[$timestamp] ✓ 服务正常"
    else
        echo "[$timestamp] ✗ 服务异常 (HTTP $status)"
        # 发送告警
    fi
    
    sleep 60
done
EOF

chmod +x monitor.sh
./monitor.sh
```

### 备份策略

#### 1. 模型文件备份

```bash
# 创建备份脚本
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backup/hiv_model"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份模型文件
tar -czf $BACKUP_DIR/models_$DATE.tar.gz saved_models/

# 保留最近30天的备份
find $BACKUP_DIR -name "models_*.tar.gz" -mtime +30 -delete

echo "备份完成: $BACKUP_DIR/models_$DATE.tar.gz"
EOF

chmod +x backup.sh

# 添加到crontab（每天凌晨2点备份）
crontab -e
# 添加：0 2 * * * /path/to/backup.sh
```

#### 2. 数据库备份（如果使用）

```bash
# 备份预测日志等数据
# 根据实际使用的数据库类型调整
```

---

## 故障排查

### 常见问题

#### 1. 模型加载失败

**症状**: API启动时报错 "模型加载失败"

**解决方案**:
```bash
# 检查模型文件是否存在
ls -lh saved_models/final_model_3to5.pkl

# 检查文件权限
chmod 644 saved_models/final_model_3to5.pkl

# 测试模型加载
python3 -c "import joblib; joblib.load('saved_models/final_model_3to5.pkl')"
```

#### 2. 端口被占用

**症状**: "Address already in use"

**解决方案**:
```bash
# 查找占用端口的进程
lsof -i :5000

# 或
netstat -tulpn | grep :5000

# 杀死进程
kill -9 <PID>

# 或使用其他端口
PORT=5001 python3 api/app.py
```

#### 3. 内存不足

**症状**: 服务崩溃，日志显示 "MemoryError"

**解决方案**:
```bash
# 检查内存使用
free -h

# 减少Gunicorn worker数量
# 修改gunicorn_config.py: workers = 2

# 或增加系统内存
```

#### 4. 响应时间过长

**症状**: API响应超过30秒

**解决方案**:
```bash
# 检查是否使用了增强模型
# 如果不需要，可以禁用
export USE_ENHANCED_MODEL=false

# 优化批量预测
# 减小batch_size

# 增加worker数量
# 修改gunicorn_config.py: workers = 8
```

### 日志分析

```bash
# 查看错误日志
grep ERROR logs/api.log | tail -n 50

# 统计请求数
grep "POST /v1/predict" logs/gunicorn_access.log | wc -l

# 分析响应时间
awk '{print $NF}' logs/gunicorn_access.log | sort -n | tail -n 10
```

### 健康检查

```bash
# 创建健康检查脚本
cat > healthcheck.sh << 'EOF'
#!/bin/bash

# 检查服务是否运行
if ! pgrep -f "python3 api/app.py" > /dev/null; then
    echo "✗ 服务未运行"
    exit 1
fi

# 检查API响应
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/health)
if [ "$response" != "200" ]; then
    echo "✗ API响应异常 (HTTP $response)"
    exit 1
fi

echo "✓ 服务正常"
exit 0
EOF

chmod +x healthcheck.sh
./healthcheck.sh
```

---

## 安全建议

### 1. 网络安全

```bash
# 配置防火墙
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# 限制API访问（仅允许特定IP）
# 在Nginx配置中添加：
# allow 192.168.1.0/24;
# deny all;
```

### 2. API认证（可选）

```python
# 在api/app.py中添加认证中间件
from functools import wraps
from flask import request, jsonify

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key != os.environ.get('API_KEY'):
            return jsonify({'error': '未授权'}), 401
        return f(*args, **kwargs)
    return decorated_function

# 使用
@app.route('/v1/predict', methods=['POST'])
@require_api_key
def predict_single():
    ...
```

### 3. 速率限制

```bash
# 安装Flask-Limiter
pip install Flask-Limiter

# 在api/app.py中配置
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)
```

---

## 性能优化

### 1. 模型预加载

```python
# 在Gunicorn配置中启用preload
preload_app = True
```

### 2. 连接池优化

```python
# 如果使用数据库，配置连接池
# SQLAlchemy示例：
engine = create_engine(
    'postgresql://...',
    pool_size=10,
    max_overflow=20
)
```

### 3. 缓存策略

```python
# 使用Redis缓存预测结果
import redis
import hashlib
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_cached_prediction(features):
    # 生成缓存key
    key = hashlib.md5(json.dumps(features, sort_keys=True).encode()).hexdigest()
    
    # 尝试从缓存获取
    cached = redis_client.get(key)
    if cached:
        return json.loads(cached)
    
    # 预测
    result = predictor.predict_single(features)
    
    # 缓存结果（1小时）
    redis_client.setex(key, 3600, json.dumps(result))
    
    return result
```

---

## 更新和升级

### 更新模型

```bash
# 1. 备份当前模型
cp saved_models/final_model_3to5.pkl saved_models/final_model_3to5_backup.pkl

# 2. 上传新模型
# 将新模型文件复制到saved_models/

# 3. 重启服务
sudo systemctl restart hiv-api

# 4. 验证
curl http://localhost:5000/v1/model/info
```

### 更新代码

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 更新依赖
pip install -r requirements.txt --upgrade

# 3. 重启服务
sudo systemctl restart hiv-api
```

---

## 附录

### A. 完整的systemd服务文件

```ini
[Unit]
Description=HIV Risk Assessment API Service
After=network.target

[Service]
Type=simple
User=hivapi
Group=hivapi
WorkingDirectory=/opt/hiv_project/hiv_risk_model
Environment="PATH=/opt/conda/envs/hivenv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="USE_ENHANCED_MODEL=true"
Environment="PORT=5000"
Environment="HOST=0.0.0.0"
Environment="DEBUG=false"
ExecStart=/opt/conda/envs/hivenv/bin/gunicorn -c gunicorn_config.py api.app:app
Restart=always
RestartSec=10
StandardOutput=append:/var/log/hiv-api/stdout.log
StandardError=append:/var/log/hiv-api/stderr.log

[Install]
WantedBy=multi-user.target
```

### B. 完整的Nginx配置

```nginx
upstream hiv_api {
    least_conn;
    server 127.0.0.1:5000 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name api.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.example.com;

    # SSL证书
    ssl_certificate /etc/letsencrypt/live/api.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # 日志
    access_log /var/log/nginx/hiv-api-access.log;
    error_log /var/log/nginx/hiv-api-error.log;

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # 请求限制
    client_max_body_size 10M;
    client_body_timeout 30s;
    client_header_timeout 30s;

    location / {
        proxy_pass http://hiv_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    location /health {
        proxy_pass http://hiv_api/health;
        access_log off;
    }
}
```

---

**文档版本**: 1.0.0  
**最后更新**: 2025-11-04  
**适用系统**: Linux, macOS  
**适用模型版本**: v1.1.0
