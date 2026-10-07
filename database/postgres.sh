#!/usr/bin/env bash
# Запускает только PostgreSQL. Python-приложения запускаются на машине учителя.
set -euo pipefail
container="${DB_CONTAINER:-school-orders-postgres}"
port="${DB_PORT:-5433}"
bind_host="${DB_BIND_HOST:-127.0.0.1}"
volume="${DB_VOLUME:-school-orders-data}"

if docker container inspect "$container" >/dev/null 2>&1; then
    # Не трогаем случайно найденный чужой контейнер с тем же именем.
    label=$(docker inspect --format '{{index .Config.Labels "school-orders-demo"}}' "$container")
    if [[ "$label" != "true" ]]; then
        echo "Имя $container уже занято чужим контейнером. Задайте DB_CONTAINER." >&2
        exit 1
    fi
    mapped_port=$(docker inspect --format '{{(index (index .HostConfig.PortBindings "5432/tcp") 0).HostPort}}' "$container")
    if [[ "$mapped_port" != "$port" ]]; then
        echo "Контейнер создан с портом $mapped_port, а DB_PORT=$port." >&2
        exit 1
    fi
    mapped_host=$(docker inspect --format '{{(index (index .HostConfig.PortBindings "5432/tcp") 0).HostIp}}' "$container")
    if [[ "$mapped_host" != "$bind_host" ]]; then
        echo "Контейнер создан с адресом $mapped_host, а DB_BIND_HOST=$bind_host." >&2
        echo "Для смены публикации порта нужно пересоздать контейнер, сохранив volume." >&2
        exit 1
    fi
    docker start "$container" >/dev/null
else
    # --pull=never использует уже имеющийся postgres:17. Данные живут в volume,
    # поэтому остановка контейнера не удаляет учебные заказы.
    docker run --detach --pull=never --name "$container" \
        --label school-orders-demo=true \
        --env POSTGRES_USER=postgres --env POSTGRES_PASSWORD=demo-admin \
        --publish "${bind_host}:${port}:5432" \
        --mount "type=volume,source=${volume},target=/var/lib/postgresql/data" \
        postgres:17 >/dev/null
fi

# Docker start возвращается раньше, чем БД начинает принимать подключения.
for attempt in {1..60}; do
    if docker exec "$container" pg_isready --username=postgres --dbname=postgres >/dev/null 2>&1; then
        echo "PostgreSQL готов: $bind_host:$port ($container)"
        exit 0
    fi
    sleep 1
done
echo "PostgreSQL не стал доступен за 60 секунд. Проверьте docker logs $container." >&2
exit 1
