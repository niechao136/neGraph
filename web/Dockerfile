# frontend/Dockerfile
FROM node:20-alpine AS build

WORKDIR /app

# 复制 package.json 和锁文件
COPY package*.json ./

# 安装依赖
RUN npm install

# 复制前端源代码（忽略 node_modules）
COPY . .

# 构建生产版本
RUN npm run build

# Nginx 提供静态文件
FROM nginx:alpine

# 删除默认 nginx 网站
RUN rm -rf /usr/share/nginx/html/*

# 复制打包后的前端静态文件
COPY --from=build /app/dist /usr/share/nginx/html

# 复制 nginx 配置
COPY nginx/nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
