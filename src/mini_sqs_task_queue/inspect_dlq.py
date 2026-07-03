import argparse
import json
from typing import Any, Dict

from mini_sqs_task_queue.config import get_settings
from mini_sqs_task_queue.sqs_client import create_sqs_client


def main() -> None:
    args = _parse_args()
    settings = get_settings()

    if settings.dlq_url is None:
        raise SystemExit("SQS_DLQ_URL is not set. Run setup_queues first.")

    sqs = create_sqs_client()
    print(f"Checking DLQ for up to {args.max_messages} message(s).")

    response = sqs.receive_message(
        QueueUrl=settings.dlq_url,
        MaxNumberOfMessages=args.max_messages,
        WaitTimeSeconds=args.wait_time_seconds,
        MessageAttributeNames=["All"],
        AttributeNames=["All"],
    )

    messages = response.get("Messages", [])
    if not messages:
        print("No messages available in the dead-letter queue.")
        return

    for message in messages:
        _print_message(message)

        if args.delete_after_read:
            sqs.delete_message(
                QueueUrl=settings.dlq_url,
                ReceiptHandle=message["ReceiptHandle"],
            )
            print(f"Deleted DLQ message {message['MessageId']}")
        else:
            print(
                "DLQ message was not deleted. It will become visible again "
                "after the visibility timeout."
            )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect messages that landed in the dead-letter queue."
    )
    parser.add_argument(
        "--max-messages",
        type=int,
        default=1,
        help="Maximum number of DLQ messages to receive. SQS allows 1-10.",
    )
    parser.add_argument(
        "--wait-time-seconds",
        type=int,
        default=5,
        help="How long to wait for DLQ messages.",
    )
    parser.add_argument(
        "--delete-after-read",
        action="store_true",
        help="Delete DLQ messages after printing them.",
    )
    args = parser.parse_args()

    if args.max_messages < 1 or args.max_messages > 10:
        parser.error("--max-messages must be between 1 and 10")

    if args.wait_time_seconds < 0 or args.wait_time_seconds > 20:
        parser.error("--wait-time-seconds must be between 0 and 20")

    return args


def _print_message(message: Dict[str, Any]) -> None:
    order = _parse_body(message)
    attributes = message.get("Attributes", {})

    print(f"DLQ message: {message['MessageId']}")
    print(f"DLQ receive count: {attributes.get('ApproximateReceiveCount', 'unknown')}")
    print(f"Original event type: {_message_attribute(message, 'event_type')}")
    print(f"Failure mode: {_message_attribute(message, 'failure_mode')}")
    print(f"Order ID: {order.get('order_id')}")
    print(f"Customer: {order.get('customer')}")
    print(f"Items: {', '.join(order.get('items', []))}")
    print(f"Total: ${order.get('total')}")
    print(f"Failure reason: {order.get('failure_reason', 'not set')}")


def _parse_body(message: Dict[str, Any]) -> Dict[str, Any]:
    try:
        return json.loads(message["Body"])
    except json.JSONDecodeError:
        return {"raw_body": message["Body"]}


def _message_attribute(message: Dict[str, Any], name: str) -> str:
    attribute = message.get("MessageAttributes", {}).get(name)
    if attribute is None:
        return "not set"
    return attribute.get("StringValue", "not set")


if __name__ == "__main__":
    main()
