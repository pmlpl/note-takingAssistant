// API 基础配置
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// 上传文件相关配置
export const UPLOAD_IMAGE_URL = `${API_BASE_URL}/api/v1/note/upload-image`
export const IMAGE_BASE_URL = API_BASE_URL

// 其他可能的API端点可以在这里添加
export const API_ENDPOINTS = {
  NOTES: `${API_BASE_URL}/api/v1/notes`,
  USERS: `${API_BASE_URL}/api/v1/users`,
  AI: `${API_BASE_URL}/api/v1/ai`
}
