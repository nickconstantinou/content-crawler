#!/bin/bash
# Heartbeat script - run one category per invocation
# Add to crontab: 0 * * * * ~/content-crawler/heartbeat.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Load environment
source ~/.openclaw/.env 2>/dev/null || true

echo "=== Content Crawler Heartbeat ==="
echo "Time: $(date)"

# Run category processor
python3 category_processor.py

echo "=== Done ==="
