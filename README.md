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

### Step 3: Configure AWS Access

Install and configure the AWS CLI, choose a region, and verify credentials.

### Step 4: Create SQS Queues

Create a main SQS queue and a dead-letter queue. Connect them with a redrive policy.

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

- Python 3.10 or newer
- An AWS account
- AWS CLI installed
- Basic terminal familiarity

## Safety Note

Never commit real AWS credentials or local environment files. This repository ignores `.env` and `.env.*` files by default.
