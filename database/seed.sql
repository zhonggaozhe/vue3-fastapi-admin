-- Seed data for FastAPI Admin backend

TRUNCATE TABLE role_permissions RESTART IDENTITY CASCADE;
TRUNCATE TABLE user_roles RESTART IDENTITY CASCADE;
TRUNCATE TABLE permissions RESTART IDENTITY CASCADE;
TRUNCATE TABLE users RESTART IDENTITY CASCADE;
TRUNCATE TABLE roles RESTART IDENTITY CASCADE;

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

-- Menus & Actions
TRUNCATE TABLE menu_actions RESTART IDENTITY CASCADE;
TRUNCATE TABLE menus RESTART IDENTITY CASCADE;

INSERT INTO menus (
    id, parent_id, name, title, title_i18n, path, component, redirect, "order", icon, type,
    is_external, always_show, keep_alive, affix, hidden, enabled,
    active_menu, show_breadcrumb, no_tags_view, can_to
)
VALUES
    (1, NULL, 'Dashboard', '首页', 'router.dashboard', '/dashboard', '#', '/dashboard/analysis', 1, 'vi-ant-design:dashboard-filled', 'directory', FALSE, TRUE, TRUE, FALSE, FALSE, TRUE, NULL, TRUE, FALSE, FALSE),
    (2, 1, 'Analysis', '分析页', 'router.analysis', 'analysis', 'views/Dashboard/Analysis', NULL, 1, NULL, 'route', FALSE, FALSE, FALSE, FALSE, FALSE, TRUE, NULL, TRUE, FALSE, FALSE),
    (3, 1, 'Workplace', '工作台', 'router.workplace', 'workplace', 'views/Dashboard/Workplace', NULL, 2, NULL, 'route', FALSE, FALSE, FALSE, FALSE, FALSE, TRUE, NULL, TRUE, FALSE, FALSE),
    (4, NULL, 'ExternalLink', '文档', 'router.document', '/external-link', '#', NULL, 2, 'vi-clarity:document-solid', 'directory', FALSE, FALSE, TRUE, FALSE, FALSE, TRUE, NULL, TRUE, FALSE, FALSE),
    (5, 4, 'DocumentLink', '文档', 'router.document', 'https://element-plus-admin-doc.cn/', NULL, NULL, 1, NULL, 'route', TRUE, FALSE, TRUE, FALSE, FALSE, TRUE, NULL, TRUE, FALSE, FALSE),
    (6, NULL, 'Level', '菜单', 'router.level', '/level', '#', '/level/menu1/menu1-1/menu1-1-1', 3, 'vi-carbon:skill-level-advanced', 'directory', FALSE, FALSE, TRUE, FALSE, FALSE, TRUE, NULL, TRUE, FALSE, FALSE),
    (7, 6, 'Menu1', '菜单1', 'router.menu1', 'menu1', '##', '/level/menu1/menu1-1/menu1-1-1', 1, NULL, 'directory', FALSE, FALSE, TRUE, FALSE, FALSE, TRUE, NULL, TRUE, FALSE, FALSE),
    (8, 7, 'Menu11', '菜单1-1', 'router.menu11', 'menu1-1', '##', '/level/menu1/menu1-1/menu1-1-1', 1, NULL, 'directory', FALSE, TRUE, TRUE, FALSE, FALSE, TRUE, NULL, TRUE, FALSE, FALSE),
    (9, 8, 'Menu111', '菜单1-1-1', 'router.menu111', 'menu1-1-1', 'views/Level/Menu111', NULL, 1, NULL, 'route', FALSE, FALSE, TRUE, FALSE, FALSE, TRUE, NULL, TRUE, FALSE, FALSE),
    (10, 7, 'Menu12', '菜单1-2', 'router.menu12', 'menu1-2', 'views/Level/Menu12', NULL, 2, NULL, 'route', FALSE, FALSE, TRUE, FALSE, FALSE, TRUE, NULL, TRUE, FALSE, FALSE),
    (11, 6, 'Menu2Demo', '菜单2', 'router.menu2', 'menu2', 'views/Level/Menu2', NULL, 2, NULL, 'route', FALSE, FALSE, TRUE, FALSE, FALSE, TRUE, NULL, TRUE, FALSE, FALSE),
    (12, NULL, 'Example', '综合示例', 'router.example', '/example', '#', '/example/example-dialog', 4, 'vi-ep:management', 'directory', FALSE, TRUE, TRUE, FALSE, FALSE, TRUE, NULL, TRUE, FALSE, FALSE),
    (13, 12, 'ExampleDialog', '综合示例-弹窗', 'router.exampleDialog', 'example-dialog', 'views/Example/Dialog/ExampleDialog', NULL, 1, NULL, 'route', FALSE, FALSE, TRUE, FALSE, FALSE, TRUE, NULL, TRUE, FALSE, FALSE),
    (14, 12, 'ExamplePage', '综合示例-页面', 'router.examplePage', 'example-page', 'views/Example/Page/ExamplePage', NULL, 2, NULL, 'route', FALSE, FALSE, TRUE, FALSE, FALSE, TRUE, NULL, TRUE, FALSE, FALSE),
    (15, 12, 'ExampleAdd', '综合示例-新增', 'router.exampleAdd', 'example-add', 'views/Example/Page/ExampleAdd', NULL, 3, NULL, 'route', FALSE, FALSE, FALSE, FALSE, TRUE, TRUE, '/example/example-page', TRUE, TRUE, FALSE),
    (16, 12, 'ExampleEdit', '综合示例-编辑', 'router.exampleEdit', 'example-edit', 'views/Example/Page/ExampleEdit', NULL, 4, NULL, 'route', FALSE, FALSE, FALSE, FALSE, TRUE, TRUE, '/example/example-page', TRUE, TRUE, FALSE),
    (17, 12, 'ExampleDetail', '综合示例-详情', 'router.exampleDetail', 'example-detail', 'views/Example/Page/ExampleDetail', NULL, 5, NULL, 'route', FALSE, FALSE, FALSE, FALSE, TRUE, TRUE, '/example/example-page', TRUE, TRUE, FALSE),
    (18, NULL, 'System', '系统设置', 'router.authorization', '/system', '#', '/system/user', 5, 'vi-ep:setting', 'directory', FALSE, TRUE, TRUE, FALSE, FALSE, TRUE, NULL, TRUE, FALSE, FALSE),
    (19, 18, 'SystemUser', '用户管理', 'router.user', 'user', 'views/Authorization/User/User', NULL, 1, NULL, 'route', FALSE, FALSE, TRUE, FALSE, FALSE, TRUE, NULL, TRUE, FALSE, FALSE),
    (20, 18, 'SystemMenu', '菜单管理', 'router.menuManagement', 'menu', 'views/Authorization/Menu/Menu', NULL, 2, NULL, 'route', FALSE, FALSE, TRUE, FALSE, FALSE, TRUE, NULL, TRUE, FALSE, FALSE),
    (21, 18, 'SystemRole', '角色管理', 'router.role', 'role', 'views/Authorization/Role/Role', NULL, 3, NULL, 'route', FALSE, FALSE, TRUE, FALSE, FALSE, TRUE, NULL, TRUE, FALSE, FALSE);

