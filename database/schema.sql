-- PostgreSQL schema for FastAPI Admin Service

CREATE EXTENSION IF NOT EXISTS citext;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'menu_type') THEN
        CREATE TYPE menu_type AS ENUM ('directory', 'route', 'action');
    END IF;
END$$;

CREATE TABLE IF NOT EXISTS users (
    id              BIGSERIAL PRIMARY KEY,
    username        CITEXT UNIQUE NOT NULL,
    email           CITEXT UNIQUE,
    full_name       TEXT,
    password_hash   TEXT NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    is_superuser    BOOLEAN NOT NULL DEFAULT FALSE,
    mfa_secret      TEXT,
    locked_until    TIMESTAMPTZ,
    attributes      JSONB DEFAULT '{}'::JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS roles (
    id          BIGSERIAL PRIMARY KEY,
    code        TEXT UNIQUE NOT NULL,
    name        TEXT UNIQUE NOT NULL,
    description TEXT,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_roles (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id     BIGINT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    UNIQUE (user_id, role_id)
);

CREATE TABLE IF NOT EXISTS permissions (
    id          BIGSERIAL PRIMARY KEY,
    namespace   TEXT NOT NULL,
    resource    TEXT NOT NULL,
    action      TEXT NOT NULL,
    label       TEXT,
    effect      TEXT NOT NULL DEFAULT 'allow',
    condition   JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS role_permissions (
    id             BIGSERIAL PRIMARY KEY,
    role_id        BIGINT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id  BIGINT NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    UNIQUE (role_id, permission_id)
);

CREATE TABLE IF NOT EXISTS menus (
    id              BIGSERIAL PRIMARY KEY,
    parent_id       BIGINT REFERENCES menus(id) ON DELETE SET NULL,
    name            TEXT UNIQUE NOT NULL,
    title           TEXT NOT NULL,
    path            TEXT NOT NULL,
    component       TEXT,
    redirect        TEXT,
    "order"         INT NOT NULL DEFAULT 0,
    icon            TEXT,
    type            menu_type NOT NULL DEFAULT 'route',
    is_external     BOOLEAN NOT NULL DEFAULT FALSE,
    always_show     BOOLEAN NOT NULL DEFAULT FALSE,
    keep_alive      BOOLEAN NOT NULL DEFAULT TRUE,
    affix           BOOLEAN NOT NULL DEFAULT FALSE,
    hidden          BOOLEAN NOT NULL DEFAULT FALSE,
    enabled         BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS menu_actions (
    id          BIGSERIAL PRIMARY KEY,
    menu_id     BIGINT NOT NULL REFERENCES menus(id) ON DELETE CASCADE,
    code        TEXT NOT NULL,
    label       TEXT NOT NULL,
    description TEXT,
    UNIQUE (menu_id, code)
);

CREATE TABLE IF NOT EXISTS role_menus (
    id          BIGSERIAL PRIMARY KEY,
    role_id     BIGINT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    menu_id     BIGINT NOT NULL REFERENCES menus(id) ON DELETE CASCADE,
    UNIQUE (role_id, menu_id)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id          BIGSERIAL PRIMARY KEY,
    event_type  TEXT NOT NULL,
    user_id     BIGINT REFERENCES users(id) ON DELETE SET NULL,
    ip          TEXT,
    ua          TEXT,
    resource    TEXT,
    action      TEXT,
    status      TEXT,
    detail      JSONB,
    ts          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
