# NoteMind 桌面端（Electron）

基于 **Electron + Vue 3** 的桌面客户端，100% 复用 Web 端前端代码。

## 技术栈

| 层级 | 技术 |
|------|------|
| 桌面框架 | Electron 28.x |
| 前端 | Vue 3 + Vite（复用 Web 端） |
| 打包 | electron-builder |
| 本地存储 | electron-store |
| 原生能力 | IPC + Node.js fs |

## 项目结构

```
desktop/
├── electron/
│   ├── main.js          # 主进程（窗口、菜单、托盘）
│   ├── preload.js       # 预加载脚本（安全API桥接）
│   └── ipc.js           # IPC 处理（文件、对话框、存储）
├── build/
│   ├── icon.svg         # 图标源文件
│   └── generate-icons.js # 图标生成说明
├── package.json
└── .gitignore
```

## 开发运行

### 前置条件

- Node.js 18+
- 已启动后端服务（http://localhost:8000）
- 前端开发服务器（http://localhost:5174）

### 启动步骤

```bash
# 1. 启动后端（在 note-takingAssistant/backend 目录）
pip install -r requirements.txt
python main.py

# 2. 启动前端开发服务器（在 note-takingAssistant/frontend 目录）
cd ../note-takingAssistant/frontend
npm install
npm run dev

# 3. 启动 Electron 桌面端（在 desktop 目录）
cd ../../desktop
npm install
npm run dev
```

## 生产构建

### Windows x64

```bash
npm run dist
```

输出目录：`release/`

### macOS（需在 macOS 上构建）

```bash
npm run dist:mac
```

## 前端适配说明

前端代码通过 `window.electronAPI` 检测是否运行在桌面端：

```javascript
import { useDesktop } from '@/composables/useDesktop'

const { isDesktop, showOpenDialog, readFile } = useDesktop()

if (isDesktop.value) {
  // 桌面端：使用原生文件对话框
  const result = await showOpenDialog({ properties: ['openFile'] })
}
```

### 可用 API

| 类别 | API |
|------|-----|
| 应用 | `app.getVersion`, `app.getPath`, `app.openExternal` |
| 窗口 | `window.minimize`, `window.maximize`, `window.close` |
| 对话框 | `dialog.showOpenDialog`, `dialog.showSaveDialog` |
| 文件系统 | `fs.readFile`, `fs.writeFile`, `fs.readDir`, `fs.stat` |
| 本地存储 | `store.get`, `store.set`, `store.delete` |
| 系统 | `shell.openPath`, `clipboard.writeText` |

## 菜单快捷键

| 功能 | 快捷键 |
|------|--------|
| 新建笔记 | Ctrl+N |
| 导入笔记 | Ctrl+I |
| 导出笔记 | Ctrl+E |
| 首页 | Ctrl+1 |
| 我的笔记 | Ctrl+2 |
| AI 生成 | Ctrl+3 |
| 思维导图 | Ctrl+4 |
| 开发者工具 | Ctrl+Shift+I |

## 图标生成

打包前需要准备图标：

### Windows (.ico)

1. 访问 https://www.icoconverter.com/
2. 上传 `build/icon.svg`
3. 下载 `icon.ico` 放到 `build/` 目录

### macOS (.icns)

在 macOS 上使用 `iconutil` 命令生成。

## 与 Web 端差异

| 特性 | Web 端 | 桌面端 |
|------|--------|--------|
| 数据存储 | MySQL + Redis | 共用后端 API |
| 文件访问 | 浏览器上传下载 | 原生文件对话框 |
| 系统托盘 | ❌ | ✅ |
| 本地配置 | localStorage | electron-store |
| 快捷键 | 浏览器内 | 系统级菜单 |
| 包体积 | — | ~150-200MB |
