FROM nginx:alpine

# 前端静态资源（需要本机先 npm run build 生成 dist 目录）
COPY dist /usr/share/nginx/html

# 两套 nginx 配置（entrypoint.sh 会选择一份启用）
COPY nginx.http.conf  /etc/nginx/conf.d/nginx.http.conf
COPY nginx.https.conf /etc/nginx/conf.d/nginx.https.conf

# 入口脚本：自动判断证书是否存在，选择 HTTP 或 HTTPS 模式
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 80 443

ENTRYPOINT ["/entrypoint.sh"]
