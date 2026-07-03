from typing import Optional

from mini_sqs_task_queue.config import get_settings


def main() -> None:
    settings = get_settings()

    print("Mini SQS Task Queue setup check")
    print(f"AWS region: {settings.aws_region}")
    print(f"Main queue URL: {_display(settings.queue_url)}")
    print(f"Dead-letter queue URL: {_display(settings.dlq_url)}")
    print(f"Worker wait time: {settings.wait_time_seconds} seconds")
    print(f"Worker max messages: {settings.max_messages}")


def _display(value: Optional[str]) -> str:
    return value if value else "not set yet"


if __name__ == "__main__":
    main()
