export interface UserLoginType {
  username: string
  password: string
}

export type LoginParams = UserLoginType

export interface LoginResult {
  access_token: string
  username: string
}

export interface UserInfo {
  id: number
  username: string
  alias?: string
  email?: string
  phone?: string
  avatar?: string
  is_active?: boolean
  is_superuser?: boolean
  last_login?: string
  role?: string
  roleId?: string | number
}
