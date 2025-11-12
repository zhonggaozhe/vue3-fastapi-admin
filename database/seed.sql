-- Seed data for FastAPI Admin backend

-- Roles
INSERT INTO roles (id, code, name, description, is_active)
VALUES
    (1, 'admin', 'Administrator', '全量权限', TRUE),
    (2, 'test', 'Tester', '示例权限', TRUE)
ON CONFLICT (id) DO UPDATE SET
    code = EXCLUDED.code,
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    is_active = EXCLUDED.is_active;

-- Users
INSERT INTO users (id, username, email, full_name, password_hash, is_active, is_superuser)
VALUES
    (1, 'admin', 'admin@example.com', 'Admin', '$2b$12$YQd6IGjikqOMc.Bmn8U1guEnkUx8j9i7IjoIESAGOs4TGrmZMJ6uC', TRUE, TRUE),
    (2, 'test', 'test@example.com', 'Tester', '$2b$12$WhhpBuP7jTV573Bt2EMXxe38Uf.YmfDNwVJjfeJCyhyxtrnt7FsfO', TRUE, FALSE)
ON CONFLICT (id) DO UPDATE SET
    username = EXCLUDED.username,
    email = EXCLUDED.email,
    full_name = EXCLUDED.full_name,
    password_hash = EXCLUDED.password_hash,
    is_active = EXCLUDED.is_active,
    is_superuser = EXCLUDED.is_superuser;

-- Permissions
INSERT INTO permissions (id, namespace, resource, action, label, effect)
VALUES
    (1, '*', '*', '*', 'All Access', 'allow'),
    (2, 'example', 'dialog', 'create', '示例弹窗-新增', 'allow'),
    (3, 'example', 'dialog', 'delete', '示例弹窗-删除', 'allow')
ON CONFLICT (id) DO UPDATE SET
    namespace = EXCLUDED.namespace,
    resource = EXCLUDED.resource,
    action = EXCLUDED.action,
    label = EXCLUDED.label,
    effect = EXCLUDED.effect;

-- Menus
INSERT INTO menus (id, parent_id, name, title, path, component, type, icon, "order", enabled, always_show)
VALUES
    (1, NULL, 'Dashboard', '首页', '/dashboard', '#', 'directory', 'vi-ant-design:dashboard-filled', 1, TRUE, TRUE),
    (2, 1, 'Analysis', '分析页', 'analysis', 'views/Dashboard/Analysis', 'route', NULL, 1, TRUE, FALSE),
    (3, 1, 'Workplace', '工作台', 'workplace', 'views/Dashboard/Workplace', 'route', NULL, 2, TRUE, FALSE),
    (4, NULL, 'ExternalLink', '文档', '/external-link', '#', 'directory', 'vi-clarity:document-solid', 2, TRUE, FALSE)
ON CONFLICT (id) DO UPDATE SET
    parent_id = EXCLUDED.parent_id,
    name = EXCLUDED.name,
    title = EXCLUDED.title,
    path = EXCLUDED.path,
    component = EXCLUDED.component,
    type = EXCLUDED.type,
    icon = EXCLUDED.icon,
    "order" = EXCLUDED."order",
    enabled = EXCLUDED.enabled,
    always_show = EXCLUDED.always_show;

INSERT INTO menu_actions (id, menu_id, code, label)
VALUES
    (1, 2, 'add', '新增'),
    (2, 2, 'edit', '编辑'),
    (3, 3, 'add', '新增'),
    (4, 3, 'edit', '编辑'),
    (5, 3, 'delete', '删除')
ON CONFLICT (id) DO UPDATE SET
    menu_id = EXCLUDED.menu_id,
    code = EXCLUDED.code,
    label = EXCLUDED.label;

-- Relations
INSERT INTO user_roles (id, user_id, role_id)
VALUES
    (1, 1, 1),
    (2, 2, 2)
ON CONFLICT (user_id, role_id) DO NOTHING;

INSERT INTO role_permissions (id, role_id, permission_id)
VALUES
    (1, 1, 1),
    (2, 2, 2),
    (3, 2, 3)
ON CONFLICT (role_id, permission_id) DO NOTHING;

INSERT INTO role_menus (id, role_id, menu_id)
VALUES
    (1, 1, 1),
    (2, 1, 2),
    (3, 1, 3),
    (4, 1, 4),
    (5, 2, 1),
    (6, 2, 2),
    (7, 2, 3)
ON CONFLICT (role_id, menu_id) DO NOTHING;
