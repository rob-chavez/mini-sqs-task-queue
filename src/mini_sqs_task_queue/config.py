from dataclasses import dataclass
import os
from typing import Optional

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    aws_region: str
    queue_url: Optional[str]
    dlq_url: Optional[str]
    wait_time_seconds: int
    max_messages: int


def get_settings() -> Settings:
    return Settings(
        aws_region=os.getenv("AWS_REGION", "us-east-1"),
        queue_url=_optional_env("SQS_QUEUE_URL"),
        dlq_url=_optional_env("SQS_DLQ_URL"),
        wait_time_seconds=_int_env("SQS_WAIT_TIME_SECONDS", default=20),
        max_messages=_int_env("SQS_MAX_MESSAGES", default=10),
    )


def _optional_env(name: str) -> Optional[str]:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return None
    return value


def _int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value.strip() == "":
        return default

    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {raw_value!r}") from exc
