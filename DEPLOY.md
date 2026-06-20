# 🚀 服务器部署指南

> **你需要**：一台 Linux 云服务器（CentOS / Ubuntu）+ 你手上的 Windows 电脑。
> 下面所有命令都标注了在哪台机器上执行。

---

## 一、在服务器上安装 Docker（仅第一次）

用 SSH 工具（XShell / FinalShell / PowerShell SSH）连上你的服务器，然后执行：

### 1. 安装 Docker

```bash
# ⚠️ 以下命令在服务器（Linux）上执行，不是在 Windows 上！

# 一键安装（阿里云镜像，国内速度快）
curl -fsSL https://get.docker.com | bash -s docker --mirror Aliyun

# 启动 Docker 并设置开机自启
systemctl enable docker && systemctl start docker

# 验证
docker --version
```

### 2. 安装 Docker Compose

```bash
# ⚠️ 同样在服务器上执行
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

chmod +x /usr/local/bin/docker-compose

# 验证
docker-compose --version
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

# 上传到服务器（替换成你的服务器 IP）
scp note-app.tar.gz root@你的服务器IP:/root/
```

**方式 B：用 XShell / FinalShell 的 SFTP 直接拖拽上传**（图形界面，更直观）

### 在服务器上解压

SSH 连上服务器：

```bash
# ⚠️ 在服务器上执行
cd /root
tar -xzf note-app.tar.gz
cd note-takingAssistant   # 解压后进入项目目录
ls                         # 应该能看到 docker-compose.yml
```

---

## 三、修改配置

在服务器上：

```bash
# ⚠️ 在服务器上执行
cd /root/note-takingAssistant
vim .env    # 或用 nano .env
```

**务必修改这两个值**：

```ini
DB_PASSWORD=你的安全密码（大小写+数字+特殊字符，如 MyN0te!2024）
SECRET_KEY=一个很长的随机字符串（至少 32 个字符，乱敲键盘即可）
```

> 💡 如果你不熟悉 vim：按 `i` 进入编辑模式，改完后按 `Esc` 再输入 `:wq` 保存退出。
> 或者用 `nano .env` 更简单，`Ctrl+X` 然后 `Y` 保存。

---

## 四、一键启动

在服务器上：

```bash
# ⚠️ 在服务器上执行
cd /root/note-takingAssistant
docker-compose up -d
```

首次启动会自动下载镜像、构建项目，大约需要 **3-5 分钟**。

看到以下输出就成功了：

```
✔ Container note-redis    Started
✔ Container note-mysql    Started
✔ Container note-backend  Started
✔ Container note-frontend Started
```

验证一下：

```bash
docker-compose ps                    # 确认 4 个服务都在 running
curl http://localhost/api/             # 测试后端 API，应返回 JSON
```

---

## 五、访问应用

打开**浏览器**访问：

```
http://你的服务器IP
```

> ⚠️ 如果访问不了，检查服务器**防火墙/安全组**是否放行了 **80 端口**。
> - 阿里云/腾讯云：去控制台 → 安全组 → 入方向 → 添加 TCP 80
> - 服务器防火墙：`firewall-cmd --add-port=80/tcp --permanent && firewall-cmd --reload`

---

## 六、代码更新后重新部署

在 Windows 本地上打包，上传新文件到服务器后：

```bash
# ⚠️ 在服务器上执行
cd /root/note-takingAssistant
docker-compose down
tar -xzf note-app.tar.gz              # 覆盖旧文件
docker-compose up -d --build          # 重新构建并启动
```

---

## 七、常用运维命令

```bash
# 查看所有容器状态
docker-compose ps

# 查看实时日志
docker-compose logs -f backend        # 后端日志
docker-compose logs -f frontend       # 前端日志

# 重启某个服务
docker-compose restart backend

# 停止所有服务
docker-compose down

# 备份数据库
docker exec note-mysql mysqldump -u root -p note_db > backup.sql

# 恢复数据库
docker exec -i note-mysql mysql -u root -p note_db < backup.sql
```

---

## 八、常见问题

### Q1: 端口被占用
修改 `docker-compose.yml`，把 `"80:80"` 改成 `"8080:80"`，然后访问 `http://IP:8080`。

### Q2: 数据库连接失败
`.env` 里的 `DB_PASSWORD` 改了之后，需要**删掉旧数据库卷**重建：
```bash
docker-compose down -v   # ⚠️ -v 会删掉数据库数据，谨慎使用
docker-compose up -d
```

### Q3: 想绑域名 + HTTPS
在服务器上安装 Nginx，加一层反向代理后用 Let's Encrypt 申请免费 SSL 证书。

### Q4: AI 功能？
用户登录后在**个人中心**自己填 API Key（兼容 OpenAI 协议），不需要服务器上跑模型。

### Q5: 服务器是 Windows Server 怎么办？
Docker Desktop for Windows 可以用，但建议装个 WSL2 或者直接用 Linux 服务器 — 生态好得多。

---

## 一键部署流程图

```
Windows 本地                        Linux 服务器
─────────────                      ─────────────
tar 打包项目                        安装 Docker + Compose
    │                                   │
    └── scp 上传 ──────────────────────→ 解压
                                        │
                                    修改 .env（密码）
                                        │
                                    docker-compose up -d
                                        │
                                    ✅ 访问 http://IP
```
