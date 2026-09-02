# 🚀 服务器部署指南（v1.1.0）

> **你需要**：一台 Linux 云服务器（CentOS / Ubuntu）+ 你手上的 Windows 电脑。
> 下面所有命令都标注了在哪台机器上执行。
>
> **本指南适用于 v1.1.0+**，使用 Docker Compose V2（`docker compose` 命令）。
>
> 📌 部署完成后的**运行期运维**（监控 / 告警 / 日志 / 多实例 / 备份）见 [docs/PRODUCTION_OPS.md](docs/PRODUCTION_OPS.md)。

---

## 一、在服务器上安装 Docker（仅第一次）

用 SSH 工具（XShell / FinalShell / PowerShell SSH）连上你的服务器，然后执行：

### 1. 安装 Docker（含 Compose V2）

```bash
# ⚠️ 以下命令在服务器（Linux）上执行

# 一键安装 Docker（包含 docker compose 子命令）
curl -fsSL https://get.docker.com | bash -s docker --mirror Aliyun

# 启动 Docker 并设置开机自启
systemctl enable docker && systemctl start docker

# 验证（新版 docker compose 是 docker 的子命令，无需单独装 docker-compose）
docker --version
docker compose version
```

### 2. 如服务器已有旧版 docker-compose

```bash
# 确认是 V2 版（docker compose）还是 V1 版（docker-compose）
docker compose version   # ← 推荐用这个（V2）
docker-compose --version # ← 旧版，如果存在请用新版替代
```

---

## 二、上传项目到服务器

### 在 Windows 本地上操作

**方式 A：用 PowerShell 打包上传（推荐）**

```powershell
# ⚠️ 在 Windows PowerShell 中执行（不在服务器上）
# 进入项目所在目录
cd C:\Users\MOM\Desktop\bishe\note-takingAssistant\note-takingAssistant

# 打包（排除 node_modules、.venv 等不需要的文件）
tar -czf note-app.tar.gz --exclude=node_modules --exclude=.venv --exclude=__pycache__ --exclude=.git --exclude=dist --exclude=build .

# 上传到服务器（替换成你的服务器 IP 和用户名）
scp note-app.tar.gz root@你的服务器IP:/root/
```

**方式 B：用 XShell / FinalShell 的 SFTP 直接拖拽上传**（图形界面，更直观）

### 在服务器上解压

```bash
# ⚠️ 在服务器上执行
cd /root
tar -xzf note-app.tar.gz
cd note-takingAssistant
ls
# 应该能看到 docker-compose.yml
```

---

## 三、构建前端静态资源

**⚠️ 必须先构建前端**：前端代码需要打包后才能放入 Docker 镜像。

如果上传前未构建，需要在服务器上构建（Node.js ≥ 18）：

```bash
# ⚠️ 在服务器上执行
cd /root/note-takingAssistant/frontend

# 如果服务器没装 Node.js，先安装：
# curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
# apt-get install -y nodejs

npm install
npm run build
cd ..
```

> 💡 **建议在本机构建后再上传**：在本机 `frontend` 目录运行 `npm run build`，将生成的 `dist` 文件夹一起打包上传，服务器上就无需安装 Node.js。

---

## 四、修改配置并生成随机密钥

```bash
# ⚠️ 在服务器上执行
cd /root/note-takingAssistant

# 复制环境变量模板
cp .env.docker .env

# 生成随机密钥（任选一个方式）
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
# 或
openssl rand -base64 48

# 编辑 .env（必须修改以下 3 个值）
nano .env
```

**必须修改的值**（⚠️ 不要用默认值）：

```ini
DB_PASSWORD=一个很长的随机字符串（建议 48 字符）
REDIS_PASSWORD=另一个很长的随机字符串（建议 48 字符）
SECRET_KEY=JWT 签名密钥，至少 32 字符
```

> 💡 不熟悉 vim/nano？按 `i` 进入编辑模式，改完后按 `Esc` 再输入 `:wq` 保存退出。

---

## 五、一键启动

