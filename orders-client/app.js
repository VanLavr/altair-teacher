// Клиент знает только Order Service. Всю цепочку остальных сервисов запускает backend.
const apiInput = document.querySelector("#api-url");
const orderForm = document.querySelector("#order-form");
const quantityInput = document.querySelector("#quantity");
const priceInput = document.querySelector("#price");
const feedback = document.querySelector("#feedback");
const ordersBody = document.querySelector("#orders");
const listInfo = document.querySelector("#list-info");
const details = document.querySelector("#order-details");
const money = new Intl.NumberFormat("ru-RU", { style: "currency", currency: "RUB", maximumFractionDigits: 0 });
const statuses = { processing: "Обрабатывается", completed: "Завершён", failed: "Ошибка обработки" };
const maxInteger = 2147483647;

// file:// может ограничивать localStorage, поэтому сохранение адреса необязательно.
try {
  apiInput.value = localStorage.getItem("orders-api-url") || apiInput.value;
} catch (_) { /* При недоступном хранилище используем адрес из поля. */ }

function apiUrl() {
  let value = apiInput.value.trim();
  if (!value.includes("://")) value = "http://" + value;
  let url;
  try { url = new URL(value); } catch (_) { throw new Error("Укажите адрес Order Service, например 192.168.1.10:8000."); }
  if (!["http:", "https:"].includes(url.protocol) || url.username || url.password || url.search || url.hash || url.pathname !== "/") {
    throw new Error("Укажите только адрес сервиса: http://IP:порт, без пути и параметров.");
  }
  try { localStorage.setItem("orders-api-url", url.origin); } catch (_) { /* Не мешаем запросу. */ }
  return url.origin;
}

function message(text, kind = "") {
  feedback.textContent = text;
  feedback.className = "feedback" + (kind ? " " + kind : "");
}

function errorDetail(data) {
  const detail = data?.detail;
  if (typeof detail === "string") return detail;
  // FastAPI возвращает массив ошибок валидации при HTTP 422.
  if (Array.isArray(detail)) return detail.map(item => `${item.loc.join(".")}: ${item.msg}`).join("; ");
  if (detail?.order_id) return `Заказ №${detail.order_id} сохранён, но обработка не завершилась: ${detail.message}`;
  return "Сервис вернул ошибку.";
}

