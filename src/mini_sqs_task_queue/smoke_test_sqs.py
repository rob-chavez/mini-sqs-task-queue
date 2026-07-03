import json
from uuid import uuid4

from mini_sqs_task_queue.config import get_settings
from mini_sqs_task_queue.sqs_client import create_sqs_client


def main() -> None:
    settings = get_settings()
    sqs = create_sqs_client()

    if settings.queue_url is None:
        raise SystemExit("SQS_QUEUE_URL is not set. Run setup_queues first.")

    order_id = f"smoke-test-{uuid4()}"
    message_body = {
        "order_id": order_id,
        "customer": "Tutorial Smoke Test",
        "total": 12.34,
    }

    send_response = sqs.send_message(
        QueueUrl=settings.queue_url,
        MessageBody=json.dumps(message_body),
        MessageAttributes={
            "source": {
                "DataType": "String",
                "StringValue": "smoke-check",
            },
        },
    )
    print(f"Sent message: {send_response['MessageId']}")

    receive_response = sqs.receive_message(
        QueueUrl=settings.queue_url,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=5,
        MessageAttributeNames=["All"],
    )

    messages = receive_response.get("Messages", [])
    if not messages:
        raise SystemExit("No message received during smoke test.")

    message = messages[0]
    print(f"Received message: {message['MessageId']}")
    print(f"Message body: {message['Body']}")

    sqs.delete_message(
        QueueUrl=settings.queue_url,
        ReceiptHandle=message["ReceiptHandle"],
    )
    print("Deleted message successfully")

    attributes = sqs.get_queue_attributes(
        QueueUrl=settings.queue_url,
        AttributeNames=[
            "ApproximateNumberOfMessages",
            "ApproximateNumberOfMessagesNotVisible",
        ],
    )["Attributes"]

    print(
        "Approximate visible messages: "
        f"{attributes.get('ApproximateNumberOfMessages')}"
    )
    print(
        "Approximate in-flight messages: "
        f"{attributes.get('ApproximateNumberOfMessagesNotVisible')}"
    )


if __name__ == "__main__":
    main()