```bash
# ⚠️ 在服务器上执行
cd /root/note-takingAssistant
docker compose up -d --build
```

首次启动会自动下载镜像、构建项目，大约需要 **3-5 分钟**。

查看状态：

```bash
docker compose ps
# 应看到 5 个服务：mysql / redis / backend / frontend / certbot
# 全部应为 Up（或 Up (healthy)）
```

查看日志：

```bash
docker compose logs -f backend   # 后端日志
docker compose logs -f frontend  # 前端日志
```

---

## 六、申请免费 HTTPS 证书（Let's Encrypt）

**⚠️ 先确认 DNS 已生效**：

```bash
# 在服务器上测试域名是否解析正确
ping momo.makeup
# 应显示你的服务器 IP
```

**申请证书**（将 `your@email.com` 换成你的真实邮箱）：

```bash
docker compose run --rm certbot certonly --webroot \
    -w /var/www/certbot \
    -d momo.makeup -d www.momo.makeup \
    --email your@email.com --agree-tos --no-eff-email
```

✅ 成功后会显示：`Congratulations! Your certificate and chain have been saved at: /etc/letsencrypt/...`

**重启前端容器，启用 HTTPS**：

```bash
docker compose restart frontend
```

---

## 七、验证部署

```bash
# 浏览器访问
https://momo.makeup
# 应显示 🔒 锁图标

# API 测试
curl https://momo.makeup/api/v1/public/stats
# 应返回 JSON
```

---

## 八、代码更新后重新部署

```bash
# ⚠️ 在服务器上执行
cd /root/note-takingAssistant

# 拉取新代码或解压新包
docker compose down
tar -xzf note-app.tar.gz
docker compose up -d --build
```

---

## 九、常用运维命令

```bash
# 查看所有容器状态
docker compose ps

# 查看实时日志
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f certbot

# 重启某个服务
docker compose restart backend

# 停止所有服务（保留数据卷）
docker compose down

# 停止并删除数据卷（⚠️ 会清空数据库，谨慎！）
docker compose down -v

# 手动续期证书（一般由容器自动处理）
docker compose run --rm certbot certbot renew

# 查看证书状态
docker compose exec certbot certbot certificates

# 备份数据库
docker exec note-mysql mysqldump -u root -p note_db > backup_$(date +%Y%m%d).sql

# 恢复数据库
docker exec -i note-mysql mysql -u root -p note_db < backup_20260620.sql
```

---

## 十、常见问题

### Q1：端口被占用
修改 `docker-compose.yml`，把 `"80:80"` 改成 `"8080:80"`，然后访问 `http://IP:8080`。

### Q2：数据库连接失败
`.env` 里的 `DB_PASSWORD` 改了之后，需要**删掉旧数据库卷**重建：
```bash
docker compose down -v   # ⚠️ -v 会删掉数据库数据，谨慎使用
docker compose up -d
```

### Q3：证书申请失败（Timeout during connect）
- DNS 还没生效 → 等 2-10 分钟后再试
- 服务器 80 端口被防火墙挡住 → `ufw allow 80; ufw allow 443`
- 阿里云/腾讯云安全组 → 入方向添加 TCP 80 和 443

### Q4：前端启动后 nginx 报 502
检查后端是否正常：`docker compose logs backend`
后端健康检查通过后再试：`curl http://localhost:8000/docs`

### Q5：AI 功能？
用户登录后在**个人中心**自己填 API Key（兼容 OpenAI 协议），不需要服务器上跑模型。

### Q6：服务器是 Windows Server 怎么办？
Docker Desktop for Windows 可以用，但建议装 WSL2 或直接用 Linux 服务器。

---

## 一键部署流程图

```
Windows 本地                        Linux 服务器
─────────────                      ─────────────
npm run build（构建前端）              安装 Docker
    │                                   │
    └── tar 打包 ──────────────────────→ 解压
                                        │
                                    生成随机密钥（3个）
                                        │
                                    docker compose up -d
                                        │
                                    申请 Let's Encrypt 证书
                                        │
                                    docker compose restart frontend
                                        │
                                    ✅ https://momo.makeup
```
