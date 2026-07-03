# Mini SQS Task Queue

A beginner-friendly AWS SQS tutorial project that demonstrates how producers, consumers, retries, visibility timeouts, long polling, and dead-letter queues work.

The project simulates a tiny order-processing system:

- A producer sends fake order messages to an SQS queue.
- A worker receives messages from the queue.
- Successfully processed messages are deleted.
- Failed messages are retried automatically by SQS.
- Repeatedly failing messages eventually move to a dead-letter queue.

## Learning Goals

By the end of this project, you should understand:

- What an SQS queue is
- How to send messages to SQS
- How to receive messages from SQS
- Why workers must delete messages after successful processing
- How visibility timeout affects retries
- How long polling reduces empty responses
- How message attributes add metadata
- How dead-letter queues capture repeatedly failing messages

## Project Roadmap

### Step 1: Initialize the Repository

Create the Git repository, add a `.gitignore`, and document the learning path.

### Step 2: Create the Python Project Skeleton

Add the basic project layout, dependency files, and an `.env.example` file.

Files added in this step:

- `.env.example`: documents local environment variables without storing secrets
- `requirements.txt`: lists Python dependencies
- `src/mini_sqs_task_queue/config.py`: loads settings from environment variables
- `src/mini_sqs_task_queue/sqs_client.py`: creates a reusable SQS client
- `src/mini_sqs_task_queue/check_setup.py`: verifies local configuration

To set up your local Python environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

To verify the project can load local configuration:

```bash
PYTHONPATH=src python -m mini_sqs_task_queue.check_setup
```

Expected output should look similar to this before queues exist:

```text
Mini SQS Task Queue setup check
AWS region: us-east-1
Main queue name: mini-sqs-task-queue
Dead-letter queue name: mini-sqs-task-queue-dlq
Main queue URL: not set yet
Dead-letter queue URL: not set yet
Worker wait time: 20 seconds
Worker max messages: 10
Visibility timeout: 30 seconds
Max receive count: 3
```

### Step 3: Configure AWS Access

Install and configure the AWS CLI, choose a region, and verify credentials.

This project uses your normal AWS credential chain. Do not put AWS access keys in `.env` and do not commit credentials to Git.

First, confirm the AWS CLI is installed:

```bash
aws --version
```

If you have not configured AWS credentials yet, run:

```bash
aws configure
```

The AWS CLI will ask for:

- AWS access key ID
- AWS secret access key
- Default region name
- Default output format

For this tutorial, choose one region and use it consistently. For example, if your AWS CLI is configured for `us-east-1`, make sure `AWS_REGION=us-east-1` in your local `.env` file too.

To see your configured CLI region:

```bash
aws configure get region
```

To verify your AWS credentials with the CLI:

```bash
aws sts get-caller-identity
```

To verify your AWS credentials with this Python project:

```bash
PYTHONPATH=src python -m mini_sqs_task_queue.check_aws_access
```

Expected output should look similar to this:

```text
AWS access check passed
Region: us-east-1
Account: ********1234
Identity type: IAM user
```

### Step 4: Create SQS Queues

Create a main SQS queue and a dead-letter queue. Connect them with a redrive policy.

The dead-letter queue is where SQS moves messages after they fail too many times. In this project, the main queue sends a message to the dead-letter queue after `SQS_MAX_RECEIVE_COUNT=3` failed receives.

The setup script creates:

- Main queue: `mini-sqs-task-queue`
- Dead-letter queue: `mini-sqs-task-queue-dlq`
- Main queue long polling: `20` seconds
- Main queue visibility timeout: `30` seconds
- Redrive policy: move messages to the DLQ after `3` failed receives

Run the setup command:

```bash
PYTHONPATH=src python -m mini_sqs_task_queue.setup_queues
```

The script writes the generated queue URLs to your local `.env` file:

```text
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789012/mini-sqs-task-queue
SQS_DLQ_URL=https://sqs.us-east-1.amazonaws.com/123456789012/mini-sqs-task-queue-dlq
```

Then verify local configuration again:

```bash
PYTHONPATH=src python -m mini_sqs_task_queue.check_setup
```

If you see an `AccessDenied` error, your AWS identity can authenticate but does not have permission to manage SQS queues yet. For a learning account, an AWS administrator can attach the AWS managed `AmazonSQSFullAccess` policy, or use a narrower custom policy for this tutorial.

Example custom policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sqs:ListQueues",
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sqs:CreateQueue",
        "sqs:GetQueueUrl",
        "sqs:GetQueueAttributes",
        "sqs:SetQueueAttributes",
        "sqs:SendMessage",
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage"
      ],
      "Resource": "arn:aws:sqs:us-east-1:123456789012:mini-sqs-task-queue*"
    }
  ]
}
```

Replace `us-east-1` and `123456789012` with your AWS region and account ID.

### Step 5: Build the Producer

Write a script that sends fake order messages to the main queue.

### Step 6: Build the Worker

Write a script that receives messages, processes them, and deletes successful messages.

### Step 7: Add Long Polling

Update the worker to wait for messages efficiently instead of constantly returning empty responses.

### Step 8: Add Simulated Failures

Make some messages fail on purpose so retries become visible.

### Step 9: Explore the Dead-Letter Queue

Inspect messages that failed too many times and landed in the dead-letter queue.

### Step 10: Polish the Tutorial

Add setup instructions, diagrams, cleanup steps, and troubleshooting notes for GitHub readers.

## Prerequisites

- Python 3.9 or newer
- An AWS account
- AWS CLI installed
- Basic terminal familiarity

## Safety Note

Never commit real AWS credentials or local environment files. This repository ignores `.env` and `.env.*` files by default.
