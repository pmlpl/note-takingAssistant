// API 基础配置（上传、图片绝对地址等）
// 生产环境用相对路径，由 nginx 代理 /api 和 /uploads 到后端
// 开发环境 vite.config.js 也代理了 /api 和 /uploads
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

export const UPLOAD_IMAGE_URL = `${API_BASE_URL}/api/v1/note/upload-image`
export const IMAGE_BASE_URL = API_BASE_URL

export const MAX_IMPORT_SIZE = 20 * 1024 * 1024
