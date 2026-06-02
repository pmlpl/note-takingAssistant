// API 基础配置（上传、图片绝对地址等）
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const UPLOAD_IMAGE_URL = `${API_BASE_URL}/api/v1/note/upload-image`
export const IMAGE_BASE_URL = API_BASE_URL
