import { getApiBaseUrl } from '@/api'

function getUploadImageUrl() {
  const baseUrl = getApiBaseUrl()
  return `${baseUrl}/note/upload-image`
}

function getImageBaseUrl() {
  const baseUrl = getApiBaseUrl()
  return baseUrl.replace(/\/api$/, '')
}

export const UPLOAD_IMAGE_URL = getUploadImageUrl()
export const IMAGE_BASE_URL = getImageBaseUrl()

export const MAX_IMPORT_SIZE = 20 * 1024 * 1024