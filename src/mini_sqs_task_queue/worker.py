import argparse
import json
from typing import Any, Dict

from mini_sqs_task_queue.config import get_settings
from mini_sqs_task_queue.sqs_client import create_sqs_client


def main() -> None:
    args = _parse_args()
    settings = get_settings()

    if settings.queue_url is None:
        raise SystemExit("SQS_QUEUE_URL is not set. Run setup_queues first.")

    sqs = create_sqs_client()
    response = sqs.receive_message(
        QueueUrl=settings.queue_url,
        MaxNumberOfMessages=args.max_messages,
        WaitTimeSeconds=args.wait_time_seconds,
        MessageAttributeNames=["All"],
        AttributeNames=["ApproximateReceiveCount"],
    )

    messages = response.get("Messages", [])
    if not messages:
        print("No messages available.")
        return

    for message in messages:
        order = _parse_message_body(message)
        _process_order(order, message)
        sqs.delete_message(
            QueueUrl=settings.queue_url,
            ReceiptHandle=message["ReceiptHandle"],
        )
        print(f"Deleted message {message['MessageId']}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Receive, process, and delete order messages from SQS."
    )
    parser.add_argument(
        "--max-messages",
        type=int,
        default=1,
        help="Maximum number of messages to receive in one request. SQS allows 1-10.",
    )
    parser.add_argument(
        "--wait-time-seconds",
        type=int,
        default=0,
        help="How long to wait for messages. Part 6 uses 0; Part 7 will use long polling.",
    )
    args = parser.parse_args()

    if args.max_messages < 1 or args.max_messages > 10:
        parser.error("--max-messages must be between 1 and 10")

    if args.wait_time_seconds < 0 or args.wait_time_seconds > 20:
        parser.error("--wait-time-seconds must be between 0 and 20")

    return args


def _parse_message_body(message: Dict[str, Any]) -> Dict[str, Any]:
    try:
        return json.loads(message["Body"])
    except json.JSONDecodeError as exc:
        raise ValueError(f"Message {message['MessageId']} did not contain valid JSON") from exc


def _process_order(order: Dict[str, Any], message: Dict[str, Any]) -> None:
    receive_count = message.get("Attributes", {}).get("ApproximateReceiveCount", "unknown")
    event_type = _message_attribute(message, "event_type")

    print(f"Processing message {message['MessageId']}")
    print(f"Receive count: {receive_count}")
    print(f"Event type: {event_type}")
    print(f"Order ID: {order.get('order_id')}")
    print(f"Customer: {order.get('customer')}")
    print(f"Items: {', '.join(order.get('items', []))}")
    print(f"Total: ${order.get('total')}")


def _message_attribute(message: Dict[str, Any], name: str) -> str:
    attribute = message.get("MessageAttributes", {}).get(name)
    if attribute is None:
        return "not set"
    return attribute.get("StringValue", "not set")


if __name__ == "__main__":
    main()
