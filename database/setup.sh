#!/usr/bin/env bash
# Единственная точка подготовки общей БД для всех пяти сервисов.
# Можно запускать из любого каталога: пути вычисляются относительно скрипта.
set -euo pipefail
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
container="${DB_CONTAINER:-school-orders-postgres}"

# Запуск PostgreSQL и административная инициализация выполняются отдельно
# от приложений. Ни один сервис не запускает этот скрипт при старте.
bash "$script_dir/postgres.sh"
docker exec -i "$container" psql -U postgres -d postgres -v ON_ERROR_STOP=1 \
    < "$script_dir/bootstrap.sql"

# Имена файлов определяют порядок: 001_initial.sql, 002_*.sql, ...
# Одна миграция = одна транзакция. Ошибка откатывает и DDL, и запись версии.
# Блокировка защищает от одновременного применения миграции двумя запусками.
for migration_file in "$script_dir"/migrations/*.sql; do
    version=$(basename -- "$migration_file")
    if [[ ! "$version" =~ ^[0-9]{3}_[a-z0-9_]+\.sql$ ]]; then
        echo "Некорректное имя миграции: $version" >&2
        exit 1
    fi
    {
        cat <<'SQL'
BEGIN;
SELECT pg_advisory_xact_lock(734821);
SELECT EXISTS (
    SELECT FROM infrastructure.schema_migrations WHERE version = :'migration'
) AS already_applied
\gset
\if :already_applied
    \echo Миграция уже применена: :migration
\else
SQL
        cat "$migration_file"
        cat <<'SQL'
INSERT INTO infrastructure.schema_migrations (version) VALUES (:'migration');
\endif
COMMIT;
SQL
    } | docker exec -i "$container" psql -U postgres -d orders_db \
        -v ON_ERROR_STOP=1 -v "migration=$version"
done

echo "Общая база orders_db готова для всех сервисов."
