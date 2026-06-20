#!/bin/sh
# ======================================================================
# Nginx 入口脚本（极简版）
# - 证书存在：用 nginx.https.conf（80 跳转 + 443 HTTPS）
# - 证书不存在：用 nginx.http.conf（只有 80 HTTP，供首次部署用）
# ======================================================================

set -e

HTTP_CONF="/etc/nginx/conf.d/nginx.http.conf"
HTTPS_CONF="/etc/nginx/conf.d/nginx.https.conf"
TARGET_CONF="/etc/nginx/conf.d/default.conf"

CERT_FILE="/etc/letsencrypt/live/momo.makeup/fullchain.pem"
KEY_FILE="/etc/letsencrypt/live/momo.makeup/privkey.pem"

echo "[entrypoint] 检查证书..."
echo "  → $CERT_FILE"
echo "  → $KEY_FILE"

if [ -f "$CERT_FILE" ] && [ -f "$KEY_FILE" ]; then
    echo "[entrypoint] ✅ 证书已存在，启用 HTTPS 模式"
    cp "$HTTPS_CONF" "$TARGET_CONF"
else
    echo "[entrypoint] ℹ️  证书不存在，使用 HTTP 模式（首次部署）"
    echo "[entrypoint]    服务启动后请执行："
    echo "[entrypoint]    docker compose run --rm certbot certonly --webroot -w /var/www/certbot -d momo.makeup -d www.momo.makeup --email YOUR_EMAIL --agree-tos --no-eff-email"
    echo "[entrypoint]    然后：docker compose restart frontend"
    cp "$HTTP_CONF" "$TARGET_CONF"
fi

echo "[entrypoint] 启动 nginx..."
exec nginx -g 'daemon off;'
