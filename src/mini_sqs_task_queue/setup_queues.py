import json
from pathlib import Path
from typing import Dict

from botocore.exceptions import ClientError

from mini_sqs_task_queue.config import get_settings
from mini_sqs_task_queue.sqs_client import create_sqs_client


ENV_FILE = Path(".env")


def main() -> None:
    settings = get_settings()
    sqs = create_sqs_client()

    try:
        dlq_url = _ensure_queue(
            sqs,
            settings.dlq_name,
            {
                "MessageRetentionPeriod": "1209600",
            },
        )
        dlq_arn = _get_queue_arn(sqs, dlq_url)

        queue_url = _ensure_queue(
            sqs,
            settings.queue_name,
            {
                "ReceiveMessageWaitTimeSeconds": str(settings.wait_time_seconds),
                "VisibilityTimeout": str(settings.visibility_timeout),
                "RedrivePolicy": json.dumps(
                    {
                        "deadLetterTargetArn": dlq_arn,
                        "maxReceiveCount": str(settings.max_receive_count),
                    }
                ),
            },
        )
    except ClientError as exc:
        if _is_access_denied(exc):
            print("SQS setup failed because this AWS identity does not have SQS permissions.")
            print("Ask an AWS administrator for permission to create and manage these tutorial queues.")
            print(f"Region: {settings.aws_region}")
            print(f"Main queue name: {settings.queue_name}")
            print(f"Dead-letter queue name: {settings.dlq_name}")
            raise SystemExit(1) from exc
        raise

    _update_env_file(
        {
            "SQS_QUEUE_URL": queue_url,
            "SQS_DLQ_URL": dlq_url,
        }
    )

    print("SQS queues are ready")
    print(f"Region: {settings.aws_region}")
    print(f"Main queue: {settings.queue_name}")
    print(f"Main queue URL: {queue_url}")
    print(f"Dead-letter queue: {settings.dlq_name}")
    print(f"Dead-letter queue URL: {dlq_url}")
    print(f"Max receive count before DLQ: {settings.max_receive_count}")


def _ensure_queue(sqs, queue_name: str, attributes: Dict[str, str]) -> str:
    try:
        response = sqs.create_queue(
            QueueName=queue_name,
            Attributes=attributes,
        )
        queue_url = response["QueueUrl"]
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code")
        if error_code not in {"QueueAlreadyExists", "AWS.SimpleQueueService.QueueDeletedRecently"}:
            raise

        if error_code == "AWS.SimpleQueueService.QueueDeletedRecently":
            raise RuntimeError(
                f"Queue {queue_name!r} was deleted recently. SQS may require up to "
                "60 seconds before the same name can be reused."
            ) from exc

        queue_url = sqs.get_queue_url(QueueName=queue_name)["QueueUrl"]
        sqs.set_queue_attributes(QueueUrl=queue_url, Attributes=attributes)

    return queue_url


def _get_queue_arn(sqs, queue_url: str) -> str:
    response = sqs.get_queue_attributes(
        QueueUrl=queue_url,
        AttributeNames=["QueueArn"],
    )
    return response["Attributes"]["QueueArn"]


def _is_access_denied(exc: ClientError) -> bool:
    return exc.response.get("Error", {}).get("Code") in {
        "AccessDenied",
        "AccessDeniedException",
    }


def _update_env_file(updates: Dict[str, str]) -> None:
    if ENV_FILE.exists():
        lines = ENV_FILE.read_text().splitlines()
    else:
        lines = []

    updated_keys = set()
    next_lines = []

    for line in lines:
        key = line.split("=", 1)[0] if "=" in line else None
        if key in updates:
            next_lines.append(f"{key}={updates[key]}")
            updated_keys.add(key)
        else:
            next_lines.append(line)

    for key, value in updates.items():
        if key not in updated_keys:
            next_lines.append(f"{key}={value}")

    ENV_FILE.write_text("\n".join(next_lines) + "\n")


if __name__ == "__main__":
    main()
