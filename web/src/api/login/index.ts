import request from '@/axios'
import type { LoginResult, UserLoginType, UserType } from './types'

interface MenuRouteParams {
  username: string
}

export const loginApi = (data: UserLoginType): Promise<IResponse<LoginResult>> => {
  return request.post({ url: '/auth/login', data })
}

export const loginOutApi = (refreshToken?: string): Promise<IResponse> => {
  return request.post({
    url: '/auth/logout',
    data: refreshToken
      ? {
          refreshToken
        }
      : undefined
  })
}

export const getUserListApi = ({ params }: AxiosConfig) => {
  return request.get<{
    code: string
    data: {
      list: UserType[]
      total: number
    }
  }>({ url: '/mock/user/list', params })
}

export const getUserRoutesApi = (
  params: MenuRouteParams
): Promise<IResponse<AppCustomRouteRecordRaw[]>> => {
  return request.get({ url: '/menus/routes', params })
}

export const getTestRoleApi = (params: { roleName: string }): Promise<IResponse<string[]>> => {
  return request.get({ url: '/mock/role/list2', params })
}
