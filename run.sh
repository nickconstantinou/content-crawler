#!/bin/bash
# Content Crawler Runner
# Usage: ./run.sh
# Requires: MINIMAX_API_KEY, GITHUB_TOKEN, TAVILY_API_KEY in environment

# Load OpenClaw environment
source ~/.openclaw/.env 2>/dev/null

cd /home/openclaw/.openclaw/workspace/projects/content-crawler
/usr/bin/python3 main.py
