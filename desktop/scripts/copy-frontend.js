const fs = require('fs')
const path = require('path')

const RENDERER_DIST_PATH = process.env.RENDERER_DIST_PATH
  || path.resolve(__dirname, '..', 'renderer', 'dist')

const DESKTOP_DIST = path.resolve(__dirname, '..', 'dist')

if (!fs.existsSync(path.join(RENDERER_DIST_PATH, 'index.html'))) {
  console.error('错误：找不到 renderer/dist 目录，请先在 renderer 目录执行 npm run build')
  console.error('  路径:', RENDERER_DIST_PATH)
  process.exit(1)
}

console.log('清空目标目录:', DESKTOP_DIST)
if (fs.existsSync(DESKTOP_DIST)) {
  fs.rmSync(DESKTOP_DIST, { recursive: true, force: true })
}
fs.mkdirSync(DESKTOP_DIST, { recursive: true })

let fileCount = 0
let totalSize = 0

function copyDirSync(src, dest) {
  fs.mkdirSync(dest, { recursive: true })
  const entries = fs.readdirSync(src, { withFileTypes: true })

  for (const entry of entries) {
    const srcPath = path.join(src, entry.name)
    const destPath = path.join(dest, entry.name)

    try {
      if (entry.isDirectory()) {
        copyDirSync(srcPath, destPath)
      } else {
        fs.copyFileSync(srcPath, destPath)
        fileCount++
        totalSize += fs.statSync(srcPath).size
      }
    } catch (err) {
      console.error(`复制失败: ${srcPath} → ${destPath}`)
      console.error(err.message)
      process.exit(1)
    }
  }
}

console.log('源目录:', RENDERER_DIST_PATH)
copyDirSync(RENDERER_DIST_PATH, DESKTOP_DIST)

console.log(`完成! 共复制 ${fileCount} 个文件，${(totalSize / 1024 / 1024).toFixed(1)} MB`)
