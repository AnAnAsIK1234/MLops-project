# Практическое задание №2

## Состав проекта
- app — backend-приложение
- web-proxy — reverse proxy на Nginx
- rabbitmq — брокер сообщений
- database — PostgreSQL

## Запуск
```bash
cp ./app/.env.example ./app/.env # чтобы не передавать лишнюю информацию
docker compose up --build
kek