async function request(baseUrl, path, payload) {
  const controller = new AbortController();
  // POST ждёт всю цепочку; таймаут браузера больше 60 секунд Order Service.
  const timer = setTimeout(() => controller.abort(), 90000);
  try {
    const response = await fetch(baseUrl + path, {
      method: payload ? "POST" : "GET",
      headers: payload ? { "Content-Type": "application/json" } : {},
      body: payload ? JSON.stringify(payload) : undefined,
      signal: controller.signal,
    });
    let data;
    try { data = await response.json(); } catch (_) { throw new Error(`Ответ HTTP ${response.status} не содержит JSON. Проверьте адрес API.`); }
    if (!response.ok) throw new Error(`HTTP ${response.status}. ${errorDetail(data)}`);
    return data;
  } catch (error) {
    if (error.name === "AbortError") throw new Error("Ожидание превысило 90 секунд. Проверьте список заказов перед повторной отправкой: заказ мог сохраниться.");
    if (error instanceof TypeError) throw new Error("Нет связи с API. Проверьте адрес, доступность сервиса, брандмауэр и CORS. Заказ мог сохраниться — проверьте список перед повторной отправкой.");
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

// Пока идёт запрос, исключаем случайный повторный POST и смену адреса API.
async function perform(action, waitingText) {
  const buttons = document.querySelectorAll("button");
  buttons.forEach(button => { button.disabled = true; });
  apiInput.disabled = true;
  message(waitingText);
  try { await action(apiUrl()); } catch (error) { message(error.message, "error"); }
  finally {
    buttons.forEach(button => { button.disabled = false; });
    apiInput.disabled = false;
  }
}

function updateTotal() {
  const total = Number(quantityInput.value) * Number(priceInput.value);
  document.querySelector("#total").textContent = Number.isFinite(total) ? money.format(total) : "—";
}
quantityInput.addEventListener("input", updateTotal);
priceInput.addEventListener("input", updateTotal);
updateTotal();

function showOrder(order) {
  // textContent отображает название товара как текст, а не исполняемый HTML.
  details.textContent = JSON.stringify(order, null, 2);
  details.hidden = false;
  document.querySelector("#order-id").value = order.id;
}

async function loadOrders(baseUrl) {
  const orders = await request(baseUrl, "/orders?limit=1000&offset=0");
  ordersBody.replaceChildren();
  for (const order of orders) {
    const row = document.createElement("tr");
    const values = [order.id, order.product_name, order.quantity, money.format(order.price), money.format(order.quantity * order.price)];
    for (const value of values) {
      const cell = document.createElement("td");
      cell.textContent = value;
      row.append(cell);
    }
    const cell = document.createElement("td");
    const badge = document.createElement("span");
    badge.className = "badge" + (Object.hasOwn(statuses, order.status) ? " " + order.status : "");
    badge.textContent = statuses[order.status] || order.status;
    cell.append(badge);
    row.append(cell);
    ordersBody.append(row);
  }
  listInfo.textContent = orders.length ? `Показано заказов: ${orders.length}. Загружаются первые 1000 записей; любой заказ можно найти по ID.` : "Заказов пока нет.";
}

orderForm.addEventListener("submit", event => {
  event.preventDefault();
  const payload = {
    product_name: document.querySelector("#product").value.trim(),
    quantity: Number(quantityInput.value),
    price: Number(priceInput.value),
  };
  if (!payload.product_name || !Number.isInteger(payload.quantity) || payload.quantity < 1 || payload.quantity > maxInteger ||
      !Number.isInteger(payload.price) || payload.price < 0 || payload.price > maxInteger || payload.quantity * payload.price > maxInteger) {
    message("Укажите непустое название, целое количество от 1 и целую цену от 0. Сумма не должна превышать 2 147 483 647.", "error");
    return;
  }
  perform(async baseUrl => {
    const order = await request(baseUrl, "/orders", payload);
    showOrder(order);
    const result = `Заказ №${order.id}: ${statuses[order.status] || order.status}.`;
    // Ошибка обновления списка не должна скрыть результат уже выполненного POST.
    try { await loadOrders(baseUrl); }
    catch (error) { message(`${result} Список обновить не удалось: ${error.message}`, "error"); return; }
    message(result, order.status === "completed" ? "success" : "error");
  }, "Обрабатываем заказ… Ожидаем прохождения всей цепочки сервисов.");
});

document.querySelector("#refresh").addEventListener("click", () => {
  perform(async baseUrl => {
    await loadOrders(baseUrl);
    message("Список обновлён.", "success");
  }, "Загружаем заказы…");
});

document.querySelector("#lookup-form").addEventListener("submit", event => {
  event.preventDefault();
  const id = Number(document.querySelector("#order-id").value);
  if (!Number.isInteger(id) || id < 1 || id > maxInteger) { message("Введите положительный целый ID заказа.", "error"); return; }
  perform(async baseUrl => {
    const order = await request(baseUrl, `/orders/${id}`);
    showOrder(order);
    message(`Заказ №${order.id}: ${statuses[order.status] || order.status}.`, order.status === "failed" ? "error" : "success");
  }, "Ищем заказ…");
});

// Старые результаты относятся к прежнему API, поэтому при смене адреса убираем их.
apiInput.addEventListener("change", () => {
  ordersBody.replaceChildren();
  details.hidden = true;
  listInfo.textContent = "Адрес изменён. Обновите список заказов.";
  message("Указан новый адрес API. Загрузите список или создайте заказ.");
});
