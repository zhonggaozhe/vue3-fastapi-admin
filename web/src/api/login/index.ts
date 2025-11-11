import request from '@/axios'
import type { LoginParams, LoginResult, UserInfo } from './types'

interface RoleParams {
  roleName: string
}

export const loginApi = (data: LoginParams): Promise<IResponse<LoginResult>> => {
  return request.post({ url: '/v1/base/access_token', data })
}

export const loginOutApi = (): Promise<IResponse> => {
  return request.get({ url: '/mock/user/loginOut' })
}

export const getUserInfoApi = (): Promise<IResponse<UserInfo>> => {
  return request.get({ url: '/v1/base/userinfo' })
}

export const getUserListApi = ({ params }: AxiosConfig) => {
  return request.get<{
    code: string
    data: {
      list: UserInfo[]
      total: number
    }
  }>({ url: '/mock/user/list', params })
}

export const getAdminRoleApi = (
  params: RoleParams
): Promise<IResponse<AppCustomRouteRecordRaw[]>> => {
  return request.get({ url: '/mock/role/list', params })
}

export const getTestRoleApi = (params: RoleParams): Promise<IResponse<string[]>> => {
  return request.get({ url: '/mock/role/list2', params })
}
