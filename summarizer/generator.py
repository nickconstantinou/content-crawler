#!/usr/bin/env python3
"""Content Summarizer using MiniMax API"""
import os
import json
import sys
from pathlib import Path

# MiniMax API configuration
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "")
MINIMAX_BASE_URL = "https://api.minimax.chat/v1"


def call_minimax(prompt: str, system_prompt: str = "You are a helpful assistant.") -> str:
    """Call MiniMax API to generate summary"""
    import requests
    
    if not MINIMAX_API_KEY:
        print("Warning: MINIMAX_API_KEY not set, using mock response")
        return "Summary not available (no API key)"
    
    url = f"{MINIMAX_BASE_URL}/text/chatcompletion_v2"
    
    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "MiniMax-M2.5",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 2000
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Error calling MiniMax: {e}")
        return "Summary not available"


def summarize_youtube_video(title: str, transcript: str, max_words: int = 2000) -> str:
    """Summarize a YouTube video from transcript"""
    # Truncate transcript if too long
    words = transcript.split()
    if len(words) > max_words:
        transcript = " ".join(words[:max_words])
    
    prompt = f"""Summarize this YouTube video in 3-5 paragraphs:

Title: {title}

Transcript:
{transcript}

Provide:
1. Key topics discussed
2. Main takeaways (3-5 bullet points)
3. Who would benefit from watching"""

    system_prompt = """You are an expert content summarizer. 
Create engaging, informative summaries that capture the essence of videos.
Use a conversational but informative tone.
Format with clear sections."""

    return call_minimax(prompt, system_prompt)


def summarize_article(title: str, content: str, url: str = "") -> str:
    """Summarize a news article"""
    prompt = f"""Summarize this article in 2-3 paragraphs:

Title: {title}
URL: {url}

Content:
{content[:2000]}

Provide:
1. Main story points (2-3 sentences)
2. Why this matters
3. A brief takeaway"""

    system_prompt = """You are an expert news summarizer.
Create concise, informative summaries.
Focus on what's new and why readers should care."""

    return call_minimax(prompt, system_prompt)


def summarize_podcast_episode(title: str, description: str = "") -> str:
    """Summarize a podcast episode"""
    prompt = f"""Create a compelling description for this podcast episode:

Title: {title}

Description: {description[:1000]}

Provide:
1. What the episode covers (2-3 sentences)
2. Key topics/guests
3. Why listeners should tune in"""

    system_prompt = """You are a podcast content specialist.
Create engaging descriptions that make people want to listen.
Keep it conversational and exciting."""

    return call_minimax(prompt, system_prompt)


if __name__ == "__main__":
    # Test
    test_transcript = """
    Today we're talking about the future of AI agents and how they're changing software development.
    AI agents are autonomous programs that can use tools, make decisions, and complete complex tasks.
    Unlike traditional AI models that just respond to prompts, agents can take actions on your behalf.
    """
    
    summary = summarize_youtube_video("The Future of AI Agents", test_transcript)
    print(summary)
