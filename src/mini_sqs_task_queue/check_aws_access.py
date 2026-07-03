from botocore.exceptions import BotoCoreError, ClientError
import boto3

from mini_sqs_task_queue.config import get_settings


def main() -> None:
    settings = get_settings()
    sts = boto3.client("sts", region_name=settings.aws_region)

    try:
        identity = sts.get_caller_identity()
    except (BotoCoreError, ClientError) as exc:
        print("AWS access check failed.")
        print(f"Region: {settings.aws_region}")
        print(f"Error: {exc}")
        raise SystemExit(1) from exc

    print("AWS access check passed")
    print(f"Region: {settings.aws_region}")
    print(f"Account: {_mask_account(identity['Account'])}")
    print(f"Identity type: {_identity_type(identity['Arn'])}")


def _mask_account(account_id: str) -> str:
    return f"********{account_id[-4:]}"


def _identity_type(arn: str) -> str:
    if ":user/" in arn:
        return "IAM user"
    if ":assumed-role/" in arn:
        return "Assumed role"
    if ":role/" in arn:
        return "IAM role"
    return "AWS principal"


if __name__ == "__main__":
    main()
