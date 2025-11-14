# Token 自动刷新流程设计文档

## 1. 概述

本文档描述了一套完整的 JWT Token 自动刷新机制，包括前端自动刷新逻辑和后端 Refresh Token 轮换（Rotation）机制。

## 2. 核心设计原则

### 2.1 安全原则
- **Refresh Token 单次有效**：每次使用 refresh token 后，旧的 refresh token 立即失效
- **Token 轮换（Rotation）**：刷新时生成新的 access token 和 refresh token
- **黑名单机制**：失效的 token 加入 Redis 黑名单，防止重放攻击
- **并发控制**：防止多个请求同时触发刷新，导致重复刷新

### 2.2 用户体验原则
- **静默刷新**：用户无感知，自动刷新 token
- **请求重试**：刷新成功后自动重试失败的请求
- **失败降级**：刷新失败时跳转登录页，避免无限循环

## 3. 详细流程

### 3.1 正常请求流程

```
┌─────────┐
│  Client │
└────┬────┘
     │ 1. 发起 API 请求（携带 access_token）
     ▼
┌─────────────────┐
│  Axios Request  │
│  Interceptor    │
└────┬────────────┘
     │ 2. 添加 Authorization Header
     ▼
┌─────────────────┐
│   FastAPI       │
│   Backend       │
└────┬────────────┘
     │ 3. 验证 access_token
     │    - 检查签名
     │    - 检查过期时间
     │    - 检查黑名单
     ▼
┌─────────────────┐
│   Response 200  │
└─────────────────┘
```

### 3.2 Access Token 过期流程（自动刷新）

```
┌─────────┐
│  Client │
└────┬────┘
     │ 1. 发起 API 请求（access_token 已过期）
     ▼
┌─────────────────┐
│  Axios Request  │
└────┬────────────┘
     │
     ▼
┌─────────────────┐
│   FastAPI       │
│   Backend       │
└────┬────────────┘
     │ 2. 验证失败：AUTH.TOKEN_EXPIRED (401)
     ▼
┌─────────────────┐
│  Response 401   │
└────┬────────────┘
     │
     ▼
┌─────────────────────────────────┐
│  Axios Response Interceptor     │
│  - 检测到 401 错误              │
│  - 检查是否有 refresh_token     │
│  - 检查是否正在刷新（防并发）   │
└────┬────────────────────────────┘
     │
     ├─ 如果正在刷新 → 等待刷新完成
     │
     ├─ 如果没有 refresh_token → 跳转登录
     │
     └─ 否则 → 发起刷新请求
         │
         ▼
┌─────────────────────────────────┐
│  POST /auth/refresh             │
│  {                              │
│    refreshToken: "xxx",         │
│    deviceId: "xxx"              │
│  }                              │
└────┬────────────────────────────┘
     │
     ▼
┌─────────────────────────────────┐
│  Backend: AuthOrchestrator      │
│  .refresh()                     │
└────┬────────────────────────────┘
     │
     ├─ 3.1 验证 refresh_token
     │   - 解码 JWT
     │   - 检查类型（type=refresh）
     │   - 检查过期时间
     │
     ├─ 3.2 检查 Redis 状态
     │   - 查询 rt:{hash} 是否存在
     │   - 检查状态是否为 "active"
     │   - 检查是否在黑名单中
     │
     ├─ 3.3 加载用户信息
     │   - 根据 user_id 加载用户
     │   - 加载角色和权限
     │
     ├─ 3.4 生成新 Token 对
     │   - 生成新的 access_token（15分钟）
     │   - 生成新的 refresh_token（7-30天）
     │   - 保存到 Redis
     │
     ├─ 3.5 旧 Token 加入黑名单
     │   - 旧 refresh_token.jti → jti:black:{jti}
     │   - 设置 TTL = 旧 refresh_token 剩余过期时间
     │
     ├─ 3.6 更新会话
     │   - 创建新 session
     │   - 绑定新的 refresh_jti
     │
     └─ 3.7 审计日志
         │
         ▼
┌─────────────────────────────────┐
│  Response 200                   │
│  {                              │
│    tokens: {                    │
│      accessToken: "new_jwt",    │
│      refreshToken: "new_refresh"│
│    },                           │
│    session: {...},              │
│    user: {...}                  │
│  }                              │
└────┬────────────────────────────┘
     │
     ▼
┌─────────────────────────────────┐
│  Frontend: 更新 Token           │
│  - 保存新的 access_token        │
│  - 保存新的 refresh_token       │
│  - 更新 session 信息            │
└────┬────────────────────────────┘
     │
     ▼
┌─────────────────────────────────┐
│  重试原始请求                   │
│  - 使用新的 access_token        │
│  - 返回原始请求结果             │
└─────────────────────────────────┘
```

