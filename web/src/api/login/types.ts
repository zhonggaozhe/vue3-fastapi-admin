export interface UserLoginType {
  username: string
  password: string
  deviceId?: string
  mfaCode?: string
}

export interface UserType extends UserLoginType {
  role: string
  roleId: string
}

export interface LoginUserInfo {
  username: string
  role: string
  roleId: string
  permissions: string[]
  attributes?: Record<string, any>
}

export interface LoginTokens {
  accessToken: string
  refreshToken: string
  token_type: string
  expires_in: number
  payload: Record<string, any>
}

export interface LoginSession {
  sid: string
  expires_at: string
}

export interface LoginResult {
  tokens: LoginTokens
  session: LoginSession
}

export interface UserRoutesResult {
  user: LoginUserInfo
  routes: AppCustomRouteRecordRaw[]
}
