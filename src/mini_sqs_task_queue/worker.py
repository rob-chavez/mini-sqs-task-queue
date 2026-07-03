import argparse
import json
from typing import Any, Dict, List

from mini_sqs_task_queue.config import get_settings
from mini_sqs_task_queue.sqs_client import create_sqs_client


class SimulatedProcessingError(Exception):
    """Raised when a tutorial message is marked to fail on purpose."""


def lambda_handler(
    event: Dict[str, Any],
    context: Any,
) -> Dict[str, List[Dict[str, str]]]:
    """Process SQS records delivered by an AWS Lambda event source mapping.

    Lambda deletes successful SQS records automatically. Failed records are
    returned in batchItemFailures so SQS can retry only those messages.
    """

    batch_item_failures = []

    for record in event.get("Records", []):
        try:
            order = _parse_message_body(record)
            _process_order(order, record)
        except Exception as exc:
            message_id = _message_id(record)
            batch_item_failures.append({"itemIdentifier": message_id})
            print(f"Processing failed for message {message_id}: {exc}")

    return {"batchItemFailures": batch_item_failures}


def main() -> None:
    args = _parse_args()
    settings = get_settings()

    if settings.queue_url is None:
        raise SystemExit("SQS_QUEUE_URL is not set. Run setup_queues first.")

    wait_time_seconds = (
        settings.wait_time_seconds
        if args.wait_time_seconds is None
        else args.wait_time_seconds
    )
    max_messages = (
        settings.max_messages
        if args.max_messages is None
        else args.max_messages
    )

    sqs = create_sqs_client()
    print(f"Polling for up to {max_messages} message(s).")
    print(f"Wait time: {wait_time_seconds} second(s).")

    response = sqs.receive_message(
        QueueUrl=settings.queue_url,
        MaxNumberOfMessages=max_messages,
        WaitTimeSeconds=wait_time_seconds,
        MessageAttributeNames=["All"],
        AttributeNames=["ApproximateReceiveCount"],
    )

    messages = response.get("Messages", [])
    if not messages:
        print("No messages available.")
        return

    failed_messages = 0

    for message in messages:
        try:
            order = _parse_message_body(message)
            _process_order(order, message)
        except SimulatedProcessingError as exc:
            failed_messages += 1
            print(f"Processing failed: {exc}")
            print(
                "Message was not deleted. SQS will make it visible again "
                "after the visibility timeout."
            )
            continue

        sqs.delete_message(
            QueueUrl=settings.queue_url,
            ReceiptHandle=message["ReceiptHandle"],
        )
        print(f"Deleted message {message['MessageId']}")

    if failed_messages:
        raise SystemExit(1)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Receive, process, and delete order messages from SQS."
    )
    parser.add_argument(
        "--max-messages",
        type=int,
        default=None,
        help=(
            "Maximum number of messages to receive in one request. "
            "Defaults to SQS_MAX_MESSAGES from .env."
        ),
    )
    parser.add_argument(
        "--wait-time-seconds",
        type=int,
        default=None,
        help=(
            "How long to wait for messages. Defaults to "
            "SQS_WAIT_TIME_SECONDS from .env."
        ),
    )
    args = parser.parse_args()

    if args.max_messages is not None and (
        args.max_messages < 1 or args.max_messages > 10
    ):
        parser.error("--max-messages must be between 1 and 10")

    if args.wait_time_seconds is not None and (
        args.wait_time_seconds < 0 or args.wait_time_seconds > 20
    ):
        parser.error("--wait-time-seconds must be between 0 and 20")

    return args


def _parse_message_body(message: Dict[str, Any]) -> Dict[str, Any]:
    try:
        return json.loads(_message_body(message))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Message {_message_id(message)} did not contain valid JSON") from exc


def _process_order(order: Dict[str, Any], message: Dict[str, Any]) -> None:
    receive_count = _message_system_attribute(
        message,
        "ApproximateReceiveCount",
    )
    event_type = _message_attribute(message, "event_type")

    print(f"Processing message {_message_id(message)}")
    print(f"Receive count: {receive_count}")
    print(f"Event type: {event_type}")
    print(f"Order ID: {order.get('order_id')}")
    print(f"Customer: {order.get('customer')}")
    print(f"Items: {', '.join(order.get('items', []))}")
    print(f"Total: ${order.get('total')}")

    if order.get("should_fail"):
        reason = order.get("failure_reason", "Order was marked to fail.")
        raise SimulatedProcessingError(str(reason))


def _message_attribute(message: Dict[str, Any], name: str) -> str:
    attribute = _message_attributes(message).get(name)
    if attribute is None:
        return "not set"
    return attribute.get("StringValue") or attribute.get("stringValue", "not set")


def _message_id(message: Dict[str, Any]) -> str:
    return message.get("MessageId") or message.get("messageId") or "unknown"


def _message_body(message: Dict[str, Any]) -> str:
    return message.get("Body") or message.get("body") or ""


def _message_attributes(message: Dict[str, Any]) -> Dict[str, Any]:
    return message.get("MessageAttributes") or message.get("messageAttributes") or {}


def _message_system_attribute(message: Dict[str, Any], name: str) -> str:
    attributes = message.get("Attributes") or message.get("attributes") or {}
    return attributes.get(name, "unknown")


if __name__ == "__main__":
    main()