INSERT INTO menu_actions (id, menu_id, code, label)
VALUES
    (1, 2, 'add', '新增'),
    (2, 2, 'edit', '编辑'),
    (3, 3, 'add', '新增'),
    (4, 3, 'edit', '编辑'),
    (5, 3, 'delete', '删除'),
    (6, 13, 'add', '新增'),
    (7, 13, 'edit', '编辑'),
    (8, 13, 'delete', '删除'),
    (9, 13, 'view', '查看'),
    (10, 14, 'add', '新增'),
    (11, 14, 'edit', '编辑'),
    (12, 14, 'delete', '删除'),
    (13, 14, 'view', '查看'),
    (14, 19, 'add', '新增'),
    (15, 19, 'edit', '编辑'),
    (16, 19, 'delete', '删除'),
    (17, 19, 'view', '查看'),
    (18, 20, 'add', '新增'),
    (19, 20, 'edit', '编辑'),
    (20, 20, 'delete', '删除'),
    (21, 20, 'view', '查看'),
    (22, 21, 'add', '新增'),
    (23, 21, 'edit', '编辑'),
    (24, 21, 'delete', '删除'),
    (25, 21, 'view', '查看');

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
    (5, 1, 5),
    (6, 1, 6),
    (7, 1, 7),
    (8, 1, 8),
    (9, 1, 9),
    (10, 1, 10),
    (11, 1, 11),
    (12, 1, 12),
    (13, 1, 13),
    (14, 1, 14),
    (15, 1, 15),
    (16, 1, 16),
    (17, 1, 17),
    (18, 1, 18),
    (19, 1, 19),
    (20, 1, 20),
    (21, 1, 21),
    (22, 2, 12),
    (23, 2, 13),
    (24, 2, 14)
ON CONFLICT (role_id, menu_id) DO NOTHING;