### 3.3 并发请求处理流程

当多个请求同时返回 401 时，需要防止重复刷新：

```
请求 A (401) ──┐
               ├─→ 检测到需要刷新
请求 B (401) ──┤   ├─→ 第一个请求：发起刷新
               │   │
请求 C (401) ──┘   └─→ 其他请求：等待刷新完成
                     │
                     ▼
                ┌─────────────┐
                │ 刷新完成    │
                └──────┬──────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
    重试请求 A    重试请求 B    重试请求 C
```

**实现方式**：
- 使用 Promise 队列：第一个请求创建刷新 Promise，其他请求等待该 Promise
- 使用标志位：`isRefreshing` 标志 + `refreshPromise` 变量

### 3.4 Refresh Token 过期流程

```
┌─────────────────┐
│  POST /refresh  │
└────┬────────────┘
     │
     ▼
┌─────────────────┐
│  Backend 验证   │
└────┬────────────┘
     │
     ├─ refresh_token 过期
     │
     ▼
┌─────────────────┐
│  Response 401   │
│  AUTH.REFRESH_INVALID
└────┬────────────┘
     │
     ▼
┌─────────────────┐
│  Frontend       │
│  - 清除所有 token
│  - 跳转登录页
└─────────────────┘
```

## 4. 前端实现细节

### 4.1 响应拦截器逻辑

```typescript
// 伪代码
let isRefreshing = false
let refreshPromise: Promise<string> | null = null
const failedQueue: Array<{
  resolve: (value: string) => void
  reject: (error: any) => void
}> = []

axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    
    // 如果是 401 且不是刷新接口本身
    if (error.response?.status === 401 && 
        !originalRequest._retry &&
        !originalRequest.url?.includes('/auth/refresh')) {
      
      originalRequest._retry = true
      
      // 如果没有 refresh_token，直接跳转登录
      if (!refreshToken) {
        logout()
        return Promise.reject(error)
      }
      
      // 如果正在刷新，等待刷新完成
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then(() => {
          // 使用新 token 重试
          originalRequest.headers['Authorization'] = `Bearer ${newAccessToken}`
          return axios(originalRequest)
        })
      }
      
      // 开始刷新
      isRefreshing = true
      refreshPromise = refreshTokenRequest()
        .then(({ accessToken, refreshToken: newRefreshToken }) => {
          // 更新 token
          updateTokens(accessToken, newRefreshToken)
          
          // 处理等待队列
          failedQueue.forEach(({ resolve }) => resolve(accessToken))
          failedQueue.length = 0
          
          return accessToken
        })
        .catch((err) => {
          // 刷新失败，清空队列并跳转登录
          failedQueue.forEach(({ reject }) => reject(err))
          failedQueue.length = 0
          logout()
          throw err
        })
        .finally(() => {
          isRefreshing = false
          refreshPromise = null
        })
      
      // 等待刷新完成并重试
      const newToken = await refreshPromise
      originalRequest.headers['Authorization'] = `Bearer ${newToken}`
      return axios(originalRequest)
    }
    
    return Promise.reject(error)
  }
)
```

### 4.2 主动刷新机制（可选）

除了被动刷新（401 触发），还可以实现主动刷新：

```typescript
// 在 access_token 即将过期前（如剩余 5 分钟）主动刷新
setInterval(() => {
  const token = getAccessToken()
  if (token) {
    const payload = decodeJWT(token)
    const expiresIn = payload.exp - Date.now() / 1000
    if (expiresIn < 5 * 60) { // 剩余 5 分钟
      refreshTokenSilently()
    }
  }
}, 60000) // 每分钟检查一次
```

## 5. 后端实现细节

### 5.1 Refresh Token 验证

