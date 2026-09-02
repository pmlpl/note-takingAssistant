# 🔧 生产运维方案（v1.1.0）

> 面向部署在 Linux 云服务器上的 NoteMind（Docker Compose 部署），覆盖**监控 / 告警 / 日志 / 多实例 / 备份 / 巡检**六个方面。
> 配套部署步骤见 [DEPLOY.md](../DEPLOY.md)。本文所有命令默认在服务器上执行。

---

## 一、监控（怎么知道系统活着）

### 1.1 现有基础

| 组件 | 已有能力 |
|------|---------|
| MySQL | Docker `healthcheck`（`mysqladmin ping`，10s 间隔） |
| Redis | Docker `healthcheck`（`redis-cli ping`，10s 间隔） |
| 后端 | uvicorn 多 worker + Docker healthcheck |
| 前端 Nginx | 80/443 反代后端 |

```bash
# 手动探活（任何一台机器都能跑）
curl -fsS https://momo.makeup/api/v1/public/stats -o /dev/null && echo "API OK"
curl -fsS https://momo.makeup/ && echo "Web OK"

# 服务器上查看容器健康状态
docker compose ps
# 期望：全部 Up (healthy)
```

### 1.2 推荐：Uptime Kuma（自托管监控，5 分钟部署）

```bash
# docker run 单容器启动，dashboard 端口 3001（记得开安全组/防火墙）
docker run -d --name uptime-kuma --restart=always \
  -p 3001:3001 \
  -v uptime_kuma_data:/app/data \
  louislam/uptime-kuma:1
```

在 Kuma 里添加监控项：

| 监控项 | 类型 | URL |
|--------|------|-----|
| 网站 | HTTP(S) | `https://momo.makeup` |
| API 健康 | HTTP(S) | `https://momo.makeup/api/v1/public/stats` |
| 证书到期 | Certificate | `momo.makeup:443` |
| TCP 端口 | Port | `服务器IP:443` |

### 1.3 进阶：Prometheus + Grafana（可选，指标级监控）

当前为单体 Compose，指标级监控按需启用（`docker-compose.override.yml` 追加即可，不污染主文件）：

```yaml
# docker-compose.override.yml（可选，不提交生产必用）
services:
  node-exporter:
    image: prom/node-exporter:latest
    container_name: note-node-exporter
    restart: always
    network_mode: host
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    container_name: note-cadvisor
    restart: always
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
    privileged: true
  prometheus:
    image: prom/prometheus:latest
    container_name: note-prometheus
    restart: always
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
  grafana:
    image: grafana/grafana:latest
    container_name: note-grafana
    restart: always
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: "换一个强密码"
```

> 单机轻量场景，**先做 Uptime Kuma（1.2）即可**；Prometheus/Grafana 是流量上来后的升级项。

---

## 二、告警（出了问题怎么第一时间知道）

### 2.1 Uptime Kuma 通知渠道（任选）

在 Kuma 的**通知设置**里添加，多选可同时推多个渠道：

- **邮件**：SMTP（阿里云/腾讯云邮箱或 SMTP 服务）
- **Server酱 / PushPlus**：微信推送，注册拿 key 填进去即可
- **钉钉 / 企业微信机器人**：webhook 填到 Kuma
- **Telegram Bot**：海外可用

### 2.2 建议的告警规则

| 触发条件 | 建议阈值 | 备注 |
|----------|---------|------|
| 网站/API 挂 | 连续 2 次失败，10 分钟重试 | Kuma 自带 |
| 证书剩余天数 | < 14 天 | certbot 自动续期失败时兜底提醒 |
| 磁盘空间 | < 20% | 日志/数据库增长最易吃满磁盘 |
| 数据库备份失败 | 备份 cron 中 `&&` 链失败即发邮件 | 见第五节 |

### 2.3 磁盘告警（cron 检查）

```bash
# /etc/cron.d/disk-alert
*/30 * * * * root df -h / | awk 'NR==2 && $5+0 >= 80 { echo "磁盘使用率 $5" | mail -s "磁盘告警" your@email.com }'
```

---

## 三、日志（怎么查、怎么留、怎么不写爆磁盘）

### 3.1 实时查看

```bash
docker compose logs -f backend    # 后端
docker compose logs -f frontend   # 前端/Nginx
docker compose logs -f certbot    # 证书续期
docker compose logs -f mysql      # 数据库
```

### 3.2 【必须做】日志轮转，防止写爆磁盘

