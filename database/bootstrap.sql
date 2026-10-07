-- Выполняется администратором через psql, не самим приложением.
-- Повторный запуск сохраняет данные, восстанавливает пароль и права orders.
-- Пользователь приложения не является суперпользователем и не создаёт таблицы.
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'orders') THEN
        CREATE ROLE orders LOGIN PASSWORD '1234';
    END IF;
END $$;
ALTER ROLE orders WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION PASSWORD '1234';

-- CREATE DATABASE нельзя выполнять внутри транзакции DO.
-- \gexec выполняет строки SQL, возвращённые SELECT; существующие БД пропускаем.
SELECT 'CREATE DATABASE orders_db OWNER postgres'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'orders_db')
\gexec

\connect orders_db
-- История миграций — инфраструктурные данные, отдельно от таблиц проекта.
-- Приложения не управляют этой схемой и не имеют к ней доступа.
CREATE SCHEMA IF NOT EXISTS infrastructure AUTHORIZATION postgres;
CREATE TABLE IF NOT EXISTS infrastructure.schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT CONNECT ON DATABASE orders_db TO orders;
GRANT USAGE ON SCHEMA public TO orders;
-- Read + write на все текущие таблицы; sequence нужна для SERIAL при INSERT.
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO orders;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO orders;
-- Те же права для будущих таблиц, созданных администратором postgres.
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO orders;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO orders;
