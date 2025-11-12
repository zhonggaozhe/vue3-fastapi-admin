Python 3.11 + FastAPI 高性能异步权限认证系统（Agent-Oriented Architecture）设计文档

⸻

1. 概述（Overview）

本系统采用 Agent-Oriented Architecture，围绕 Python 3.11 + FastAPI 构建高性能认证、授权、会话管理与审计体系。
整体由多个自治 Agent 组成，通过 Orchestrator 统一编排。

背景：
	•	web 目录下是前端项目，app 目录下是后端项目
	•	web 基于 `element-plus` 免费开源的中后台模版。使用了最新的`vue3`，`vite`，`TypeScript`等主流技术开发
	•	web 项目已经实现权限功能，包括：
		•	用户管理
		•	角色管理
		•	菜单管理
		•	权限管理
		•	用户登录
		•	登录推出
		•	动态菜单
		•	权限控制
	•	web 现采用mock数据，后端接口未实现, 你现在要做的工作就是根据mock数据反向推理后端接口
⸻

设计目标：
	•	高性能
	•	高可观察性
	•	可扩展
	•	支持 JWT + Refresh Token
	•	支持 RBAC 权限体系
	•	支持 MFA、OAuth、黑名单、角色/策略缓存
	•	支持分布式/多实例部署
	•	使用 PostgreSQL + Redis

⸻

2. 总体架构（Architecture）

                         ┌────────────────────┐
                         │   Client / App     │
                         └─────────┬──────────┘
                                   │
                           HTTPS / API Gateway
                                   │
                         ┌─────────▼──────────┐
                         │  FastAPI Service    │
                         └─────────┬──────────┘
                                   │
                     ┌─────────────▼──────────────┐
                     │     Codex Orchestrator     │
                     └───────┬────────┬───────────┘
                             │        │
            ┌────────────────▼───┐ ┌──▼──────────────────┐
            │    IdentityAgent   │ │     TokenAgent       │
            └────────────────────┘ └──────────────────────┘
            ┌────────────────────┐ ┌──────────────────────┐
            │    RBACAgent       │ │    SessionAgent       │
            └────────────────────┘ └──────────────────────┘
            ┌────────────────────┐ ┌──────────────────────┐
            │   AuditAgent       │ │  RateLimitAgent       │
            └────────────────────┘ └──────────────────────┘


⸻

3. Agent 职责说明

3.1 Orchestrator（主控）

编排所有登录/登出/刷新/鉴权流程。
提供统一错误规约、事务一致性、重试、审计触发。

⸻

3.2 IdentityAgent（身份验证）

功能：
	•	用户名/邮箱登录
	•	密码认证（argon2 / bcrypt）
	•	可选 TOTP MFA
	•	账号锁定策略（连续失败 N 次）
	•	可选 OAuth2/OIDC/SAML 接入

输出：

{
  "user_id": 101,
  "username": "alice",
  "mfa_required": false,
  "attributes": {"dept": "RDM"}
}


⸻

3.3 TokenAgent（JWT + Refresh）
	•	生成 Access Token（短期，比如 15min）
	•	生成 Refresh Token（长期，比如 7-30 天）
	•	Refresh Token 轮换（rotate）
	•	JTI 黑名单（access/refresh）
	•	JWT kid 密钥轮换
	•	保存 Token 状态到 Redis

⸻

3.4 RBACAgent（授权）
	•	RBAC 模型：用户 → 角色 → 权限（resource:action）
	•	角色策略缓存（Redis）
	•	权限判定：is_allowed(user, resource, action)
	•	支持 ABAC 动态条件（可选）

⸻

3.5 SessionAgent（会话）
	•	生成 session_id(sid)
	•	绑定 user_id / device / ua / ip
	•	刷新会话（refresh rotate 时更新）
	•	支持多端会话、限制并发会话数量（可选）
	•	Redis 持久化（TTL = refresh token TTL）

⸻

3.6 AuditAgent（审计）

记录所有：
	•	登录成功/失败
	•	刷新令牌
	•	访问拒绝（403）
	•	权限变更
	•	配置变更
	•	敏感行为（比如导出数据）

可写入：
	•	PostgreSQL

⸻

3.7 RateLimitAgent（限流）

支持：
	•	IP 限流
	•	用户限流
	•	登录限流（防爆破）
	•	刷新 Token 限流

Redis 滑动窗口或令牌桶。

⸻

4. API 定义（外部接口）

4.1 登录（Login）

POST /auth/login

请求：

{
  "username": "alice",
  "password": "123456",
  "mfa_code": null,
  "device_id": "ios-xxx"
}

响应：

{
  "access_token": "jwt...",
  "refresh_token": "xxx",
  "expires_in": 900,
  "token_type": "Bearer",
  "session": {
    "sid": "sess_xxx",
    "expires_at": "2025-01-01T12:34:56Z"
  }
  "user":  {
    role: 'admin',
    roleId: '1',
    permissions: ['*.*.*']
  }
}


⸻

4.2 刷新令牌（Token Refresh）

POST /auth/refresh

请求：

{
  "refresh_token": "xxxx",
  "device_id": "ios-xxx"
}

响应与 login 相同。

⸻

4.3 登出（Logout）

POST /auth/logout
Authorization: Bearer <access_token>

