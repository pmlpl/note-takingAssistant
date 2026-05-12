# AI个人智能笔记助手 📝

一个基于 **Vue 3 + FastAPI + Ollama** 的全栈智能笔记应用，提供AI辅助的笔记生成、总结和管理功能。

![Vue](https://img.shields.io/badge/Vue-3.3-brightgreen)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-blue)
![Python](https://img.shields.io/badge/Python-3.10+-yellow)
![License](https://img.shields.io/badge/License-MIT-orange)

## ✨ 核心功能

### 📝 笔记管理
- ✅ 富文本编辑器支持
- ✅ 笔记分类与标签
- ✅ 搜索与筛选
- ✅ 收藏功能
- ✅ 历史记录追踪
- ✅ 导入 Word/TXT 文档

### 🤖 AI 智能助手
- ✅ AI 自动生成笔记（多格式输出）
- ✅ 智能总结笔记内容
- ✅ AI 对话交互
- ✅ 流式输出显示
- ✅ 上下文理解（支持上传笔记作为参考）
- ✅ /note 命令快速调用

### 📊 数据可视化
- ✅ 笔记统计图表（ECharts）
- ✅ 最近笔记动态展示
- ✅ 学习趋势分析

### 🔐 用户系统
- ✅ JWT 身份认证
- ✅ 用户注册/登录
- ✅ 个人中心管理

### 💾 缓存优化
- ✅ Redis 高性能缓存
- ✅ 持久化缓存策略
- ✅ 自动同步机制

## 🏗️ 技术架构

### 前端技术栈
- **框架**: Vue 3 (Composition API)
- **路由**: Vue Router 4
- **状态管理**: Pinia
- **UI组件**: Element Plus
- **富文本**: WangEditor
- **HTTP客户端**: Axios
- **Markdown**: Marked
- **Word解析**: Mammoth
- **图表**: ECharts
- **构建工具**: Vite 5

### 后端技术栈
- **框架**: FastAPI
- **数据库**: MySQL + SQLAlchemy ORM
- **缓存**: Redis
- **AI模型**: Ollama (本地部署)
- **认证**: JWT (python-jose)
- **密码加密**: Bcrypt
- **文档处理**: python-docx
- **异步服务器**: Uvicorn

## 📁 项目结构

```
note-takingAssistant/
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── api/v1/         # API路由层
│   │   │   ├── user.py     # 用户接口
│   │   │   ├── note.py     # 笔记接口
│   │   │   └── ai.py       # AI接口
│   │   ├── core/           # 核心配置
│   │   │   ├── config.py   # 环境变量配置
│   │   │   ├── database.py # 数据库连接
│   │   │   ├── redis_client.py # Redis客户端
│   │   │   └── security.py # 安全工具
│   │   ├── crud/           # 数据操作层
│   │   ├── models/         # 数据模型
│   │   ├── services/       # 业务逻辑层
│   │   │   ├── prompts.py          # AI提示词
│   │   │   ├── note_generator.py   # 笔记生成
│   │   │   ├── note_analyzer.py    # 笔记分析
│   │   │   └── chat_service.py     # 聊天服务
│   │   └── utils/          # 工具函数
│   ├── uploads/            # 文件上传目录
│   ├── .env                # 环境配置（不提交）
│   ├── .env.example        # 配置模板
│   ├── requirements.txt    # Python依赖
│   └── main.py             # 入口文件
│
├── frontend/               # 前端应用
│   ├── src/
│   │   ├── api/           # API接口封装
│   │   ├── assets/        # 静态资源
│   │   ├── components/    # 公共组件
│   │   │   ├── icons/     # SVG图标
│   │   │   ├── Layout.vue # 布局组件
│   │   │   └── RichText.vue # 富文本编辑器
│   │   ├── composables/   # 组合式函数
│   │   │   ├── useNoteManager.js  # 笔记管理
│   │   │   └── useAIAssistant.js  # AI助手
│   │   ├── config/        # 配置文件
│   │   ├── router/        # 路由配置
│   │   ├── store/         # Pinia状态管理
│   │   ├── utils/         # 工具函数
│   │   ├── views/         # 页面视图
│   │   │   ├── auth/      # 认证页面
│   │   │   ├── notes/     # 笔记页面
│   │   │   └── ai/        # AI功能页面
│   │   ├── App.vue        # 根组件
│   │   └── main.js        # 入口文件
│   ├── .env               # 环境配置（不提交）
│   ├── .env.example       # 配置模板
│   └── package.json       # Node依赖
│
└── docs/                  # 项目文档
    ├── ENVIRONMENT_CONFIG.md          # 环境配置指南
    ├── PROJECT_OPTIMIZATION_SUMMARY.md # 项目优化总结
    └── ...                            # 其他功能文档
```

## 🚀 快速开始

### 前置要求

- **Node.js** >= 16.x
- **Python** >= 3.10
- **MySQL** >= 8.0
- **Redis** >= 6.0
- **Ollama** (本地AI模型)

### 1️⃣ 安装 Ollama

```bash
# 访问 https://ollama.ai 下载安装

# 拉取 AI 模型
ollama pull qwen:7b

# 启动 Ollama 服务
ollama serve
```

### 2️⃣ 配置后端

```bash
cd backend

# 创建虚拟环境（推荐）
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置数据库密码等配置
```

编辑 `backend/.env`：
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=你的数据库密码
DB_NAME=ai_note_db

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

SECRET_KEY=your-secret-key-change-in-production
OLLAMA_MODEL=qwen:7b
```

创建数据库：
```sql
CREATE DATABASE ai_note_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

启动后端服务：
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

访问 API 文档：http://localhost:8000/docs

### 3️⃣ 配置前端

```bash
cd frontend

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件
```

编辑 `frontend/.env`：
```env
VITE_API_BASE_URL=http://localhost:8000
```

启动开发服务器：
```bash
npm run dev
```

访问前端应用：http://localhost:5173

## 📖 使用指南

### 基本流程

1. **注册/登录** - 创建账户并登录
2. **创建笔记** - 手动编写或使用 AI 生成
3. **AI 辅助** - 使用 AI 总结、生成或对话
4. **管理笔记** - 搜索、分类、收藏、导出

### AI 功能使用

#### 生成笔记
- 进入"AI生成"页面
- 输入主题或关键词
- 选择输出格式（Markdown/纯文本）
- 点击生成，等待 AI 创作

#### 总结笔记
- 在笔记列表中点击"AI总结"
- 或直接上传已有笔记
- AI 会自动提取关键信息

#### AI 对话
- 在首页打开 AI 助手面板
- 输入问题或指令
- 支持 `/note` 命令引用笔记
- 可上传笔记作为上下文

### 导入笔记

1. 点击"导入笔记"按钮
2. 选择 Word (.docx) 或 TXT 文件
3. 预览内容并确认
4. 系统自动保存至历史记录

## 📚 详细文档

更多功能说明和技术细节请查看 [docs](./docs/) 文件夹：

- 📌 [环境配置指南](./docs/ENVIRONMENT_CONFIG.md) - 详细的配置说明
- 📌 [项目优化总结](./docs/PROJECT_OPTIMIZATION_SUMMARY.md) - 代码优化记录
- 📌 [AI功能文档](./docs/AI_*.md) - AI相关功能说明
- 📌 [修复报告](./docs/FIX_*.md) - Bug修复记录
- 📌 [功能特性](./docs/*_FEATURE.md) - 功能特性介绍

## 🔧 开发说明

### 后端开发

```bash
cd backend

# 启动开发服务器（热重载）
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 运行测试
pytest
```

### 前端开发

```bash
cd frontend

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览生产构建
npm run preview
```

### 代码规范

- **前端**: 遵循 Vue 3 Composition API 最佳实践
- **后端**: 遵循 PEP 8 Python 编码规范
- **Git提交**: 使用语义化提交信息

## 🐛 常见问题

### Q: AI 响应很慢怎么办？
A: 检查 Ollama 服务是否正常运行，可以尝试使用更小的模型（如 qwen:1.8b）

### Q: Redis 连接失败？
A: 确保 Redis 服务已启动，检查 `.env` 中的配置是否正确

### Q: 图片上传失败？
A: 检查 `backend/uploads` 目录是否有写入权限

### Q: 前端白屏？
A: 检查浏览器控制台错误，确认后端 API 地址配置正确

更多问题请查看 [docs](./docs/) 中的修复报告文档。

## 📝 更新日志

详见各功能文档：
- [AI生成优化](./docs/AI_GENERATE_*.md)
- [笔记导入功能](./docs/IMPORT_*.md)
- [缓存优化](./docs/REDIS_*.md)
- [界面优化](./docs/HOME_*.md)

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 👨‍💻 作者

如有问题或建议，欢迎联系！

---

**最后更新**: 2026-05-12  
**版本**: 1.0.0  
**状态**: ✅ 活跃开发中
