# 使用 Python 3.11 作为基础镜像
FROM python:3.11-slim

# 安装依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 设置默认源（国内源）
ARG USE_CN_SOURCE=true

# 根据环境变量选择是否使用国内源
RUN if [ "$USE_CN_SOURCE" = "true" ]; then \
        pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple; \
    else \
        pip config set global.index-url https://pypi.org/simple; \
    fi

# 设置工作目录
WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 拷贝后端代码
COPY . .

# 默认端口
EXPOSE 10085

# 启动 FastAPI
CMD ["python", "server.py"]
