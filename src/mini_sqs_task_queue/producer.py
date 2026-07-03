import argparse
import json
import random
from datetime import datetime, timezone
from uuid import uuid4

from mini_sqs_task_queue.config import get_settings
from mini_sqs_task_queue.sqs_client import create_sqs_client


CUSTOMERS = [
    "Ada Lovelace",
    "Grace Hopper",
    "Katherine Johnson",
    "Margaret Hamilton",
    "Radia Perlman",
]

ITEMS = [
    "keyboard",
    "notebook",
    "coffee mug",
    "desk lamp",
    "water bottle",
]


def main() -> None:
    args = _parse_args()
    settings = get_settings()

    if settings.queue_url is None:
        raise SystemExit("SQS_QUEUE_URL is not set. Run setup_queues first.")

    sqs = create_sqs_client()

    for _ in range(args.count):
        _send_order(sqs, settings.queue_url, _build_order())

    if args.include_failing_order:
        _send_order(sqs, settings.queue_url, _build_order(should_fail=True))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send fake order messages to the SQS queue."
    )
    parser.add_argument(
        "--count",
        type=int,
        default=5,
        help="Number of fake orders to send.",
    )
    parser.add_argument(
        "--include-failing-order",
        action="store_true",
        help="Also send one order that the worker will fail on purpose.",
    )
    args = parser.parse_args()

    if args.count < 0:
        parser.error("--count must be 0 or greater")

    if args.count == 0 and not args.include_failing_order:
        parser.error("--count must be at least 1 unless --include-failing-order is used")

    return args


def _send_order(sqs, queue_url: str, order: dict) -> None:
    message_attributes = {
        "event_type": {
            "DataType": "String",
            "StringValue": "order.created",
        },
        "source": {
            "DataType": "String",
            "StringValue": "producer.py",
        },
    }

    if order.get("should_fail"):
        message_attributes["failure_mode"] = {
            "DataType": "String",
            "StringValue": "always_fail",
        }

    response = sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(order),
        MessageAttributes=message_attributes,
    )

    failure_note = " (will fail)" if order.get("should_fail") else ""
    print(
        "Sent order "
        f"{order['order_id']}{failure_note} "
        f"as message {response['MessageId']}"
    )


def _build_order(should_fail: bool = False) -> dict:
    item_count = random.randint(1, 3)
    selected_items = random.sample(ITEMS, k=item_count)

    order = {
        "order_id": str(uuid4()),
        "customer": random.choice(CUSTOMERS),
        "items": selected_items,
        "total": _random_total(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    if should_fail:
        order["customer"] = "Failure Demo"
        order["should_fail"] = True
        order["failure_reason"] = "This order is marked to fail for the retry lesson."

    return order


def _random_total() -> float:
    return round(random.uniform(10.0, 250.0), 2)


if __name__ == "__main__":
    main()