Docker 默认 json-file 无上限，生产必须加轮转。编辑 `/etc/docker/daemon.json`：

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "50m",
    "max-file": "5"
  }
}
```

```bash
systemctl restart docker    # 改完重启生效（会重启所有容器，安排低峰期）
```

已存在的旧容器需重建才生效：`docker compose up -d --force-recreate`。

### 3.3 集中日志（可选，多实例时推荐）

单机：3.2 轮转 + `docker compose logs > note_$(date +%F).log` 定期归档即可。
多机/多实例后：上 **Loki + Promtail**（比 ELK 轻一个量级），Grafana 里统一检索 `{container="note-backend"}`。

---

## 四、多实例 / 水平扩展

### 4.1 现状：单机多 worker（已就绪）

`backend/Dockerfile` 已配置 uvicorn 多 worker：

```bash
# workers = CPU×2+1，上限 8
CMD ["sh", "-c", "WORKERS=$(python -c \"...\") && uvicorn main:app --host 0.0.0.0 --port 8000 --workers $WORKERS"]
```

后端**无状态**（认证走 JWT，会话/黑名单/限流走共享 Redis，数据走 MySQL），天然支持横向扩展。

### 4.2 方案 A：同一台机器扩副本（简单）

```bash
docker compose up -d --scale backend=2
# Nginx 已反代 backend 服务名，会自动在两个副本间轮询
```

### 4.3 方案 B：多台机器（集群）

```
                     ┌── backend-1 (服务器A) ──┐
外部 → Nginx(负载均衡) ── backend-2 (服务器B) ──┼── MySQL + Redis（单独/托管）
                     └── backend-N (服务器C) ──┘
```

要点：
- **MySQL / Redis 必须独立**（或用托管云数据库），否则多实例共享不了数据与限流状态；
- Nginx `upstream` 配多个 backend 地址做负载均衡；
- 后端 `API_BASE_URL` / `FRONTEND_URL` / `SECRET_KEY` 必须各实例一致（JWT 验签需要同一密钥）；
- Redis 用于限流计数与 token 黑名单，多实例下必须指向**同一个** Redis。

### 4.4 扩展前检查清单

- [ ] Redis 已独立/托管，多实例共享
- [ ] MySQL 连接池参数（`pool_size`）按实例数调整
- [ ] `SECRET_KEY` 多实例统一
- [ ] 上传文件目录（uploads）考虑共享存储（NFS/对象存储）——多实例时本地盘各自独立

---

## 五、备份与恢复（数据是命根子）

### 5.1 MySQL 定时备份（建议每天）

```bash
# /etc/cron.d/note-backup
0 3 * * * root bash /root/note-takingAssistant/scripts/backup.sh
```

`scripts/backup.sh`（项目内已有备份思路，脚本内容示例）：

```bash
#!/usr/bin/env bash
set -euo pipefail
STAMP=$(date +%Y%m%d_%H%M%S)
DIR=/root/backups
mkdir -p "$DIR"
# 备份（-p 后直接跟密码，注意 .env 与这里保持一致）
docker exec note-mysql mysqldump -u root -p"$DB_PASSWORD" note_db | gzip > "$DIR/note_db_$STAMP.sql.gz"
# 保留最近 14 天
find "$DIR" -name 'note_db_*.sql.gz' -mtime +14 -delete
# 可选：上传到对象存储/另一台机器做异地备份
```

> 用 `crontab` 而非 compose 内置，可配合 2.3 的磁盘/失败告警。

### 5.2 恢复

```bash
gunzip -c /root/backups/note_db_YYYYMMDD_HHMMSS.sql.gz | docker exec -i note-mysql mysql -u root -p"$DB_PASSWORD" note_db
```

### 5.3 Redis

Redis 数据是缓存（限流计数/验证码/黑名单），丢了会自动重建，一般无需备份；`redis_data` 卷已持久化。

---

## 六、日常巡检清单（每周/每月）

```bash
# 1. 容器健康
docker compose ps

# 2. 磁盘（重点看 /var/lib/docker）
df -h

# 3. 日志有无 ERROR（数量统计）
docker compose logs --since 24h backend | grep -c "ERROR" || true

# 4. 证书剩余天数
docker compose exec certbot certbot certificates

# 5. 依赖漏洞（CI 已带 informational 检查，发布前人工确认）
#    前端: cd frontend && npm audit；后端: pip-audit -r backend/requirements.txt

# 6. 依赖安全基线
#    backend: pip check；前端: npm audit --audit-level=high
```

**上线前一次性动作**：
1. `/etc/docker/daemon.json` 配日志轮转（3.2）；
2. 起 Uptime Kuma 并配好通知渠道（1.2 + 二）；
3. 配置 MySQL 每日备份 cron（5.1）；
4. 确认 `.env` 中 `SECRET_KEY` / `DB_PASSWORD` / `REDIS_PASSWORD` 为随机强密码（非默认值）。

---

## 七、与现有文档的关系

- 部署步骤（装 Docker、传代码、起服务、申请证书）→ [DEPLOY.md](../DEPLOY.md)
- 本文件解决的是 **部署完成之后** 的运行期问题（看着它、出事了知道、坏了能查、不够用了能扩）。
