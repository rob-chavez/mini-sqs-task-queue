from pathlib import Path
from typing import Optional

from botocore.exceptions import ClientError

from mini_sqs_task_queue.config import get_settings
from mini_sqs_task_queue.sqs_client import create_sqs_client


ENV_FILE = Path(".env")


def main() -> None:
    settings = get_settings()
    sqs = create_sqs_client()

    queue_url = settings.queue_url or _get_queue_url(sqs, settings.queue_name)
    dlq_url = settings.dlq_url or _get_queue_url(sqs, settings.dlq_name)

    print("SQS cleanup plan")
    print(f"Region: {settings.aws_region}")
    print(f"Main queue URL: {queue_url or 'not found'}")
    print(f"Dead-letter queue URL: {dlq_url or 'not found'}")
    print()
    print("This command is dry-run only by default.")
    print("Run with --confirm-delete to delete both queues.")


def delete_queues(confirm_delete: bool = False) -> None:
    settings = get_settings()
    sqs = create_sqs_client()

    queue_url = settings.queue_url or _get_queue_url(sqs, settings.queue_name)
    dlq_url = settings.dlq_url or _get_queue_url(sqs, settings.dlq_name)

    if not confirm_delete:
        main()
        return

    for label, queue_url in [
        ("main queue", queue_url),
        ("dead-letter queue", dlq_url),
    ]:
        if queue_url is None:
            print(f"Skipping {label}: queue URL was not found.")
            continue

        _delete_queue(sqs, label, queue_url)

    _clear_env_queue_urls()


def _get_queue_url(sqs, queue_name: str) -> Optional[str]:
    try:
        return sqs.get_queue_url(QueueName=queue_name)["QueueUrl"]
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code")
        if error_code in {"AWS.SimpleQueueService.NonExistentQueue", "QueueDoesNotExist"}:
            return None
        raise


def _delete_queue(sqs, label: str, queue_url: str) -> None:
    try:
        sqs.delete_queue(QueueUrl=queue_url)
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code")
        if error_code in {"AWS.SimpleQueueService.NonExistentQueue", "QueueDoesNotExist"}:
            print(f"Skipping {label}: queue no longer exists.")
            return
        raise

    print(f"Deleted {label}: {queue_url}")


def _clear_env_queue_urls() -> None:
    if not ENV_FILE.exists():
        return

    lines = []
    for line in ENV_FILE.read_text().splitlines():
        if line.startswith("SQS_QUEUE_URL="):
            lines.append("SQS_QUEUE_URL=")
        elif line.startswith("SQS_DLQ_URL="):
            lines.append("SQS_DLQ_URL=")
        else:
            lines.append(line)

    ENV_FILE.write_text("\n".join(lines) + "\n")
    print("Cleared SQS_QUEUE_URL and SQS_DLQ_URL in local .env")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Show or run cleanup for the tutorial SQS queues."
    )
    parser.add_argument(
        "--confirm-delete",
        action="store_true",
        help="Actually delete the main queue and dead-letter queue.",
    )
    args = parser.parse_args()

    delete_queues(confirm_delete=args.confirm_delete)
