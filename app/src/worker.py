from __future__ import annotations

import json
import time

from database.db import Base, ENGINE, session_scope
from database.services import PredictionService
from src.config import settings
from src.rabbitmq import create_consumer_channel


def handle_message(ch, method, properties, body: bytes) -> None:
    task_id: str | None = None

    try:
        payload = json.loads(body.decode("utf-8"))
        task_id = payload.get("task_id")
        if not task_id:
            raise ValueError("Queue message does not contain task_id")

        print(f"[{settings.worker_id}] received task {task_id}")

        with session_scope() as session:
            result = PredictionService(session).run_task(
                task_id=task_id,
                worker_id=settings.worker_id,
            )

        print(
            f"[{settings.worker_id}] finished task {task_id}, "
            f"output_ref={result.output_ref}"
        )

    except Exception as exc:
        print(f"[{settings.worker_id}] failed to process message: {exc}")

        if task_id:
            try:
                with session_scope() as session:
                    PredictionService(session).fail_task(
                        task_id=task_id,
                        worker_id=settings.worker_id,
                        error_message=str(exc),
                    )
            except Exception as fail_exc:
                print(
                    f"[{settings.worker_id}] failed to mark task {task_id} as failed "
                    f"and refund credits: {fail_exc}"
                )

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
