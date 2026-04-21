# Что доступно:
* API: `http://localhost:8000`
* Swagger: `http://localhost:8000/docs`
* RabbitMQ UI: `http://localhost:15672`

## Что можно проверить

### 1. Проверка, что API запущен

curl http://localhost:8000/health


Ожидаемый ответ:

{"status":"ok"}


### 2. Отправка ML-задачи в очередь
**publisher принимает запрос, формирует задачу, публикует сообщение в RabbitMQ и возвращает `task_id`**

curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "features": {
      "x1": 1.2,
      "x2": 5.7
    },
    "model": "demo_model"
  }'


Пример ответа:

{
  "task_id": "uuid",
  "status": "queued"
}


### 3. Проверка результата обработки задачи

Подставить полученный `task_id`:

curl http://localhost:8000/tasks/<task_id>


Пример ответа после обработки:

json
{
  "task_id": "uuid",
  "model": "demo_model",
  "status": "success",
  "prediction": 3.9,
  "worker_id": "worker-1",
  "created_at": "...",
  "updated_at": "..."
}

### 4. Проверка, что работают несколько consumers

Отправить несколько задач подряд:

curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d '{"features":{"x1":1,"x2":2},"model":"demo_model"}'
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d '{"features":{"x1":2,"x2":3},"model":"demo_model"}'
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d '{"features":{"x1":3,"x2":4},"model":"demo_model"}'
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d '{"features":{"x1":4,"x2":5},"model":"demo_model"}'

Посмотреть логи воркеров:

docker compose logs -f worker-1 worker-2

По логам видно, что задачи распределяются между `worker-1` и `worker-2`.

### 5. Проверка тестов

docker compose exec api pytest -q

