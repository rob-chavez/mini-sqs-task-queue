#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$ROOT_DIR/build/lambda"
DIST_DIR="$ROOT_DIR/dist"
ZIP_PATH="$DIST_DIR/mini-sqs-task-queue-lambda.zip"

rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR" "$DIST_DIR"

python3 -m pip install \
  --requirement "$ROOT_DIR/requirements.txt" \
  --target "$BUILD_DIR" \
  --upgrade

cp -R "$ROOT_DIR/src/mini_sqs_task_queue" "$BUILD_DIR/"
find "$BUILD_DIR" -type d -name "__pycache__" -prune -exec rm -rf {} +
find "$BUILD_DIR" -type f -name "*.pyc" -delete

(
  cd "$BUILD_DIR"
  zip -qr "$ZIP_PATH" .
)

echo "Created Lambda package:"
echo "$ZIP_PATH"
