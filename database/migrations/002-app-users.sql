-- Post-MVP: mobile/app user accounts (POST-04)
-- Run after 001-initial-schema.sql

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS app_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    display_name TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT app_users_email_unique UNIQUE (email)
);

CREATE INDEX IF NOT EXISTS idx_app_users_email ON app_users (LOWER(email));
