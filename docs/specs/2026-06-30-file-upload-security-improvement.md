# 文件上传安全改进清单

> **归档说明**：本清单已实现完毕。P0-1（导入大小限制）落地为 `settings.MAX_IMPORT_BYTES`（默认 20MB），见 `backend/app/core/config.py` 与 `backend/app/api/v1/note.py`（`import_note` 流式读取校验，含 MD5 校验与可选覆盖）；配图上传另有 `IMAGE_MAX_BYTES`（5MB）上限。归档保留。

> 审查日期：2026-06-30
> 目标：提高上传体验 + 服务器安全
> 执行引擎：Trae / Claude Code 可直接按行执行

---

## 🔴 P0 - 紧急（有安全漏洞，必须修）

### P0-1 后端文件导入缺少大小限制（DoS 漏洞）

**问题**：`backend/app/api/v1/note.py` 的 `import_note` 端点没有校验文件大小，前端 20MB 限制形同虚设。

**文件**：`backend/app/api/v1/note.py`，约第 297-347 行

**修复步骤**：

1. 在 `import_note` 函数中，**在 `await file.read()` 之前**添加大小限制：

```python
# 在 allowed_extensions 后面插入这两行
MAX_IMPORT_BYTES = 20 * 1024 * 1024  # 20MB

# 在 file_ext 校验通过后，读取文件之前插入校验
# 方式一：利用 Starlette UploadFile.size（如果客户端提供了 Content-Length）
if file.size is not None and file.size > MAX_IMPORT_BYTES:
    raise HTTPException(
        status_code=413, detail=f"文件超过上限 {MAX_IMPORT_BYTES // 1024 // 1024}MB"
    )
```

2. 同时将 `MAX_IMPORT_BYTES` 提到 `file_upload.py` 或 `config.py` 中统一管理，不要散落魔法数字。

3. **同步修改前端** `frontend/src/composables/useNoteManager.js:146`，把 20MB 也改成读配置常量：

```javascript
import { MAX_IMPORT_SIZE } from '@/config/api'  // 新增常量
// ...
if (file.size > MAX_IMPORT_SIZE) {
```

---

### P0-2 文件名未清洗，存在路径注入风险

**问题**：`backend/app/utils/file_parser.py:109-126` 的 `extract_title_from_filename()` 没有调用 `os.path.basename()`。

**文件**：`backend/app/utils/file_parser.py`，第 109-126 行

**修复**：

```python
def extract_title_from_filename(filename: str) -> str:
    """从文件名中提取标题（去掉扩展名），已做路径清洗"""
    # 强制取 basename，防止 ../../etc/passwd.txt 路径遍历攻击
    safe_name = os.path.basename(filename)
    title = os.path.splitext(safe_name)[0]
    if not title.strip():
        title = "未命名笔记"
    return title.strip()
```

同样，`file_parser.py` 的 `parse_file()` 函数（第 83 行）也应做一次清洗：

```python
def parse_file(file_path: str, filename: str) -> Optional[str]:
    # 清洗文件名，防止路径混淆
    safe_filename = os.path.basename(filename)
    ext = os.path.splitext(safe_filename)[1].lower()
    # ... 后续逻辑保持不变
```

---

## 🟠 P1 - 重要（性能/稳定性问题）

### P1-1 文件导入应使用分块读写，避免内存抖动

**问题**：`backend/app/api/v1/note.py:319` 的 `await file.read()` 一次性把整个文件读进内存。多人并发上传 20MB 文件时内存占用暴增。

**文件**：`backend/app/api/v1/note.py`，`import_note` 函数的文件读取逻辑

**修复**：使用 `shutil.copyfileobj` 分块写入临时文件：

```python
import shutil

IMPORT_CHUNK_SIZE = 1024 * 1024  # 1MB 分块

# 替换原来的全量读写
with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
    # 分块读写，单块 1MB，防止大文件撑爆内存
    while True:
        chunk = await file.read(IMPORT_CHUNK_SIZE)
        if not chunk:
            break
        # 可选：在此处累加 bytes 长度，超过 MAX_IMPORT_BYTES 就中断
        tmp_file.write(chunk)
    tmp_path = tmp_file.name
```

同样，图片上传也建议分块（`file_upload.py` 处理虽小但原则应一致）。

---

### P1-2 导入文件异常时清理临时分片

**问题**：`note.py:317-343` 的 `import_note` 中，如果在 `tmp_file.write(raw)` 或 `await file.read()` 炸了，临时文件会残留在磁盘。

**文件**：`backend/app/api/v1/note.py`

**修复**：重构异常处理，确保 `tmp_path` 绑定后再进入清理块：

