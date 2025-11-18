-- ============================================================================
-- PostgreSQL Database Schema for FastAPI Admin Service
-- ============================================================================
-- 数据库建表脚本
-- 推荐执行顺序：
--   1. 如需重建，请运行 drop_all.sql（会清空所有对象）
--   2. 执行此文件创建表结构
--   3. 执行 seed.sql 插入测试数据
-- ============================================================================

-- ============================================================================
-- 启用扩展
-- ============================================================================
CREATE EXTENSION IF NOT EXISTS citext;

-- ============================================================================
-- 创建枚举类型
-- ============================================================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'menu_type') THEN
        CREATE TYPE menu_type AS ENUM ('directory', 'route', 'action');
        COMMENT ON TYPE menu_type IS '菜单类型：directory-目录, route-路由, action-操作';
    END IF;
END$$;

-- ============================================================================
-- 部门表
-- ============================================================================
CREATE TABLE departments (
    id          BIGSERIAL PRIMARY KEY,
    parent_id   BIGINT REFERENCES departments(id) ON DELETE SET NULL,
    name        VARCHAR(128) NOT NULL,
    remark      TEXT,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    "order"     INT NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE departments IS '部门表：支持树形结构的组织架构';
COMMENT ON COLUMN departments.id IS '部门ID，主键';
COMMENT ON COLUMN departments.parent_id IS '父部门ID，NULL表示顶级部门';
COMMENT ON COLUMN departments.name IS '部门名称';
COMMENT ON COLUMN departments.remark IS '备注说明';
COMMENT ON COLUMN departments.is_active IS '是否启用';
COMMENT ON COLUMN departments."order" IS '排序序号，数字越小越靠前';
COMMENT ON COLUMN departments.created_at IS '创建时间';
COMMENT ON COLUMN departments.updated_at IS '更新时间';

CREATE INDEX idx_departments_parent ON departments(parent_id) WHERE parent_id IS NOT NULL;

-- ============================================================================
-- 用户表
-- ============================================================================
CREATE TABLE users (
    id              BIGSERIAL PRIMARY KEY,
    username        CITEXT UNIQUE NOT NULL,
    email           CITEXT UNIQUE,
    full_name       VARCHAR(128),
    password_hash   VARCHAR(255) NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    is_superuser    BOOLEAN NOT NULL DEFAULT FALSE,
    mfa_secret      VARCHAR(64),
    locked_until    TIMESTAMPTZ,
    attributes      JSONB DEFAULT '{}'::JSONB,
    department_id   BIGINT REFERENCES departments(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE users IS '用户表：系统用户信息';
COMMENT ON COLUMN users.id IS '用户ID，主键';
COMMENT ON COLUMN users.username IS '用户名，唯一，不区分大小写';
COMMENT ON COLUMN users.email IS '邮箱地址，唯一，不区分大小写';
COMMENT ON COLUMN users.full_name IS '用户全名/昵称';
COMMENT ON COLUMN users.password_hash IS '密码哈希值（bcrypt/argon2）';
COMMENT ON COLUMN users.is_active IS '是否启用，禁用后无法登录';
COMMENT ON COLUMN users.is_superuser IS '是否超级管理员，拥有所有权限';
COMMENT ON COLUMN users.mfa_secret IS 'MFA密钥（TOTP）';
COMMENT ON COLUMN users.locked_until IS '账户锁定截止时间，NULL表示未锁定';
COMMENT ON COLUMN users.attributes IS '扩展属性，JSON格式存储额外信息';
COMMENT ON COLUMN users.department_id IS '所属部门ID';
COMMENT ON COLUMN users.created_at IS '创建时间';
COMMENT ON COLUMN users.updated_at IS '更新时间';

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email) WHERE email IS NOT NULL;
CREATE INDEX idx_users_department ON users(department_id) WHERE department_id IS NOT NULL;
CREATE INDEX idx_users_is_active ON users(is_active) WHERE is_active = TRUE;

-- ============================================================================
-- 角色表
-- ============================================================================
CREATE TABLE roles (
    id          BIGSERIAL PRIMARY KEY,
    code        VARCHAR(64) UNIQUE NOT NULL,
    name        VARCHAR(128) UNIQUE NOT NULL,
    description TEXT,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE roles IS '角色表：RBAC角色定义';
COMMENT ON COLUMN roles.id IS '角色ID，主键';
COMMENT ON COLUMN roles.code IS '角色代码，唯一标识，如：admin, user, guest';
COMMENT ON COLUMN roles.name IS '角色名称，唯一，如：管理员、普通用户';
COMMENT ON COLUMN roles.description IS '角色描述';
COMMENT ON COLUMN roles.is_active IS '是否启用';
COMMENT ON COLUMN roles.created_at IS '创建时间';
COMMENT ON COLUMN roles.updated_at IS '更新时间';

CREATE INDEX idx_roles_code ON roles(code);
CREATE INDEX idx_roles_is_active ON roles(is_active) WHERE is_active = TRUE;

-- ============================================================================
-- 用户角色关联表
-- ============================================================================
CREATE TABLE user_roles (
    id         BIGSERIAL PRIMARY KEY,
    user_id    BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id    BIGINT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, role_id)
);

COMMENT ON TABLE user_roles IS '用户角色关联表：多对多关系';
COMMENT ON COLUMN user_roles.id IS '记录ID';
COMMENT ON COLUMN user_roles.user_id IS '用户ID';
COMMENT ON COLUMN user_roles.role_id IS '角色ID';
COMMENT ON COLUMN user_roles.created_at IS '关联创建时间';

CREATE INDEX idx_user_roles_user ON user_roles(user_id);
CREATE INDEX idx_user_roles_role ON user_roles(role_id);

-- ============================================================================
-- 权限表
-- ============================================================================
CREATE TABLE permissions (
    id          BIGSERIAL PRIMARY KEY,
    namespace   VARCHAR(64) NOT NULL DEFAULT 'system',
    resource    VARCHAR(64) NOT NULL,
    action      VARCHAR(64) NOT NULL,
    label       VARCHAR(128),
    menu_id     BIGINT,
    effect      VARCHAR(10) NOT NULL DEFAULT 'allow' CHECK (effect IN ('allow', 'deny')),
    condition   JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (namespace, resource, action)
);

COMMENT ON TABLE permissions IS '权限表：RBAC权限定义，格式：namespace:resource:action';
COMMENT ON COLUMN permissions.id IS '权限ID，主键';
COMMENT ON COLUMN permissions.namespace IS '命名空间，如：system, example，*表示所有';
COMMENT ON COLUMN permissions.resource IS '资源，如：user, role, menu，*表示所有';
COMMENT ON COLUMN permissions.action IS '操作，如：create, read, update, delete, list，*表示所有';
COMMENT ON COLUMN permissions.label IS '权限标签/描述';
COMMENT ON COLUMN permissions.menu_id IS '所属菜单ID，NULL 表示独立权限';
COMMENT ON COLUMN permissions.effect IS '权限效果：allow-允许, deny-拒绝';
COMMENT ON COLUMN permissions.condition IS '权限条件，JSON格式，用于ABAC动态权限';
COMMENT ON COLUMN permissions.created_at IS '创建时间';
COMMENT ON COLUMN permissions.updated_at IS '更新时间';

CREATE INDEX idx_permissions_resource ON permissions(namespace, resource, action);
CREATE INDEX idx_permissions_effect ON permissions(effect) WHERE effect = 'allow';

-- ============================================================================
-- 角色权限关联表
-- ============================================================================
CREATE TABLE role_permissions (
    id             BIGSERIAL PRIMARY KEY,
    role_id        BIGINT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id  BIGINT NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (role_id, permission_id)
);

COMMENT ON TABLE role_permissions IS '角色权限关联表：多对多关系';
COMMENT ON COLUMN role_permissions.id IS '记录ID';
COMMENT ON COLUMN role_permissions.role_id IS '角色ID';
COMMENT ON COLUMN role_permissions.permission_id IS '权限ID';
COMMENT ON COLUMN role_permissions.created_at IS '关联创建时间';

CREATE INDEX idx_role_permissions_role ON role_permissions(role_id);
CREATE INDEX idx_role_permissions_permission ON role_permissions(permission_id);

-- ============================================================================
-- 菜单表
-- ============================================================================
CREATE TABLE menus (
    id              BIGSERIAL PRIMARY KEY,
    parent_id       BIGINT REFERENCES menus(id) ON DELETE SET NULL,
    name            VARCHAR(128) UNIQUE NOT NULL,
    title           VARCHAR(128) NOT NULL,
    title_i18n      VARCHAR(128),
    path            VARCHAR(255) NOT NULL,
    component       VARCHAR(255),
    redirect        VARCHAR(255),
    "order"         INT NOT NULL DEFAULT 0,
    icon            VARCHAR(128),
    type            menu_type NOT NULL DEFAULT 'route',
    is_external     BOOLEAN NOT NULL DEFAULT FALSE,
    always_show     BOOLEAN NOT NULL DEFAULT FALSE,
    keep_alive      BOOLEAN NOT NULL DEFAULT TRUE,
    affix           BOOLEAN NOT NULL DEFAULT FALSE,
    hidden          BOOLEAN NOT NULL DEFAULT FALSE,
    enabled         BOOLEAN NOT NULL DEFAULT TRUE,
    active_menu     VARCHAR(255),
    show_breadcrumb BOOLEAN NOT NULL DEFAULT TRUE,
    no_tags_view    BOOLEAN NOT NULL DEFAULT FALSE,
    can_to          BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE menus IS '菜单表：前端路由菜单配置，支持树形结构';
COMMENT ON COLUMN menus.id IS '菜单ID，主键';
COMMENT ON COLUMN menus.parent_id IS '父菜单ID，NULL表示顶级菜单';
COMMENT ON COLUMN menus.name IS '菜单名称（路由name），唯一标识';
COMMENT ON COLUMN menus.title IS '菜单标题（显示名称）';
COMMENT ON COLUMN menus.title_i18n IS '国际化key，如：router.dashboard';
COMMENT ON COLUMN menus.path IS '路由路径，如：/dashboard/analysis';
COMMENT ON COLUMN menus.component IS '组件路径，如：views/Dashboard/Analysis';
COMMENT ON COLUMN menus.redirect IS '重定向路径';
COMMENT ON COLUMN menus."order" IS '排序序号，数字越小越靠前';
COMMENT ON COLUMN menus.icon IS '图标，如：vi-ant-design:dashboard-filled';
COMMENT ON COLUMN menus.type IS '菜单类型：directory-目录, route-路由, action-操作';
COMMENT ON COLUMN menus.is_external IS '是否外部链接';
COMMENT ON COLUMN menus.always_show IS '是否总是显示（有子菜单时）';
COMMENT ON COLUMN menus.keep_alive IS '是否缓存页面（keep-alive）';
COMMENT ON COLUMN menus.affix IS '是否固定在标签页';
COMMENT ON COLUMN menus.hidden IS '是否隐藏（不在菜单中显示）';
COMMENT ON COLUMN menus.enabled IS '是否启用';
COMMENT ON COLUMN menus.active_menu IS '激活的菜单路径（用于高亮）';
COMMENT ON COLUMN menus.show_breadcrumb IS '是否显示面包屑';
COMMENT ON COLUMN menus.no_tags_view IS '是否不在标签页显示';
COMMENT ON COLUMN menus.can_to IS '是否可以跳转';
COMMENT ON COLUMN menus.created_at IS '创建时间';
COMMENT ON COLUMN menus.updated_at IS '更新时间';

CREATE INDEX idx_menus_parent ON menus(parent_id) WHERE parent_id IS NOT NULL;
CREATE INDEX idx_menus_name ON menus(name);
CREATE INDEX idx_menus_enabled ON menus(enabled) WHERE enabled = TRUE;
CREATE INDEX idx_menus_type ON menus(type);

ALTER TABLE permissions
    ADD CONSTRAINT fk_permissions_menu
    FOREIGN KEY (menu_id) REFERENCES menus(id) ON DELETE CASCADE;

-- ============================================================================
-- 角色菜单关联表
-- ============================================================================
CREATE TABLE role_menus (
    id         BIGSERIAL PRIMARY KEY,
    role_id    BIGINT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    menu_id    BIGINT NOT NULL REFERENCES menus(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (role_id, menu_id)
);

COMMENT ON TABLE role_menus IS '角色菜单关联表：多对多关系，控制角色可访问的菜单';
COMMENT ON COLUMN role_menus.id IS '记录ID';
COMMENT ON COLUMN role_menus.role_id IS '角色ID';
COMMENT ON COLUMN role_menus.menu_id IS '菜单ID';
COMMENT ON COLUMN role_menus.created_at IS '关联创建时间';

CREATE INDEX idx_role_menus_role ON role_menus(role_id);
CREATE INDEX idx_role_menus_menu ON role_menus(menu_id);


-- ============================================================================
-- 审计日志表
-- ============================================================================
CREATE TABLE audit_log (
    id              BIGSERIAL PRIMARY KEY,
    trace_id        VARCHAR(64) NOT NULL,
    operator_id     BIGINT,
    operator_name   VARCHAR(128),
    action          VARCHAR(128) NOT NULL,
    resource_type   VARCHAR(128),
    resource_id     VARCHAR(128),
    request_ip      VARCHAR(64),
    user_agent      VARCHAR(512),
    before_state    JSONB,
    after_state     JSONB,
    params          JSONB,
    result_status   SMALLINT NOT NULL DEFAULT 1 CHECK (result_status IN (0, 1)),
    result_message  VARCHAR(500),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE audit_log IS '审计日志表：记录所有敏感操作和权限检查';
COMMENT ON COLUMN audit_log.id IS '日志ID，主键';
COMMENT ON COLUMN audit_log.trace_id IS '追踪ID，用于关联同一请求的多个操作';
COMMENT ON COLUMN audit_log.operator_id IS '操作人ID';
COMMENT ON COLUMN audit_log.operator_name IS '操作人用户名';
COMMENT ON COLUMN audit_log.action IS '操作类型，如：LOGIN, LOGOUT, USER_CREATE, PERMISSION_DENIED';
COMMENT ON COLUMN audit_log.resource_type IS '资源类型，如：USER, ROLE, MENU';
COMMENT ON COLUMN audit_log.resource_id IS '资源ID';
COMMENT ON COLUMN audit_log.request_ip IS '请求IP地址';
COMMENT ON COLUMN audit_log.user_agent IS '用户代理（浏览器信息）';
COMMENT ON COLUMN audit_log.before_state IS '操作前状态，JSON格式';
COMMENT ON COLUMN audit_log.after_state IS '操作后状态，JSON格式';
COMMENT ON COLUMN audit_log.params IS '请求参数，JSON格式';
COMMENT ON COLUMN audit_log.result_status IS '操作结果：1-成功, 0-失败';
COMMENT ON COLUMN audit_log.result_message IS '结果消息/错误信息';
COMMENT ON COLUMN audit_log.created_at IS '创建时间（操作时间）';

CREATE INDEX idx_audit_log_trace ON audit_log(trace_id);
CREATE INDEX idx_audit_log_operator ON audit_log(operator_id) WHERE operator_id IS NOT NULL;
CREATE INDEX idx_audit_log_action ON audit_log(action);
CREATE INDEX idx_audit_log_resource ON audit_log(resource_type, resource_id) WHERE resource_type IS NOT NULL;
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at DESC);
CREATE INDEX idx_audit_log_result_status ON audit_log(result_status);

-- ============================================================================
-- 表结构创建完成
-- ============================================================================
