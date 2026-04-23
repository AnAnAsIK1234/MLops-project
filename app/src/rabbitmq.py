from __future__ import annotations

import json
import time

import pika

from src.config import settings


def build_connection_parameters() -> pika.URLParameters:
    params = pika.URLParameters(settings.rabbitmq_url)
    params.heartbeat = 600
    params.blocked_connection_timeout = 300
    return params


def create_blocking_connection() -> pika.BlockingConnection:
    last_error: Exception | None = None

    for attempt in range(1, settings.rabbitmq_connection_attempts + 1):
        try:
            parameters = build_connection_parameters()
            return pika.BlockingConnection(parameters)
        except Exception as exc:
            last_error = exc
            print(
                f"[rabbitmq] connection attempt {attempt}/"
                f"{settings.rabbitmq_connection_attempts} failed: {exc}"
            )
            time.sleep(settings.rabbitmq_retry_delay_sec)

    raise RuntimeError(f"Could not connect to RabbitMQ: {last_error}")


def declare_queue(channel: pika.adapters.blocking_connection.BlockingChannel) -> None:
    channel.queue_declare(
        queue=settings.rabbitmq_queue,
        durable=settings.rabbitmq_durable,
    )


def publish_message(message: dict) -> None:
    connection = create_blocking_connection()
    try:
        channel = connection.channel()
        declare_queue(channel)

        channel.basic_publish(
            exchange=settings.rabbitmq_exchange,
            routing_key=settings.rabbitmq_routing_key,
            body=json.dumps(message, default=str).encode("utf-8"),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type="application/json",
            ),
        )
    finally:
        connection.close()


def create_consumer_channel():
    connection = create_blocking_connection()
    channel = connection.channel()
    declare_queue(channel)
    channel.basic_qos(prefetch_count=settings.worker_prefetch_count)
    return connection, channel