```python
tmp_path = None  # <-- 先声明
try:
    # 累计读取并校验大小
    total = 0
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
        tmp_path = tmp_file.name  # <-- Immediate bind
        while True:
            chunk = await file.read(IMPORT_CHUNK_SIZE)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_IMPORT_BYTES:
                raise HTTPException(status_code=413,
                    detail=f"文件超过上限 {MAX_IMPORT_BYTES // 1024 // 1024}MB")
            tmp_file.write(chunk)

    # parse + create note...
    # ...

except HTTPException:
    raise  # HTTPException 直接透传
except Exception as e:
    raise HTTPException(status_code=500, detail=f"导入笔记失败: {str(e)}")
finally:
    # 无论成功失败，临时文件必须删除
    if tmp_path is not None and os.path.exists(tmp_path):
        try:
            os.remove(tmp_path)
        except OSError:
            pass  # 删不掉也别崩，留给系统 /tmp 清理
```

---

## 🟡 P2 - 建议（体验/健壮性）

### P2-1 图片上传也应使用后端接口而非 base64 嵌入

**问题**：`frontend/src/components/RichText.vue:42-45` 让 wangEditor 把图片转 base64 嵌入 HTML。这会导致：
- 每张图膨胀 ~33%（base64 开销）
- 数据库被 base64 垃圾填满
- 笔记加载时传输量巨大

**文件**：`frontend/src/components/RichText.vue`，约第 39-46 行

**修复**：配置 wangEditor 使用后端上传接口：

```javascript
const editorConfig = {
  placeholder: '请输入内容...',
  MENU_CONF: {
    uploadImage: {
      // 改：使用后端上传端点，不再 base64
      server: '/api/v1/note/upload-image',
      fieldName: 'file',
      maxFileSize: 5 * 1024 * 1024,  // 5MB
      // 保留小图 base64 作为性能优化
      base64LimitSize: 100 * 1024,    // 100KB以下才用base64
      // 自定义插入格式
      customInsert(res, insertFn) {
        // res.data.url 是后端返回的图片路径
        insertFn(res.data.url)
      }
    }
  }
}
```

### P2-2 增加 Content-MD5 校验（可选）

**场景**：大文件上传后校验完整性。

**实现**（如需要）：
- 前端计算文件 MD5，放入请求头 `X-Content-MD5`
- 后端接收后，计算已写入文件的 MD5，与请求头比对
- 不匹配则返回 400 要求重传

这是一个 nice-to-have，不影响当前功能。

### P2-3 图片上传同样加上分块读写

**文件**：`backend/app/utils/file_upload.py`，图片上传入口在 `backend/app/api/v1/note.py:40-62`

图片最大 5MB，虽然内存影响不大，但为了一致性建议也分块。改动量很小：

```python
# upload_image 函数内部
CHUNK_SIZE = 1024 * 1024  # 1MB
file_bytes = bytearray()
while True:
    chunk = await file.read(CHUNK_SIZE)
    if not chunk:
        break
    file_bytes.extend(chunk)
    if len(file_bytes) > IMAGE_MAX_BYTES:
        raise HTTPException(status_code=413, detail="图片过大")

ok, ext, err = validate_image_bytes(bytes(file_bytes), file.filename or "")
```

---

## 📋 执行顺序

| 优先级 | 序号 | 预计耗时 | 风险 |
|--------|------|----------|------|
| 🔴 P0 | P0-1 服务端大小限制 | 15 min | 无 |
| 🔴 P0 | P0-2 文件名清洗 | 5 min | 无 |
| 🟠 P1 | P1-1 分块读写 | 20 min | 需测试大文件 |
| 🟠 P1 | P1-2 finally 清理 | 15 min | 需测试异常场景 |
| 🟡 P2 | P2-1 base64 → 服务端上传 | 30 min | 需联调前后端 |
| 🟡 P2 | P2-2 MD5校验(可选) | 1 h | 新功能 |
| 🟡 P2 | P2-3 图片分块 | 10 min | 无 |

---

## 改动文件清单

| 文件 | 改动类型 |
|------|----------|
| `backend/app/api/v1/note.py` | 大小限制 + 分块 + finally 清理 |
| `backend/app/utils/file_parser.py` | basename 清洗 |
| `backend/app/core/config.py` | 新增 MAX_IMPORT_BYTES 配置项 |
| `frontend/src/components/RichText.vue` | wangEditor 配置改为服务端上传 |
| `frontend/src/composables/useNoteManager.js` | 前端常量引用配置 |
| `frontend/src/config/api.js` | 新增 MAX_IMPORT_SIZE 导出 |

---

## 验证方法

执行修复后，用以下测试验证：

```bash
# 1. 路径遍历测试
curl -X POST "http://localhost:8000/api/v1/note/import" \
  -F "file=@test.txt;filename=../../etc/passwd.txt"

# 预期：标题为 "passwd"，不是 "../../etc/passwd"

# 2. 大文件拒绝测试（生成 50MB 垃圾文件）
dd if=/dev/zero of=big.bin bs=1M count=50
curl -X POST "http://localhost:8000/api/v1/note/import" \
  -F "file=@big.bin;filename=test.docx"

# 预期：HTTP 413

# 3. 临时文件清理测试
# 启动后端，发送一个损坏的 multipart 请求（中间掐断），
# 检查 /tmp 目录没有残留 .docx/.md/.txt 文件
```
