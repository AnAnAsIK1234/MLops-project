mkdir -p app/src web-proxy rabbitmq-data postgres-data

cat > compose.yaml <<'EOF'
version: "3"

services:
  app:
    build: ./app
    env_file:
      - ./app/.env
    volumes:
      - ./app/src:/app/src
    working_dir: /app
    command: python /app/src/app.py
    expose:
      - "8000"
    depends_on:
      - database
      - rabbitmq
    restart: unless-stopped

  web-proxy:
    build: ./web-proxy
    depends_on:
      - app
    ports:
      - "80:80"
      - "443:443"
    restart: unless-stopped

  rabbitmq:
    image: rabbitmq:3-management
    ports:
      - "5672:5672"
      - "15672:15672"
    volumes:
      - ./rabbitmq-data:/var/lib/rabbitmq
    restart: unless-stopped

  database:
    image: postgres:16-alpine
    env_file:
      - ./app/.env
    volumes:
      - ./postgres-data:/var/lib/postgresql/data
    restart: unless-stopped
EOF

cat > app/Dockerfile <<'EOF'
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src

CMD ["python", "src/app.py"]
EOF

cat > app/requirements.txt <<'EOF'
Flask==3.0.3
EOF

cat > app/.env <<'EOF'
APP_PORT=8000

POSTGRES_DB=app_"/health")
def health()b-proxy/Dockerfile <<'EOF \
    mkdir -p /etc/nginx/ssl && \
    openssl req -x509 -nodes -day"

Cerver_name _;

    location / {
        proxy_pass http://app:80 X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Peader Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-F> README.md <<'EOF'
# Практическое задание №2

## Состав проекта
- app — backend-приложение
- web-й
- database — PostgreSQL

## Запуск
```bash
docker compose up --builddWORD=app_password

DB_HOST=database
DB_PORT=54m flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def index():
    return jsonify({
        "_port": os.getenv("APP_PORT"),
        "database_host": os.getenv("DB_HOST"),
        "database_port": os.getenv("DB_PORT"),
        "rabbitmq_host": os.getenv("RABBITMQ_HOST"),
        "rabbitmq_port": os.getenv("RABBITMQ_PORT")
    })


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("APP_PORT", 8000)))
EOF

cat > web-proxy/Dockerfile <<'EOF'
FROM nginx:alpine

RUN apk add --no-cache openssl && \
    mkdir -p /etc/nginx/ssl && \
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/nginx.key \
    -out /etc/nginx/ssl/nginx.crt \
 rwarded_for;
        proxy_set_header X-ForwardedEOF'
# Практическое задание №2

## Состав проекта
- app — backend-приложение
- web-proxy — reverse proxy на Nginx
- rabbitmq — брокер сообщений
- database — PostgreSQL

## Запуск
```bash
docker compose up --build   -subj "/CN=localhost"

COPY nginx.conf /etc/nginx/conf.d/default.conf
EOF

cat > web-proxy/nginx.conf <<'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://app:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 443 ssl;
    server_name _;

    ssl_certificate /etc/nginx/ssl/nginx.crt;
    ssl_certificate_key /etc/nginx/ssl/nginx.key;

    location / {
        proxy_pass http://app:8000;
        proHost $host;
	proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

cat > README.md <<'EOF'
# Практическое задание №2

## Состав проекта
- app — backend-приложение
- web-proxy — reverse proxy на Nginx
- rabbitmq — брокер сообщений
- database — PostgreSQL

## Запуск
```bash
docker compose up --build 
