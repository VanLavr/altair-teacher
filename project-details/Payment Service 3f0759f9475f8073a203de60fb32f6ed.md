# Payment Service

## Суть сервиса

Payment Service отвечает за обработку условной оплаты заказа.

После успешного резервирования товара Stock Service отправляет данные об оплате в Payment Service. Payment Service принимает запрос, определяет, успешна ли оплата, сохраняет результат в собственной базе данных и при успешной оплате передаёт заказ дальше в Delivery Service.

Для учебного проекта настоящая платёжная система не используется. Результат оплаты определяется простой бизнес-логикой.

Payment Service не создаёт заказы, не проверяет наличие товара и не занимается доставкой. Его задача — обработать оплату и сохранить её результат.

---

## API, которые предоставляет Payment Service

### Создание оплаты

`POST /payments`

Этот API вызывает Stock Service после успешного резервирования товара.

Request:

```
{
  "order_id": 1,
  "amount": 1000
}
```

Payment Service должен:

- принять данные об оплате;
- определить результат оплаты;
- создать запись в базе данных;
- присвоить оплате статус;
- при успешной оплате вызвать Delivery Service.

Пример успешного Response:

```
{
  "payment_id": 25,
  "order_id": 1,
  "status": "paid"
}
```

Пример Response при неуспешной оплате:

```
{
  "payment_id": 25,
  "order_id": 1,
  "status": "failed"
}
```

Допустимые статусы:

```
paid
failed
```

---

### Получение оплаты

`GET /payments/{id}`

Используется для получения информации о конкретной оплате.

Пример:

`GET /payments/25`

Response:

```
{
  "id": 25,
  "order_id": 1,
  "amount": 1000,
  "status": "paid"
}
```

---

### Получение списка оплат

`GET /payments`

Используется для просмотра всех созданных оплат.

Response:

```
[
  {
    "id": 25,
    "order_id": 1,
    "amount": 1000,
    "status": "paid"
  },
  {
    "id": 26,
    "order_id": 2,
    "amount": 7000,
    "status": "failed"
  }
]
```

---

## API, которое Payment Service вызывает

Если оплата прошла успешно, Payment Service должен вызвать Delivery Service.

`POST /deliveries`

Request:

```
{
  "order_id": 1,
  "address": "School"
}
```

Ожидаемый Response от Delivery Service:

```
{
  "delivery_id": 30,
  "order_id": 1,
  "status": "ready"
}
```

Если оплата завершилась со статусом `failed`, Delivery Service вызывать не нужно.

---

## Бизнес-логика

Для упрощения можно использовать следующее правило:

```
amount <= 5000 → paid
amount > 5000 → failed
```

Например:

```
amount = 1000
status = paid
```

А если:

```
amount = 7000
status = failed
```

---

## Таблица базы данных

Payment Service использует собственную таблицу `payments`.

| Поле | Тип | Описание |
| --- | --- | --- |
| `id` | integer | Уникальный идентификатор оплаты |
| `order_id` | integer | Идентификатор заказа из Order Service |
| `amount` | integer | Сумма оплаты |
| `status` | string | Статус оплаты |

Пример записи:

```
id: 25
order_id: 1
amount: 1000
status: paid
```

Пример в JSON:

```
{
  "id": 25,
  "order_id": 1,
  "amount": 1000,
  "status": "paid"
}
```

Таким образом, Payment Service принимает данные об оплате от Stock Service, выполняет простую проверку, сохраняет результат в своей базе данных и при успешной оплате передаёт заказ дальше в Delivery Service.