# Token 自动刷新实现总结

## 实现概述

已成功实现完整的 JWT Token 自动刷新机制，包括前端自动刷新逻辑和后端 Refresh Token 轮换（Rotation）机制。

## 后端实现

### 1. TokenAgent 增强 (`app/agents/token.py`)

新增方法：
- `verify_refresh_token()`: 验证 refresh token 在 Redis 中的状态
- `is_token_blacklisted()`: 检查 token 是否在黑名单中
- `blacklist_token()`: 将 token 加入黑名单
- `revoke_refresh_token()`: 撤销 refresh token（标记为已使用）

### 2. AuthOrchestrator 刷新流程 (`app/agents/orchestrator.py`)

`refresh()` 方法实现完整的刷新流程：

1. **解码并验证 refresh_token JWT**
   - 检查 token 格式和签名
   - 验证 token 类型为 "refresh"

2. **检查黑名单**
   - 防止重复使用已用过的 refresh token

3. **验证 Redis 中的状态**
   - 检查 refresh token 是否存在
   - 检查状态是否为 "active"

4. **加载用户信息**
   - 根据 user_id 加载用户
   - 加载角色和权限

5. **Token 轮换**
   - 将旧的 refresh_token 加入黑名单
   - 标记 Redis 中的旧 refresh token 为 "revoked"

6. **生成新 Token 对**
   - 生成新的 access_token（15分钟）
   - 生成新的 refresh_token（7-30天）

7. **更新会话**
   - 创建新 session
   - 绑定新的 refresh_jti

8. **审计日志**
   - 记录刷新操作

### 3. Token 验证增强 (`app/core/auth.py`)

`get_current_user()` 方法现在能够：
- 区分 token 过期和其他错误
- 返回正确的错误码 `AUTH.TOKEN_EXPIRED`（401）

### 4. 安全增强 (`app/core/security.py`)

`decode_jwt_token()` 方法现在能够：
- 捕获 `ExpiredSignatureError` 异常
- 区分 token 过期和签名错误

## 前端实现

### 1. Refresh API (`web/src/api/login/index.ts`)

新增 `refreshTokenApi()` 函数：
```typescript
export const refreshTokenApi = (refreshToken: string, deviceId?: string)
```

### 2. 自动刷新拦截器 (`web/src/axios/config.ts`)

实现 `tokenRefreshInterceptor` 拦截器，处理逻辑：

1. **检测 401 错误**
   - 排除 `/auth/refresh` 和 `/auth/login` 接口
   - 检查是否已重试过（`_retry` 标志）

2. **并发控制**
   - 使用 `isRefreshing` 标志防止重复刷新
   - 使用 `refreshPromise` 存储刷新 Promise
   - 使用 `failedQueue` 队列存储等待的请求

3. **刷新流程**
   - 调用 `refreshTokenApi()` 刷新 token
   - 更新 store 中的 token、refreshToken、session 和 userInfo
   - 处理等待队列中的所有请求

4. **错误处理**
   - 刷新失败时清空队列
   - 跳转登录页

5. **请求重试**
   - 刷新成功后使用新 token 重试原始请求

### 3. 拦截器注册 (`web/src/axios/service.ts`)

拦截器注册顺序：
1. 请求拦截器（添加 Authorization header）
2. **Token 刷新拦截器**（处理 401 错误）
3. 默认响应拦截器（处理业务逻辑）

## 工作流程

### 正常请求流程
```
客户端 → API 请求（携带 access_token）→ 后端验证 → 返回结果
```

### Access Token 过期流程
```
客户端 → API 请求（access_token 已过期）
  ↓
后端返回 401 (AUTH.TOKEN_EXPIRED)
  ↓
前端拦截器检测到 401
  ↓
检查是否有 refresh_token
  ├─ 无 → 跳转登录页
  └─ 有 → 发起刷新请求
      ↓
    POST /auth/refresh
      ↓
    后端验证 refresh_token
      ├─ 无效 → 返回 401 → 跳转登录页
      └─ 有效 → 生成新 token 对
          ↓
        旧 refresh_token 加入黑名单
          ↓
        返回新 token 对
          ↓
    前端更新 token
      ↓
    重试原始请求（使用新 access_token）
      ↓
    返回结果
```

### 并发请求处理
```
请求 A (401) ──┐
请求 B (401) ──┼─→ 第一个请求：发起刷新
请求 C (401) ──┘   其他请求：加入等待队列
                  ↓
              刷新完成
                  ↓
        ┌─────────┼─────────┐
        ↓         ↓         ↓
    重试请求 A  重试请求 B  重试请求 C
```

## 安全特性

1. **Refresh Token 轮换**
   - 每次刷新后，旧的 refresh token 立即失效
   - 防止 refresh token 泄露后的重放攻击

2. **黑名单机制**
   - 已使用的 refresh token 加入 Redis 黑名单
   - 黑名单 TTL = 原 token 剩余过期时间

3. **状态验证**
   - 验证 refresh token 在 Redis 中的状态
   - 只有 "active" 状态的 token 可以使用

4. **并发控制**
   - 防止多个请求同时触发刷新
   - 确保只发起一次刷新请求

## 测试建议

### 1. 正常刷新测试
- 使用过期的 access_token 发起请求
- 验证自动刷新并重试成功

### 2. 并发刷新测试
- 同时发起多个请求，都返回 401
- 验证只发起一次刷新请求
- 验证所有请求最终都成功

### 3. Refresh Token 过期测试
- 使用过期的 refresh_token 刷新
- 验证返回 401 并跳转登录

### 4. Refresh Token 重复使用测试
- 使用 refresh_token 刷新一次
- 再次使用同一个 refresh_token
- 验证返回 401（已加入黑名单）

### 5. 无 Refresh Token 测试
- 清除 refresh_token
- 发起请求返回 401
- 验证直接跳转登录页

## 配置说明

### 后端配置 (`app/core/settings.py`)
- `access_token_ttl_minutes`: Access token 过期时间（默认 15 分钟）
- `refresh_token_ttl_minutes`: Refresh token 过期时间（默认 24 * 60 分钟）

### Redis Key 规范
- `rt:{hash}`: Refresh token 状态
- `jti:black:{jti}`: Token 黑名单
- `token:access:{jti}`: Access token 元数据

## 注意事项

1. **拦截器顺序很重要**
   - Token 刷新拦截器必须在默认响应拦截器之前注册
   - 确保 401 错误先被刷新拦截器处理

2. **避免无限循环**
   - 刷新接口本身不触发刷新逻辑
   - 登录接口不触发刷新逻辑

3. **错误处理**
   - 刷新失败时清空所有状态
   - 跳转登录页，避免用户困惑

4. **性能考虑**
   - 使用 Promise 队列避免重复刷新
   - Redis 操作使用连接池

## 后续优化建议

1. **主动刷新**
   - 在 access_token 即将过期前（如剩余 5 分钟）主动刷新
   - 减少被动刷新带来的延迟

2. **监控指标**
   - 刷新请求总数
   - 刷新成功率
   - 刷新耗时（P50/P95/P99）
   - 黑名单命中次数

3. **用户体验**
   - 刷新时显示加载状态（可选）
   - 刷新失败时显示友好提示

4. **安全性增强**
   - IP 检查（refresh 请求的 IP 是否与登录时一致）
   - 设备指纹验证
   - 异常行为检测（如短时间内多次刷新）

