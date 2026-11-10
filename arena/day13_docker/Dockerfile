# 第 13 天配套文件：Bittensor 矿工与监控服务容器镜像 Dockerfile（v6）
FROM python:3.12-slim

WORKDIR /app

# 1. 先复制依赖清单以利用 Docker 缓存层
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# 2. 复制应用代码（注意：.dockerignore 已排除 .env 与所有钱包密钥文件）
COPY tools/ /app/tools/
COPY arena/ /app/arena/

ENV PYTHONUNBUFFERED=1

EXPOSE 8091

# 默认启动共学营矿工服务
CMD ["python", "arena/day09_10_miner/camp_miner.py", "--port", "8091"]
