-- ============================================================================
-- Seed Data for FastAPI Admin Service
-- ============================================================================
-- 测试数据插入脚本
-- 执行顺序：先执行 schema.sql 创建表结构，再执行此文件插入测试数据
-- ============================================================================

-- ============================================================================
-- 清空现有数据（按依赖关系倒序）
-- ============================================================================
TRUNCATE TABLE audit_log RESTART IDENTITY CASCADE;
TRUNCATE TABLE role_menus RESTART IDENTITY CASCADE;
TRUNCATE TABLE role_permissions RESTART IDENTITY CASCADE;
TRUNCATE TABLE user_roles RESTART IDENTITY CASCADE;
TRUNCATE TABLE menus RESTART IDENTITY CASCADE;
TRUNCATE TABLE permissions RESTART IDENTITY CASCADE;
TRUNCATE TABLE users RESTART IDENTITY CASCADE;
TRUNCATE TABLE roles RESTART IDENTITY CASCADE;
TRUNCATE TABLE departments RESTART IDENTITY CASCADE;

-- ============================================================================
-- 插入部门数据
-- ============================================================================
INSERT INTO departments (id, parent_id, name, remark, is_active, "order", created_at, updated_at)
VALUES
    (1, NULL, '厦门总公司', '总部统筹业务', TRUE, 1, '2019-01-04 23:21:13+00', '2019-01-04 23:21:13+00'),
    (2, NULL, '北京分公司', '华北区域运营', FALSE, 2, '2013-02-20 01:43:52+00', '2013-02-20 01:43:52+00'),
    (3, NULL, '上海分公司', '华东区域枢纽', TRUE, 3, '2011-09-12 10:18:45+00', '2011-09-12 10:18:45+00'),
    (4, NULL, '福州分公司', '东南交付中心', TRUE, 4, '2016-04-08 14:32:11+00', '2016-04-08 14:32:11+00'),
    (5, NULL, '深圳分公司', '华南总部', TRUE, 5, '2018-07-02 08:12:54+00', '2018-07-02 08:12:54+00'),
    (101, 1, '研发部', '核心产品研发', TRUE, 1, '2019-06-14 09:50:01+00', '2019-06-14 09:50:01+00'),
    (102, 1, '产品部', '平台规划与设计', TRUE, 2, '2018-07-17 11:47:40+00', '2018-07-17 11:47:40+00'),
    (103, 1, '运营部', '增长与运营', FALSE, 3, '2017-06-06 18:08:25+00', '2017-06-06 18:08:25+00'),
    (201, 2, '研发部', '北京技术团队', TRUE, 1, '2015-12-23 07:58:34+00', '2015-12-23 07:58:34+00'),
    (202, 2, '产品部', '北方解决方案', FALSE, 2, '2009-04-12 00:06:20+00', '2009-04-12 00:06:20+00'),
    (203, 2, '运营部', '本地化运营', TRUE, 3, '2014-03-09 10:21:12+00', '2014-03-09 10:21:12+00'),
    (301, 3, '研发部', '工业互联网', TRUE, 1, '2012-05-18 12:10:11+00', '2012-05-18 12:10:11+00'),
    (302, 3, '市场部', '区域市场拓展', TRUE, 2, '2013-11-05 16:44:22+00', '2013-11-05 16:44:22+00'),
    (303, 3, '客服部', '客户成功中心', TRUE, 3, '2014-08-21 09:33:02+00', '2014-08-21 09:33:02+00'),
    (401, 4, '研发部', '交付与集成', TRUE, 1, '2017-10-12 15:03:33+00', '2017-10-12 15:03:33+00'),
    (402, 4, '运营部', '生态运营', TRUE, 2, '2016-01-19 19:22:47+00', '2016-01-19 19:22:47+00'),
    (403, 4, '客服部', '客户支持', TRUE, 3, '2018-02-14 07:55:18+00', '2018-02-14 07:55:18+00'),
    (501, 5, '研发部', '移动端研发', TRUE, 1, '2018-05-10 13:11:29+00', '2018-05-10 13:11:29+00'),
    (502, 5, '产品部', '海外产品', TRUE, 2, '2019-03-22 09:41:05+00', '2019-03-22 09:41:05+00'),
    (503, 5, '销售部', '大客户销售', TRUE, 3, '2017-09-30 11:26:44+00', '2017-09-30 11:26:44+00')
