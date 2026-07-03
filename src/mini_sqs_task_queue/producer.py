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
        order = _build_order()
        response = sqs.send_message(
            QueueUrl=settings.queue_url,
            MessageBody=json.dumps(order),
            MessageAttributes={
                "event_type": {
                    "DataType": "String",
                    "StringValue": "order.created",
                },
                "source": {
                    "DataType": "String",
                    "StringValue": "producer.py",
                },
            },
        )

        print(
            "Sent order "
            f"{order['order_id']} "
            f"as message {response['MessageId']}"
        )


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
    args = parser.parse_args()

    if args.count < 1:
        parser.error("--count must be at least 1")

    return args


def _build_order() -> dict:
    item_count = random.randint(1, 3)
    selected_items = random.sample(ITEMS, k=item_count)

    return {
        "order_id": str(uuid4()),
        "customer": random.choice(CUSTOMERS),
        "items": selected_items,
        "total": _random_total(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def _random_total() -> float:
    return round(random.uniform(10.0, 250.0), 2)


if __name__ == "__main__":
    main()