行为：
	•	access_token.jti → 黑名单
	•	refresh_token.jti → 黑名单
	•	会话 session 关闭

⸻

4.4 权限测试（Policy Test）

POST /auth/perm-check

请求：

{
  "resource": "user",
  "action": "read"
}


⸻

5. 数据模型

5.1 PostgreSQL 结构（简化）

用户表

id BIGSERIAL PK
username CITEXT UNIQUE
email CITEXT UNIQUE
password_hash TEXT
is_active BOOLEAN
mfa_secret TEXT
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ

角色

id BIGSERIAL PK
code TEXT UNIQUE
name TEXT
created_at TIMESTAMPTZ

用户-角色

user_id BIGINT
role_id BIGINT
PRIMARY KEY (user_id, role_id)

权限策略

id BIGSERIAL PK
effect 'allow' | 'deny'
resource TEXT
action TEXT
condition JSONB

角色-权限

role_id BIGINT
perm_id BIGINT
PRIMARY KEY (role_id, perm_id)

审计日志

id BIGSERIAL PK
event_type TEXT
user_id BIGINT
ip TEXT
ua TEXT
resource TEXT
action TEXT
status TEXT
detail JSONB
ts TIMESTAMPTZ


⸻

6. Redis Key 规范

Key	示例	用途
sess:{sid}	sess:abc123	保存会话信息
jti:black:{jti}	jti:black:xxx	JWT 黑名单
rt:{hash}	rt:lkj4j32	Refresh Token 状态
rl:login:{ip}	rl:login:1.2.3.4	登录限流
rbac:user:{id}	rbac:user:1001	用户权限缓存


⸻

7. 登录流程（Sequence）

Client → /auth/login
    → RateLimitAgent 检查
    → IdentityAgent 校验账号密码
        如果需要 MFA → 返回 “MFA_REQUIRED”
    → TokenAgent 生成 access/refresh
    → SessionAgent 创建 session
    → AuditAgent 记录登录成功
    → 返回 token + session

刷新令牌流程：

Client → /auth/refresh
    → RateLimitAgent
    → TokenAgent 验证 refresh_token
    → TokenAgent 旋转 refresh_token
    → SessionAgent 更新 session
    → 审计
    → 返回新 token

权限判定流程：

Gateway → JWT 解码 → 将 user_id 注入
Handler → Depends(require_perm('user','list'))
    → RBACAgent 加载缓存 or 数据库
    → 判定 → allow/deny


⸻

8. 安全规范（Security Baseline）
	•	密码使用 argon2id 或 bcrypt $12+
	•	JWT 使用 RS256（推荐）并使用 kid 轮换
	•	Refresh Token 必须 单次有效（rotate）
	•	所有敏感行为审计
	•	账号锁定策略（例如 5 分钟 5 次失败）
	•	CSRF 仅在使用 Cookie 模式时启用
	•	CORS 限制来源
	•	所有 API 返回规范错误码：

code	http	含义
AUTH.INVALID_CREDENTIAL	401	密码错误
AUTH.MFA_REQUIRED	401	需要 MFA
AUTH.TOKEN_EXPIRED	401	access_token 过期
AUTH.REFRESH_INVALID	401	refresh_token 失效
AUTH.FORBIDDEN	403	权限不足
AUTH.RATE_LIMIT	429	限流


⸻

9. 可观测性（Observability）
	•	OpenTelemetry Trace：trace_id 注入所有日志
	•	Prometheus Metrics：
	•	auth_login_success_total
	•	auth_login_fail_total
	•	auth_refresh_total
	•	rbac_cache_hit/miss_total
	•	http_request_duration_ms
	•	审计日志落 PostgreSQL（可用于合规）

⸻

10. 目录结构（建议）

project/
│
├── app/
│   ├── main.py
│   ├── routers/
│   │   ├── auth.py
│   │   └── user.py
│   ├── agents/
│   │   ├── orchestrator.py
│   │   ├── identity.py
│   │   ├── token.py
│   │   ├── rbac.py
│   │   ├── session.py
│   │   ├── audit.py
│   │   └── ratelimit.py
│   ├── core/
│   │   ├── database.py
│   │   ├── redis.py
│   │   ├── settings.py
│   │   ├── security.py
│   │   └── errors.py
│   └── models/
│       ├── user.py
│       ├── role.py
│       ├── policy.py
│       └── audit.py
│
├── tests/
├── pyproject.toml
└── AGENTS.md

11. 实现建议（Implementation Notes）
	•	使用 uvicorn + uvloop + httptools 获得最大性能
	•	SQLAlchemy async + asyncpg
	•	Redis 连接池 ≥ 50
	•	JWT 尽量不查数据库（依赖 claims + redis 黑名单）
	•	RBAC 使用 Redis 版本号实现缓存自动失效
	•	Token 旋转时必须立即写黑名单旧 refresh_jti
	•	对 API 响应时间 P99 目标：< 20ms

⸻

12. 后续扩展
	•	支持 OIDC / SAML 企业级单点登录
	•	加入 ABAC（基于属性的授权）
	•	会话地理位置漂移检测（IP/地理位置）
	•	添加 Webhook（登录、权限变更事件推送）
	•	租户隔离（TenantID + RBAC 分区）
