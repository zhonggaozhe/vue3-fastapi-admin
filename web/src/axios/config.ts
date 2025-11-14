import { AxiosResponse, InternalAxiosRequestConfig } from './types'
import { ElMessage } from 'element-plus'
import qs from 'qs'
import { SUCCESS_CODE, TRANSFORM_REQUEST_DATA } from '@/constants'
import { useUserStoreWithOut } from '@/store/modules/user'
import { objToFormData } from '@/utils'

const defaultRequestInterceptors = (config: InternalAxiosRequestConfig) => {
  if (
    config.method === 'post' &&
    config.headers['Content-Type'] === 'application/x-www-form-urlencoded'
  ) {
    config.data = qs.stringify(config.data)
  } else if (
    TRANSFORM_REQUEST_DATA &&
    config.method === 'post' &&
    config.headers['Content-Type'] === 'multipart/form-data' &&
    !(config.data instanceof FormData)
  ) {
    config.data = objToFormData(config.data)
  }
  if (config.method === 'get' && config.params) {
    let url = config.url as string
    url += '?'
    const keys = Object.keys(config.params)
    for (const key of keys) {
      if (config.params[key] !== void 0 && config.params[key] !== null) {
        url += `${key}=${encodeURIComponent(config.params[key])}&`
      }
    }
    url = url.substring(0, url.length - 1)
    config.params = {}
    config.url = url
  }
  return config
}

const defaultResponseInterceptors = (response: AxiosResponse) => {
  if (response?.config?.responseType === 'blob') {
    return response
  }

  const { code, message, data } = response.data || {}
  if (code === SUCCESS_CODE) {
    return { code, message, data }
  }

  const friendly = message && SUPER_ADMIN_ERROR_MAP[message]
  ElMessage.error(friendly || message || 'Server Error')
  if (code === 401) {
    const userStore = useUserStoreWithOut()
    userStore.logout()
  }
  return Promise.reject({ code, message })
}

export { defaultResponseInterceptors, defaultRequestInterceptors }
const SUPER_ADMIN_ERROR_MAP: Record<string, string> = {
  SUPER_ADMIN_IMMUTABLE: '超级管理员不可修改或删除',
  SUPER_ADMIN_RESERVED: '超级管理员保留，无法重复创建',
  SUPER_ADMIN_INVISIBLE: '超级管理员不会展示在列表中'
}
