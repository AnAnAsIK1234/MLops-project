import os
from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def index():
    return jsonify({
        "message": "the app is working using Nginx",
        "app_port": os.getenv("APP_PORT"),
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