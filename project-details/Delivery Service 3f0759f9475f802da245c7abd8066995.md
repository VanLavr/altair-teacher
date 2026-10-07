# Delivery Service

## Суть сервиса

Delivery Service отвечает за создание доставки для успешно оплаченного заказа.

После успешной оплаты Payment Service отправляет данные о заказе в Delivery Service. Delivery Service принимает запрос, создаёт информацию о доставке, сохраняет её в собственной базе данных и передаёт информацию дальше в Notification Service.

Для учебного проекта доставка является условной. Реального расчёта маршрута, курьера или времени доставки не требуется.

Delivery Service не создаёт заказ, не проверяет наличие товара и не проводит оплату. Его задача — создать запись о доставке и передать информацию о готовом заказе следующему сервису.

---

## API, которые предоставляет Delivery Service

### Создание доставки

`POST /deliveries`

Этот API вызывает Payment Service после успешной оплаты заказа.

Request:

```
{
  "order_id": 1,
  "address": "School"
}
```

Delivery Service должен:

- принять данные о заказе;
- создать запись о доставке;
- присвоить доставке статус;
- сохранить данные в базе данных;
- вызвать Notification Service.

Пример Response:

```
{
  "delivery_id": 30,
  "order_id": 1,
  "status": "ready"
}
```

Допустимые статусы:

```
ready
failed
```

---

### Получение доставки

`GET /deliveries/{id}`

Используется для получения информации о конкретной доставке.

Пример:

`GET /deliveries/30`

Response:

```
{
  "id": 30,
  "order_id": 1,
  "address": "School",
  "status": "ready"
}
```

---

### Получение списка доставок

`GET /deliveries`

Используется для просмотра всех созданных доставок.

Response:

```
[
  {
    "id": 30,
    "order_id": 1,
    "address": "School",
    "status": "ready"
  },
  {
    "id": 31,
    "order_id": 2,
    "address": "Home",
    "status": "ready"
  }
]
```

---

## API, которое Delivery Service вызывает

После успешного создания доставки Delivery Service должен вызвать Notification Service.

`POST /notifications`

Request:

```
{
  "order_id": 1,
  "message": "Order is ready"
}
```

Ожидаемый Response от Notification Service:

```
{
  "notification_id": 45,
  "order_id": 1,
  "status": "sent"
}
```

Если доставка завершилась со статусом `failed`, Notification Service вызывать не нужно.

---

## Бизнес-логика

Для учебного проекта бизнес-логика может быть максимально простой.

Если запрос содержит `order_id` и непустой `address`, доставка считается успешно созданной:

```
address заполнен → ready
address пустой → failed
```

Например:

```
address = School
status = ready
```

Если адрес отсутствует:

```
address = ""
status = failed
```

---

## Таблица базы данных

Delivery Service использует собственную таблицу `deliveries`.

| Поле | Тип | Описание |
| --- | --- | --- |
| `id` | integer | Уникальный идентификатор доставки |
| `order_id` | integer | Идентификатор заказа |
| `address` | string | Адрес доставки |
| `status` | string | Статус доставки |

Пример записи:

```
id: 30
order_id: 1
address: School
status: ready
```

Пример в JSON:

```
{
  "id": 30,
  "order_id": 1,
  "address": "School",
  "status": "ready"
}
```

Таким образом, Delivery Service принимает данные от Payment Service, создаёт доставку, сохраняет её в собственной базе данных и передаёт информацию о заказе дальше в Notification Service.