ON CONFLICT (id) DO UPDATE SET
    parent_id = EXCLUDED.parent_id,
    name = EXCLUDED.name,
    remark = EXCLUDED.remark,
    is_active = EXCLUDED.is_active,
    "order" = EXCLUDED."order",
    created_at = EXCLUDED.created_at,
    updated_at = EXCLUDED.updated_at;

-- ============================================================================
-- 插入角色数据
-- ============================================================================
INSERT INTO roles (id, code, name, description, is_active)
VALUES
    (1, 'admin', 'Administrator', '全量权限', TRUE),
    (2, 'test', 'Tester', '示例权限', TRUE)
ON CONFLICT (id) DO UPDATE SET
    code = EXCLUDED.code,
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    is_active = EXCLUDED.is_active;

-- ============================================================================
-- 插入用户数据
-- 密码说明：
--   admin: admin (bcrypt hash)
--   test: test (bcrypt hash)
-- ============================================================================
INSERT INTO users (id, username, email, full_name, password_hash, is_active, is_superuser, department_id)
VALUES
    (1, 'admin', 'admin@example.com', 'Admin', '$2b$12$YQd6IGjikqOMc.Bmn8U1guEnkUx8j9i7IjoIESAGOs4TGrmZMJ6uC', TRUE, TRUE, 101),
    (2, 'test', 'test@example.com', 'Tester', '$2b$12$WhhpBuP7jTV573Bt2EMXxe38Uf.YmfDNwVJjfeJCyhyxtrnt7FsfO', TRUE, FALSE, 201)
ON CONFLICT (id) DO UPDATE SET
    username = EXCLUDED.username,
    email = EXCLUDED.email,
    full_name = EXCLUDED.full_name,
    password_hash = EXCLUDED.password_hash,
    is_active = EXCLUDED.is_active,
    is_superuser = EXCLUDED.is_superuser,
    department_id = EXCLUDED.department_id;

