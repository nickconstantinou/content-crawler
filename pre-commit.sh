#!/bin/bash
# Pre-commit hook for content-crawler
# Run tests before committing

echo "🧪 Running content-crawler tests..."

cd /home/openclaw/.openclaw/workspace/projects/content-crawler

# Run pytest
python3 -m pytest test_crawler.py -v --tb=short

if [ $? -ne 0 ]; then
    echo "❌ Tests failed! Fix issues before committing."
    exit 1
fi

echo "✅ All tests passed!"
exit 0
