import boto3

from mini_sqs_task_queue.config import get_settings


def create_sqs_client():
    settings = get_settings()
    return boto3.client("sqs", region_name=settings.aws_region)
