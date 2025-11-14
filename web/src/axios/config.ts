import { AxiosResponse, InternalAxiosRequestConfig, AxiosError } from './types'
import { ElMessage } from 'element-plus'
import qs from 'qs'
import { SUCCESS_CODE, TRANSFORM_REQUEST_DATA } from '@/constants'
import { useUserStoreWithOut } from '@/store/modules/user'
import { objToFormData } from '@/utils'
import { refreshTokenApi } from '@/api/login'
import axios from 'axios'

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

// Token 刷新相关状态
let isRefreshing = false
let refreshPromise: Promise<string> | null = null
const failedQueue: Array<{
  resolve: (value: string) => void
  reject: (error: any) => void
}> = []

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
  // 注意：401 错误已经在 tokenRefreshInterceptor 中处理，这里不再处理
  // 如果 tokenRefreshInterceptor 没有处理（比如没有 refresh_token），才会到这里
  if (code === 401) {
    const userStore = useUserStoreWithOut()
    // 只有在没有 refresh_token 的情况下才直接登出
    // 有 refresh_token 的情况已经在 tokenRefreshInterceptor 中处理
    if (!userStore.getRefreshToken) {
      userStore.logout()
    }
  }
  return Promise.reject({ code, message })
}

// 处理 401 错误的响应拦截器（在 defaultResponseInterceptors 之前执行）
const tokenRefreshInterceptor = (error: AxiosError) => {
  const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

  // 如果是 401 错误且不是刷新接口本身，且未重试过
  if (
    error.response?.status === 401 &&
    originalRequest &&
    !originalRequest._retry &&
    !originalRequest.url?.includes('/auth/refresh') &&
    !originalRequest.url?.includes('/auth/login')
  ) {
    const userStore = useUserStoreWithOut()
    const refreshToken = userStore.getRefreshToken

    // 如果没有 refresh_token，直接跳转登录
    if (!refreshToken) {
      userStore.logout()
      return Promise.reject(error)
    }

    // 如果正在刷新，将请求加入队列等待
    if (isRefreshing && refreshPromise) {
      return new Promise((resolve, reject) => {
        failedQueue.push({ resolve, reject })
      })
        .then((newToken: string) => {
          // 使用新 token 重试原始请求
          originalRequest.headers = originalRequest.headers || {}
          originalRequest.headers['Authorization'] = `Bearer ${newToken}`
          return axios(originalRequest)
        })
        .catch((err) => {
          return Promise.reject(err)
        })
    }

    // 开始刷新 token
    originalRequest._retry = true
    isRefreshing = true

    refreshPromise = refreshTokenApi(refreshToken)
      .then((res) => {
        if (res && res.data) {
          const { tokens, user, session } = res.data
          const newAccessToken = tokens?.accessToken
          const newRefreshToken = tokens?.refreshToken

          if (newAccessToken && newRefreshToken) {
            // 更新 store 中的 token
            userStore.setToken(`Bearer ${newAccessToken}`)
            userStore.setRefreshToken(newRefreshToken)
            if (session) {
              userStore.setSession(session)
            }
            if (user) {
              userStore.setUserInfo({
                username: user?.username || '',
                role: user?.role,
                roleId: user?.roleId,
                permissions: user?.permissions || [],
                attributes: user?.attributes
              })
            }

            // 处理等待队列中的所有请求
            failedQueue.forEach(({ resolve }) => resolve(newAccessToken))
            failedQueue.length = 0

            return newAccessToken
          } else {
            throw new Error('Invalid refresh response')
          }
        } else {
          throw new Error('Refresh token failed')
        }
      })
      .catch((err) => {
        // 刷新失败，清空队列并跳转登录
        failedQueue.forEach(({ reject }) => reject(err))
        failedQueue.length = 0
        userStore.logout()
        return Promise.reject(err)
      })
      .finally(() => {
        isRefreshing = false
        refreshPromise = null
      })

    // 等待刷新完成并重试原始请求
    return refreshPromise
      .then((newToken: string) => {
        originalRequest.headers = originalRequest.headers || {}
        originalRequest.headers['Authorization'] = `Bearer ${newToken}`
        return axios(originalRequest)
      })
      .catch((err) => {
        return Promise.reject(err)
      })
  }

  // 其他错误直接返回
  return Promise.reject(error)
}

export { defaultResponseInterceptors, defaultRequestInterceptors, tokenRefreshInterceptor }
const SUPER_ADMIN_ERROR_MAP: Record<string, string> = {
  SUPER_ADMIN_IMMUTABLE: '超级管理员不可修改或删除',
  SUPER_ADMIN_RESERVED: '超级管理员保留，无法重复创建',
  SUPER_ADMIN_INVISIBLE: '超级管理员不会展示在列表中'
}
