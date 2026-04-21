from __future__ import annotations

import json
import time

from src.config import settings
from src.db import Base, ENGINE, session_scope
from src.processing import run_mock_prediction, validate_task_message
from src.rabbitmq import create_consumer_channel
from src.service import mark_task_failed, mark_task_processing, mark_task_success


def handle_message(ch, method, properties, body: bytes) -> None:
    task_id: str | None = None

    try:
        payload = json.loads(body.decode("utf-8"))
        task_id = payload.get("task_id")

        if task_id:
            with session_scope() as session:
                mark_task_processing(session, task_id=task_id, worker_id=settings.worker_id)

        task = validate_task_message(payload)

        print(f"[{settings.worker_id}] received task {task.task_id} with payload={payload}")

        time.sleep(settings.worker_simulated_delay_sec)
        prediction = run_mock_prediction(task)

        with session_scope() as session:
            mark_task_success(
                session,
                task_id=task.task_id,
                prediction=prediction,
                worker_id=settings.worker_id,
            )

        print(
            f"[{settings.worker_id}] finished task {task.task_id}, "
            f"prediction={prediction}"
        )

    except Exception as exc:
        print(f"[{settings.worker_id}] failed to process message: {exc}")

        if task_id:
            with session_scope() as session:
                mark_task_failed(session, task_id=task_id, worker_id=settings.worker_id)

    finally:
        ch.basic_ack(delivery_tag=method.delivery_tag)


def main() -> None:
    Base.metadata.create_all(bind=ENGINE)

    while True:
        connection = None
        try:
            connection, channel = create_consumer_channel()
            channel.basic_consume(
                queue=settings.rabbitmq_queue,
                on_message_callback=handle_message,
            )

            print(
                f"[{settings.worker_id}] waiting for messages "
                f"from queue={settings.rabbitmq_queue}"
            )

            channel.start_consuming()

        except KeyboardInterrupt:
            print(f"[{settings.worker_id}] stopped by user")
            break
        except Exception as exc:
            print(f"[{settings.worker_id}] consumer crashed: {exc}. Restarting in 3 sec...")
            time.sleep(3)
        finally:
            if connection and connection.is_open:
                connection.close()


if __name__ == "__main__":
    main()