-- ============================================================================
-- 插入菜单数据
-- ============================================================================
INSERT INTO menus (
    id, parent_id, name, title, title_i18n, path, component, redirect, "order", icon, type,
    is_external, always_show, keep_alive, affix, hidden, enabled,
    active_menu, show_breadcrumb, no_tags_view, can_to
)
VALUES
    -- 一级菜单：首页
    (1, NULL, 'Dashboard', '首页', 'router.dashboard', '/dashboard', '#', '/dashboard/analysis', 1, 'vi-ant-design:dashboard-filled', 'directory', FALSE, TRUE, TRUE, FALSE, FALSE, TRUE, NULL, TRUE, FALSE, FALSE),
    (2, 1, 'Analysis', '分析页', 'router.analysis', 'analysis', 'views/Dashboard/Analysis', NULL, 1, NULL, 'route', FALSE, FALSE, FALSE, FALSE, FALSE, TRUE, NULL, TRUE, FALSE, FALSE),
    (3, 1, 'Workplace', '工作台', 'router.workplace', 'workplace', 'views/Dashboard/Workplace', NULL, 2, NULL, 'route', FALSE, FALSE, FALSE, FALSE, FALSE, TRUE, NULL, TRUE, FALSE, FALSE),
    
    -- 一级菜单：文档
    (4, NULL, 'ExternalLink', '文档', 'router.document', '/external-link', '#', NULL, 2, 'vi-clarity:document-solid', 'directory', FALSE, FALSE, TRUE, FALSE, FALSE, TRUE, NULL, TRUE, FALSE, FALSE),
    (5, 4, 'DocumentLink', '文档', 'router.document', 'https://element-plus-admin-doc.cn/', NULL, NULL, 1, NULL, 'route', TRUE, FALSE, TRUE, FALSE, FALSE, TRUE, NULL, TRUE, FALSE, FALSE),
    
    -- 一级菜单：多级菜单示例
    (6, NULL, 'Level', '菜单', 'router.level', '/level', '#', '/level/menu1/menu1-1/menu1-1-1', 3, 'vi-carbon:skill-level-advanced', 'directory', FALSE, FALSE, TRUE, FALSE, FALSE, TRUE, NULL, TRUE, FALSE, FALSE),
    (7, 6, 'Menu1', '菜单1', 'router.menu1', 'menu1', '##', '/level/menu1/menu1-1/menu1-1-1', 1, NULL, 'directory', FALSE, FALSE, TRUE, FALSE, FALSE, TRUE, NULL, TRUE, FALSE, FALSE),
    (8, 7, 'Menu11', '菜单1-1', 'router.menu11', 'menu1-1', '##', '/level/menu1/menu1-1/menu1-1-1', 1, NULL, 'directory', FALSE, TRUE, TRUE, FALSE, FALSE, TRUE, NULL, TRUE, FALSE, FALSE),
    (9, 8, 'Menu111', '菜单1-1-1', 'router.menu111', 'menu1-1-1', 'views/Level/Menu111', NULL, 1, NULL, 'route', FALSE, FALSE, TRUE, FALSE, FALSE, TRUE, NULL, TRUE, FALSE, FALSE),
    (10, 7, 'Menu12', '菜单1-2', 'router.menu12', 'menu1-2', 'views/Level/Menu12', NULL, 2, NULL, 'route', FALSE, FALSE, TRUE, FALSE, FALSE, TRUE, NULL, TRUE, FALSE, FALSE),
    (11, 6, 'Menu2Demo', '菜单2', 'router.menu2', 'menu2', 'views/Level/Menu2', NULL, 2, NULL, 'route', FALSE, FALSE, TRUE, FALSE, FALSE, TRUE, NULL, TRUE, FALSE, FALSE),
    
    -- 一级菜单：综合示例
    (12, NULL, 'Example', '综合示例', 'router.example', '/example', '#', '/example/example-dialog', 4, 'vi-ep:management', 'directory', FALSE, TRUE, TRUE, FALSE, FALSE, TRUE, NULL, TRUE, FALSE, FALSE),
    (13, 12, 'ExampleDialog', '综合示例-弹窗', 'router.exampleDialog', 'example-dialog', 'views/Example/Dialog/ExampleDialog', NULL, 1, NULL, 'route', FALSE, FALSE, TRUE, FALSE, FALSE, TRUE, NULL, TRUE, FALSE, FALSE),
    (14, 12, 'ExamplePage', '综合示例-页面', 'router.examplePage', 'example-page', 'views/Example/Page/ExamplePage', NULL, 2, NULL, 'route', FALSE, FALSE, TRUE, FALSE, FALSE, TRUE, NULL, TRUE, FALSE, FALSE),
    (15, 12, 'ExampleAdd', '综合示例-新增', 'router.exampleAdd', 'example-add', 'views/Example/Page/ExampleAdd', NULL, 3, NULL, 'route', FALSE, FALSE, FALSE, FALSE, TRUE, TRUE, '/example/example-page', TRUE, TRUE, FALSE),
    (16, 12, 'ExampleEdit', '综合示例-编辑', 'router.exampleEdit', 'example-edit', 'views/Example/Page/ExampleEdit', NULL, 4, NULL, 'route', FALSE, FALSE, FALSE, FALSE, TRUE, TRUE, '/example/example-page', TRUE, TRUE, FALSE),
    (17, 12, 'ExampleDetail', '综合示例-详情', 'router.exampleDetail', 'example-detail', 'views/Example/Page/ExampleDetail', NULL, 5, NULL, 'route', FALSE, FALSE, FALSE, FALSE, TRUE, TRUE, '/example/example-page', TRUE, TRUE, FALSE),
    
    -- 一级菜单：系统设置
    (18, NULL, 'System', '系统设置', 'router.authorization', '/authorization', '#', '/authorization/user', 5, 'vi-eos-icons:role-binding', 'directory', FALSE, TRUE, TRUE, FALSE, FALSE, TRUE, NULL, TRUE, FALSE, FALSE),
    (19, 18, 'SystemUser', '用户管理', 'router.user', 'user', 'views/Authorization/User/User', NULL, 1, NULL, 'route', FALSE, FALSE, TRUE, FALSE, FALSE, TRUE, NULL, TRUE, FALSE, FALSE),
    (20, 18, 'SystemMenu', '菜单管理', 'router.menuManagement', 'menu', 'views/Authorization/Menu/Menu', NULL, 2, NULL, 'route', FALSE, FALSE, TRUE, FALSE, FALSE, TRUE, NULL, TRUE, FALSE, FALSE),
    (21, 18, 'SystemRole', '角色管理', 'router.role', 'role', 'views/Authorization/Role/Role', NULL, 3, NULL, 'route', FALSE, FALSE, TRUE, FALSE, FALSE, TRUE, NULL, TRUE, FALSE, FALSE),
    (22, 18, 'SystemAudit', '审计日志', 'router.audit', 'audit', 'views/Authorization/Audit/Audit', NULL, 4, NULL, 'route', FALSE, FALSE, TRUE, FALSE, FALSE, TRUE, NULL, TRUE, FALSE, FALSE);

