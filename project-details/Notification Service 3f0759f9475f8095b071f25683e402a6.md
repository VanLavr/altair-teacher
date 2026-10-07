# Notification Service

## Суть сервиса

Notification Service отвечает за формирование уведомления о завершении обработки заказа.

После успешного создания доставки Delivery Service отправляет данные в Notification Service. Notification Service принимает запрос, создаёт уведомление, сохраняет его в собственной базе данных и после этого сообщает Order Service, что заказ успешно прошёл всю цепочку обработки.

Для учебного проекта реальную отправку SMS, email или push-уведомлений реализовывать не нужно. Достаточно создать запись об уведомлении и считать его отправленным.

Notification Service не занимается заказом, резервированием товара, оплатой или доставкой. Его задача — зафиксировать уведомление и завершить общий процесс обработки заказа.

---

## API, которые предоставляет Notification Service

### Создание уведомления

`POST /notifications`

Этот API вызывает Delivery Service после успешного создания доставки.

Request:

```
{
  "order_id": 1,
  "message": "Order is ready"
}
```

Notification Service должен:

- принять данные;
- создать запись об уведомлении;
- сохранить её в базе данных;
- присвоить уведомлению статус;
- вызвать Order Service и передать ему итоговый статус заказа.

Пример Response:

```
{
  "notification_id": 45,
  "order_id": 1,
  "status": "sent"
}
```

Допустимые статусы:

```
sent
failed
```

---

### Получение уведомления

`GET /notifications/{id}`

Используется для получения информации о конкретном уведомлении.

Пример:

`GET /notifications/45`

Response:

```
{
  "id": 45,
  "order_id": 1,
  "message": "Order is ready",
  "status": "sent"
}
```

---

### Получение списка уведомлений

`GET /notifications`

Используется для просмотра всех созданных уведомлений.

Response:

```
[
  {
    "id": 45,
    "order_id": 1,
    "message": "Order is ready",
    "status": "sent"
  },
  {
    "id": 46,
    "order_id": 2,
    "message": "Order is ready",
    "status": "sent"
  }
]
```

---

## API, которое Notification Service вызывает

После успешного создания уведомления Notification Service должен вызвать Order Service и сообщить, что обработка заказа завершена.

`PATCH /orders/{id}/status`

Пример:

`PATCH /orders/1/status`

Request:

```
{
  "status": "completed"
}
```

Ожидаемый Response от Order Service:

```
{
  "id": 1,
  "status": "completed"
}
```

Если создание уведомления завершилось ошибкой, можно передать в Order Service статус:

```
{
  "status": "failed"
}
```

---

## Бизнес-логика

Для учебного проекта логика может быть максимально простой.

Если `message` не пустой, уведомление считается успешно отправленным:

```
message заполнен → sent
message пустой → failed
```

Например:

```
message = Order is ready
status = sent
```

Если сообщение отсутствует:

```
message = ""
status = failed
```

---

## Таблица базы данных

Notification Service использует собственную таблицу `notifications`.

| Поле | Тип | Описание |
| --- | --- | --- |
| `id` | integer | Уникальный идентификатор уведомления |
| `order_id` | integer | Идентификатор заказа |
| `message` | string | Текст уведомления |
| `status` | string | Статус уведомления |

Пример записи:

```
id: 45
order_id: 1
message: Order is ready
status: sent
```

Пример в JSON:

```
{
  "id": 45,
  "order_id": 1,
  "message": "Order is ready",
  "status": "sent"
}
```

Таким образом, Notification Service принимает данные от Delivery Service, создаёт уведомление, сохраняет его в собственной базе данных и после этого отправляет итоговый статус обратно в Order Service, замыкая цепочку обработки заказа.