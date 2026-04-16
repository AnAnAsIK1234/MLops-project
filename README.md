## 1. Запуск

1. Copy `app/.env.example` to `app/.env`
2. `docker compose up --build`
3. `http://localhost/health`

Проверить, что сервис жив:

```bash
curl http://localhost/health
```

```bash
curl -X POST http://localhost/init-demo
```

Это создаст базовые данные для проверки.

---

## 2. Протестировать работу с пользователями

### Создание пользователя

```bash
curl -X POST http://localhost/users \
  -H "Content-Type: application/json" \
  -d "{\"login\":\"ivan\",\"email\":\"ivan@example.com\",\"role\":\"user\"}"
```

**Ожидаем:**
- пользователь создался;
- вернулся `id`;
- в БД появилась запись в `users`.

### Загрузка пользователя из БД

```bash
curl http://localhost/users/<user_id>
```

**Ожидаем:**
- приходит тот же пользователь;
- у него есть связь с балансом.

---

## 3. Протестировать баланс и транзакции

### Пополнение баланса

```bash
curl -X POST http://localhost/users/<user_id>/top-up \
  -H "Content-Type: application/json" \
  -d "{\"amount\":100}"
```

**Проверка:**
- баланс увеличился;
- в `balance_transactions` появилась запись с типом пополнения.

### Списание кредитов

```bash
curl -X POST http://localhost/users/<user_id>/debit \
  -H "Content-Type: application/json" \
  -d "{\"amount\":30}"
```

**Проверка:**
- баланс уменьшился;
- в истории транзакций появилась запись на списание.

### Проверка нехватки баланса

```bash
curl -X POST http://localhost/users/<user_id>/debit \
  -H "Content-Type: application/json" \
  -d "{\"amount\":999999}"
```

**Ожидаем:**
- ошибка;
- баланс не уходит в минус;
- новая транзакция не создаётся.

---

## 5. Протестировать историю запросов пользователя

### Посмотреть список моделей

```bash
curl http://localhost/models
```

Взять `model_id`.

### Создать prediction task

```bash
curl -X POST http://localhost/predictions \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"<user_id>\",\"model_id\":\"<model_id>\",\"input_data\":\"test prompt\"}"
```

Взять `task_id`.

### Выполнить задачу

```bash
curl -X POST http://localhost/predictions/<task_id>/run
```

**Проверка:**
- задача получила статус;
- списались кредиты;
- появился результат;
- история по задаче сохранилась.

### Получить историю по задаче

```bash
curl http://localhost/tasks/<task_id>/history
```

### Получить историю пользователя

```bash
curl http://localhost/users/<user_id>/history
```