-- ============================================================================
-- 插入权限数据（依赖菜单 ID）
-- ============================================================================
INSERT INTO permissions (id, namespace, resource, action, label, effect, menu_id)
VALUES
    (1, '*', '*', '*', 'All Access', 'allow', NULL),
    (2, 'example', 'dialog', 'create', '示例弹窗-新增', 'allow', 13),
    (3, 'example', 'dialog', 'delete', '示例弹窗-删除', 'allow', 13),
    (4, 'example', 'dialog', 'edit', '示例弹窗-编辑', 'allow', 13),
    (5, 'example', 'dialog', 'view', '示例弹窗-查看', 'allow', 13),
    (6, 'example', 'page', 'add', '综合示例-页面新增', 'allow', 14),
    (7, 'example', 'page', 'edit', '综合示例-页面编辑', 'allow', 14),
    (8, 'example', 'page', 'delete', '综合示例-页面删除', 'allow', 14),
    (9, 'example', 'page', 'view', '综合示例-页面查看', 'allow', 14),
    (10, 'dashboard', 'analysis', 'add', '分析页-新增', 'allow', 2),
    (11, 'dashboard', 'analysis', 'edit', '分析页-编辑', 'allow', 2),
    (12, 'dashboard', 'workplace', 'add', '工作台-新增', 'allow', 3),
    (13, 'dashboard', 'workplace', 'edit', '工作台-编辑', 'allow', 3),
    (14, 'dashboard', 'workplace', 'delete', '工作台-删除', 'allow', 3),
    (15, 'system', 'audit', 'list', '审计日志-列表', 'allow', 22),
    (16, 'system', 'audit', 'read', '审计日志-查看', 'allow', 22),
    (17, 'system', 'menu', 'list', '菜单-查询', 'allow', 20),
    (18, 'system', 'menu', 'create', '菜单-新增', 'allow', 20),
    (19, 'system', 'menu', 'update', '菜单-编辑', 'allow', 20),
    (20, 'system', 'menu', 'delete', '菜单-删除', 'allow', 20),
    (21, 'system', 'role', 'list', '角色-查询', 'allow', 21),
    (22, 'system', 'role', 'create', '角色-新增', 'allow', 21),
    (23, 'system', 'role', 'update', '角色-编辑', 'allow', 21),
    (24, 'system', 'role', 'delete', '角色-删除', 'allow', 21),
    (25, 'system', 'user', 'list', '用户-查询', 'allow', 19),
    (26, 'system', 'user', 'create', '用户-新增', 'allow', 19),
    (27, 'system', 'user', 'update', '用户-编辑', 'allow', 19),
    (28, 'system', 'user', 'delete', '用户-删除', 'allow', 19),
    (29, 'system', 'department', 'list', '部门-列表', 'allow', NULL),
    (30, 'system', 'department', 'users', '部门-成员', 'allow', NULL)