```python
async def refresh(
    self,
    db: AsyncSession,
    redis: Redis,
    payload: RefreshRequest,
    request: Request | None = None,
) -> LoginResponse:
    # 1. 解码 refresh_token
    try:
        refresh_claims = decode_jwt_token(payload.refresh_token)
    except ValueError:
        raise_error("AUTH.REFRESH_INVALID")
    
    # 2. 验证 token 类型
    if refresh_claims.get("type") != "refresh":
        raise_error("AUTH.REFRESH_INVALID")
    
    # 3. 检查黑名单
    jti = refresh_claims.get("jti")
    if await self._is_token_blacklisted(redis, jti):
        raise_error("AUTH.REFRESH_INVALID")
    
    # 4. 验证 Redis 中的状态
    refresh_key = self._refresh_key(payload.refresh_token)
    refresh_data = await redis.hgetall(refresh_key)
    if not refresh_data or refresh_data.get("status") != "active":
        raise_error("AUTH.REFRESH_INVALID")
    
    # 5. 加载用户
    user_id = refresh_claims.get("sub")
    user = await self.identity_agent.load_user(db, int(user_id))
    
    # 6. 将旧 refresh_token 加入黑名单
    await self._blacklist_refresh_token(redis, jti, refresh_claims.get("exp"))
    
    # 7. 生成新 token 对
    tokens = await self.token_agent.issue_pair(redis, user, payload.device_id)
    
    # 8. 更新会话
    session_info = await self.session_agent.create_session(
        redis, user_id=user.id, 
        refresh_jti=tokens.refresh_payload["jti"], 
        device_id=payload.device_id
    )
    
    # 9. 审计日志
    await self.audit_agent.log_event(...)
    
    return LoginResponse(...)
```

### 5.2 黑名单检查

```python
async def _is_token_blacklisted(self, redis: Redis, jti: str) -> bool:
    key = f"jti:black:{jti}"
    exists = await redis.exists(key)
    return exists > 0

async def _blacklist_refresh_token(self, redis: Redis, jti: str, exp: int | None):
    key = f"jti:black:{jti}"
    await redis.set(key, "1")
    if exp:
        await redis.expireat(key, exp)
```

## 6. Redis Key 设计

| Key 模式 | 示例 | 用途 | TTL |
|---------|------|------|-----|
| `rt:{hash}` | `rt:abc123...` | 存储 refresh token 状态 | = refresh_token 过期时间 |
| `jti:black:{jti}` | `jti:black:xxx` | 黑名单（已使用的 refresh token） | = 原 token 剩余过期时间 |
| `token:access:{jti}` | `token:access:yyy` | 存储 access token 元数据 | = access_token 过期时间 |

## 7. 错误码定义

| 错误码 | HTTP 状态 | 含义 | 前端处理 |
|--------|----------|------|---------|
| `AUTH.TOKEN_EXPIRED` | 401 | Access token 过期 | 自动刷新 |
| `AUTH.REFRESH_INVALID` | 401 | Refresh token 无效/过期 | 跳转登录 |
| `AUTH.INVALID_CREDENTIAL` | 401 | Token 格式错误 | 跳转登录 |
| `AUTH.FORBIDDEN` | 403 | 权限不足 | 显示错误 |

## 8. 安全考虑

### 8.1 Refresh Token 轮换的好处
- **防止重放攻击**：即使 refresh token 泄露，也只能使用一次
- **检测 token 泄露**：如果发现旧 refresh token 被使用，说明可能泄露
- **会话控制**：可以主动撤销特定设备的 refresh token

### 8.2 其他安全措施
- **HTTPS 传输**：所有 token 通过 HTTPS 传输
- **HttpOnly Cookie（可选）**：refresh token 可以存储在 HttpOnly Cookie 中
- **设备绑定**：refresh token 与 device_id 绑定
- **IP 检查（可选）**：可以检查 refresh 请求的 IP 是否与登录时一致

## 9. 测试场景

### 9.1 正常刷新
1. 使用过期的 access_token 发起请求
2. 验证自动刷新并重试成功

### 9.2 并发刷新
1. 同时发起多个请求，都返回 401
2. 验证只发起一次刷新请求
3. 验证所有请求最终都成功

### 9.3 Refresh Token 过期
1. 使用过期的 refresh_token 刷新
2. 验证返回 401 并跳转登录

### 9.4 Refresh Token 重复使用
1. 使用 refresh_token 刷新一次
2. 再次使用同一个 refresh_token
3. 验证返回 401（已加入黑名单）

## 10. 性能优化

- **Redis 连接池**：使用连接池减少连接开销
- **批量操作**：使用 Redis Pipeline 批量操作
- **缓存用户信息**：刷新时缓存用户信息，减少数据库查询
- **异步处理**：审计日志可以异步写入

## 11. 监控指标

建议监控以下指标：
- `auth_refresh_total`：刷新请求总数
- `auth_refresh_success_total`：刷新成功数
- `auth_refresh_fail_total`：刷新失败数
- `auth_refresh_duration_ms`：刷新耗时（P50/P95/P99）
- `auth_token_expired_total`：token 过期次数
- `auth_blacklist_hits_total`：黑名单命中次数

