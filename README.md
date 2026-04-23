# MLops project with RabbitMQ and Ollama

## Start

```bash
docker compose down -v
docker compose up --build --remove-orphans -d
```

After services are up, pull the Ollama model once:

```bash
docker compose exec ollama ollama pull llama3.2:1b
```

Then initialize demo data:

```bash
curl -X POST http://localhost/init-demo
```

Check models:

```bash
curl http://localhost/models
```

## 1. Запуск проекта с Ollama

В этой версии Gemini убран. Инференс идёт через локальный сервис **Ollama** в Docker.

1. Убедись, что в `app/.env` есть настройки Ollama. Готовый файл уже приложен.
2. Запусти проект:

```bash
docker compose up --build --remove-orphans
```

Что произойдёт при первом старте:
- поднимется `ollama`
- сервис `ollama-init` автоматически выполнит `ollama pull` для модели из `OLLAMA_MODEL`
- только после этого стартуют `api` и воркеры

По умолчанию используется модель:

```env
OLLAMA_MODEL=llama3.2:1b
```

Если хочешь другую модель, поменяй `OLLAMA_MODEL` в `app/.env`.

После запуска доступны адреса:
- `http://localhost/health` через nginx web-proxy
- `http://localhost:8000/health` напрямую в api-контейнер
- `http://localhost:11434/api/tags` для проверки Ollama

Проверка:

```bash
curl http://localhost/health
curl http://localhost:8000/health
curl http://localhost:11434/api/tags
```

Инициализация демо-данных:

```bash
curl -X POST http://localhost/init-demo
```

---

## 2. Пользователи и баланс

Создать пользователя:

```bash
curl -X POST http://localhost/users   -H "Content-Type: application/json"   -d '{"login":"ivan","password_hash":"ivan_pass","role":"user"}'
```

Получить пользователя:

```bash
curl http://localhost/users/<user_id>
```

Пополнить баланс:

```bash
curl -X POST http://localhost/users/<user_id>/top-up   -H "Content-Type: application/json"   -d '{"amount":10000,"description":"manual top up"}'
```

Списать кредиты:

```bash
curl -X POST http://localhost/users/<user_id>/debit   -H "Content-Type: application/json"   -d '{"amount":30,"description":"manual debit"}'
```

---

## 3. Модели и задачи

Список моделей:

```bash
curl http://localhost/models
```

После `init-demo` по умолчанию создаются две модели:
- `ollama-sentiment`
- `ollama-summary`

Создать задачу:

```bash
curl -X POST http://localhost/predictions   -H "Content-Type: application/json"   -d '{"user_id":"<user_id>","model_id":"<model_id>","input_data":"Мне очень понравился этот фильм"}'
```

Алиас под формулировку задания тоже есть:

```bash
curl -X POST http://localhost/predict   -H "Content-Type: application/json"   -d '{"user_id":"<user_id>","model_id":"<model_id>","input_data":"Кратко объясни, зачем нужен RabbitMQ"}'
```

После создания задача публикуется в RabbitMQ, а воркер забирает её из очереди.

Проверить статус:

```bash
curl http://localhost/predictions/<task_id>
```

или:

```bash
curl http://localhost/tasks/<task_id>
```

Если задача упала, в ответе будет `error_message`.

Ручной запуск без очереди:

```bash
curl -X POST http://localhost/predictions/<task_id>/run
```

История задачи:

```bash
curl http://localhost/tasks/<task_id>/history
```

История пользователя:

```bash
curl http://localhost/users/<user_id>/history
```

---

## 4. Что исправлено

- Gemini заменён на локальный Ollama
- добавлен сервис `ollama` в `docker-compose.yaml`
- добавен `ollama-init`, который автоматически скачивает модель перед стартом API и воркеров
- RabbitMQ-пайплайн сохранён: API -> RabbitMQ -> worker -> Ollama
- при ошибке в воркере задача помечается как `failed`, а кредиты возвращаются
- при ошибке публикации в RabbitMQ кредиты тоже возвращаются
- в `GET /predictions/{task_id}` добавлен `error_message`, чтобы не смотреть причину падения только в логах
