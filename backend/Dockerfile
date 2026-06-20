FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖（mysql-connector-python 需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# 先复制依赖文件，利用 Docker 缓存层
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制后端代码
COPY . .

# 创建上传目录
RUN mkdir -p uploads
# 创建空 .env 文件以避免 pydantic-settings 找不到 env_file 报错
# （实际配置通过 docker-compose 环境变量注入）
RUN touch /.env

EXPOSE 8000

# 生产模式：uvicorn 多 worker（根据 CPU 核心数动态计算）
# workers = CPU × 2 + 1 是常见配置
CMD ["sh", "-c", "WORKERS=$(python -c \"import os; n=os.cpu_count() or 2; print(max(2, min(n * 2, 8)))\") && uvicorn main:app --host 0.0.0.0 --port 8000 --workers $WORKERS"]
