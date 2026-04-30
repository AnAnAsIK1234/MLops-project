## Запуск

```bash
cp app/.env.example app/.env
docker compose up --build
```

API будет доступен тут:

```text
http://localhost:8001
```

Документация FastAPI:

```text
http://localhost:8001/api/docs
```

RabbitMQ UI:

```text
http://localhost:15673
```

Логин/пароль RabbitMQ по умолчанию:

```text
guest / guest
```

При первом запуске Ollama скачивает модель из `app/.env`, поэтому старт может быть не быстрым.

## Проверка

```bash
curl http://localhost:8001/health
```

Ответ:

```json
{"status":"ok"}
```

## Регистрация

```bash
curl -X POST http://localhost:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{"login":"bob","password":"secret123"}'
```

## Логин

```bash
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"login":"bob","password":"secret123"}'
```

В ответе будет `access_token`. Дальше его надо передавать в заголовке:

```bash
TOKEN="сюда_вставить_access_token"
```

## Мой пользователь

```bash
curl http://localhost:8001/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

## Баланс

Посмотреть баланс:

```bash
curl http://localhost:8001/balance/ \
  -H "Authorization: Bearer $TOKEN"
```

Пополнить баланс:

```bash
curl -X POST http://localhost:8001/balance/top-up \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount":10,"description":"test top up"}'
```

История операций по балансу:

```bash
curl http://localhost:8001/balance/transactions \
  -H "Authorization: Bearer $TOKEN"
```

## Модели

```bash
curl http://localhost:8001/models/ \
  -H "Authorization: Bearer $TOKEN"
```

Из ответа нужен `id` модели:

```bash
MODEL_ID="сюда_вставить_id_модели"
```

## Запрос на предсказание через форму

```bash
curl -X POST http://localhost:8001/predict/form \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id":"'"$MODEL_ID"'",
    "prompt":"Hey, how are you?"
  }'
```

Пример ответа:

```json
{
  "task_id": "uuid",
  "status": "pending",
  "processed_count": 1,
  "rejected_count": 0,
  "charged_credits": null,
  "validation_errors": []
}
```

## Проверка результата

```bash
TASK_ID="сюда_вставить_task_id"

curl http://localhost:8001/predict/$TASK_ID \
  -H "Authorization: Bearer $TOKEN"
```

Пока задача не обработана, статус будет `pending` или `processing`.
После обработки будет `success` или `failed`.

## Запрос через CSV-файл

Файл должен содержать колонку `prompt`.

```bash
cat > prompts.csv <<'CSV'
prompt
Make a predict
Explain possible risks
CSV
```

```bash
curl -X POST http://localhost:8001/predict/file \
  -H "Authorization: Bearer $TOKEN" \
  -F "model_id=$MODEL_ID" \
  -F "file=@prompts.csv"
```

Если в CSV есть пустые строки, они попадут в `validation_errors`, но валидные строки всё равно уйдут в обработку.

## История

Общая история:

```bash
curl http://localhost:8001/history/ \
  -H "Authorization: Bearer $TOKEN"
```

История предсказаний:

```bash
curl http://localhost:8001/history/predictions \
  -H "Authorization: Bearer $TOKEN"
```

События по конкретной задаче:

```bash
curl http://localhost:8001/history/predictions/$TASK_ID \
  -H "Authorization: Bearer $TOKEN"
```

## Веб-страницы

```text
http://localhost:8001/
http://localhost:8001/register
http://localhost:8001/login
http://localhost:8001/dashboard
http://localhost:8001/balance-page
http://localhost:8001/predict-page
http://localhost:8001/history-page
```

## Логи воркеров

```bash
docker compose logs -f worker-1 worker-2
```

## Тесты

```bash
docker compose exec api pytest -q
```

## Остановка

```bash
docker compose down
```

С удалением данных:

```bash
docker compose down -v
```