ON CONFLICT (namespace, resource, action) DO UPDATE SET
    label = EXCLUDED.label,
    effect = EXCLUDED.effect,
    menu_id = EXCLUDED.menu_id;


-- ============================================================================
-- 插入关联关系数据
-- ============================================================================

-- 用户角色关联
INSERT INTO user_roles (user_id, role_id)
VALUES
    (1, 1),  -- admin 用户 -> admin 角色
    (2, 2)   -- test 用户 -> test 角色
ON CONFLICT (user_id, role_id) DO NOTHING;

-- 角色权限关联
INSERT INTO role_permissions (role_id, permission_id)
VALUES
    (1, 1),  -- admin 角色 -> 所有权限 (*.*.*)
    (2, 2),   -- example:dialog:create
    (2, 3),   -- example:dialog:delete
    (2, 4),   -- example:dialog:edit
    (2, 5),   -- example:dialog:view
    (2, 6),   -- example:page:add
    (2, 7),   -- example:page:edit
    (2, 8),   -- example:page:delete
    (2, 9),   -- example:page:view
    (2, 17),  -- system:menu:list
    (2, 21),  -- system:role:list
    (2, 25),  -- system:user:list
    (2, 29),  -- system:department:list
    (2, 30)   -- system:department:users
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- 角色菜单关联
INSERT INTO role_menus (role_id, menu_id)
VALUES
    -- admin 角色拥有所有菜单
    (1, 1), (1, 2), (1, 3), (1, 4), (1, 5),
    (1, 6), (1, 7), (1, 8), (1, 9), (1, 10), (1, 11),
    (1, 12), (1, 13), (1, 14), (1, 15), (1, 16), (1, 17),
    (1, 18), (1, 19), (1, 20), (1, 21), (1, 22),
    
    -- test 角色只拥有综合示例相关菜单
    (2, 12), (2, 13), (2, 14)
ON CONFLICT (role_id, menu_id) DO NOTHING;

-- ============================================================================
-- 重置序列（确保自增ID从正确的位置开始）
-- ============================================================================
SELECT setval(pg_get_serial_sequence('departments', 'id'), COALESCE((SELECT MAX(id) FROM departments), 0) + 1, false);
SELECT setval(pg_get_serial_sequence('roles', 'id'), COALESCE((SELECT MAX(id) FROM roles), 0) + 1, false);
SELECT setval(pg_get_serial_sequence('users', 'id'), COALESCE((SELECT MAX(id) FROM users), 0) + 1, false);
SELECT setval(pg_get_serial_sequence('permissions', 'id'), COALESCE((SELECT MAX(id) FROM permissions), 0) + 1, false);
SELECT setval(pg_get_serial_sequence('menus', 'id'), COALESCE((SELECT MAX(id) FROM menus), 0) + 1, false);
SELECT setval(pg_get_serial_sequence('user_roles', 'id'), COALESCE((SELECT MAX(id) FROM user_roles), 0) + 1, false);
SELECT setval(pg_get_serial_sequence('role_permissions', 'id'), COALESCE((SELECT MAX(id) FROM role_permissions), 0) + 1, false);
SELECT setval(pg_get_serial_sequence('role_menus', 'id'), COALESCE((SELECT MAX(id) FROM role_menus), 0) + 1, false);
SELECT setval(pg_get_serial_sequence('audit_log', 'id'), COALESCE((SELECT MAX(id) FROM audit_log), 0) + 1, false);

-- ============================================================================
-- 测试数据插入完成
-- ============================================================================
-- 默认账号：
--   - admin / admin (超级管理员，拥有所有权限)
--   - test / test (测试账号，只有示例权限)
-- ============================================================================
