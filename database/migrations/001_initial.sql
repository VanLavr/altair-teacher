-- Все таблицы одной общей базы orders_db.
-- Миграция выполняется администратором, без участия сервисов.
-- IF NOT EXISTS позволяет принять существующую учебную схему первой версии.
-- order_id связывает этапы логически; сервисы общаются через HTTP.

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    price INTEGER NOT NULL CHECK (price >= 0),
    status VARCHAR(50) NOT NULL CHECK (status IN ('processing', 'completed', 'failed'))
);

CREATE TABLE IF NOT EXISTS reservations (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL CHECK (order_id > 0),
    product_name VARCHAR(255) NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    amount INTEGER NOT NULL CHECK (amount >= 0),
    status VARCHAR(50) NOT NULL CHECK (status IN ('reserved', 'rejected'))
);

CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL CHECK (order_id > 0),
    amount INTEGER NOT NULL CHECK (amount >= 0),
    status VARCHAR(50) NOT NULL CHECK (status IN ('paid', 'failed'))
);

CREATE TABLE IF NOT EXISTS deliveries (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL CHECK (order_id > 0),
    address VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL CHECK (status IN ('ready', 'failed'))
);

CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL CHECK (order_id > 0),
    message VARCHAR(500) NOT NULL,
    status VARCHAR(50) NOT NULL CHECK (status IN ('sent', 'failed'))
);
