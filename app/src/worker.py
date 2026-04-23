from __future__ import annotations

import json
import time

from database.db import session_scope
from database.services.prediction_service import PredictionService
from src.config import settings
from src.processing import run_batch_prediction
from src.rabbitmq import create_consumer_channel


def handle_message(ch, method, properties, body: bytes) -> None:
    task_id: str | None = None

    try:
        payload = json.loads(body.decode("utf-8"))
        task_id = payload.get("task_id")
        if not task_id:
            raise ValueError("task_id is required")

        with session_scope() as session:
            service = PredictionService(session)
            task = service.start_task(task_id)
            valid_records = json.loads(task.input_data)

        time.sleep(settings.worker_simulated_delay_sec)
        result_payload, summary_payload = run_batch_prediction(valid_records)

        with session_scope() as session:
            service = PredictionService(session)
            service.complete_task_success(task_id, result_payload, summary_payload)

        print(f"[{settings.worker_id}] finished task {task_id}")

    except Exception as exc:
        print(f"[{settings.worker_id}] failed to process message: {exc}")
        if task_id:
            try:
                with session_scope() as session:
                    service = PredictionService(session)
                    service.complete_task_failed(task_id, str(exc))
            except Exception as inner_exc:
                print(f"[{settings.worker_id}] failed to mark task as failed: {inner_exc}")

    finally:
        ch.basic_ack(delivery_tag=method.delivery_tag)


def main() -> None:
    while True:
        connection = None
        try:
            connection, channel = create_consumer_channel()
            channel.basic_consume(
                queue=settings.rabbitmq_queue,
                on_message_callback=handle_message,
            )

            print(f"[{settings.worker_id}] waiting for messages from queue={settings.rabbitmq_queue}")
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