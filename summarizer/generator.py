#!/usr/bin/env python3
"""Content Summarizer using MiniMax API"""
import os
import json
import sys
from pathlib import Path

try:
    import markdown
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False


def convert_markdown_to_html(text: str) -> str:
    """Convert markdown text to HTML"""
    import re
    
    # Headers (must do before bold)
    text = re.sub(r'^### (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.+)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
    
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    
    # Lists
    text = re.sub(r'^- (.+)$', r'<li>\1</li>', text, flags=re.MULTILINE)
    
    # Paragraphs - split by double newlines
    parts = text.split('\n\n')
    html_parts = []
    for part in parts:
        part = part.strip()
        if part.startswith('<h') or part.startswith('<li>') or part.startswith('<ul>'):
            html_parts.append(part)
        elif part:
            html_parts.append(f'<p>{part}</p>')
    
    return '\n\n'.join(html_parts)

# MiniMax API configuration
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "")
MINIMAX_BASE_URL = "https://api.minimax.io/anthropic/v1"


def call_minimax(prompt: str, system_prompt: str = "You are a helpful assistant.") -> str:
    """Call MiniMax API to generate summary"""
    import requests
    
    if not MINIMAX_API_KEY:
        print("Warning: MINIMAX_API_KEY not set, using mock response")
        return "Summary not available (no API key)"
    
    url = f"{MINIMAX_BASE_URL}/messages"
    
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
        "max_tokens": 4000
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        result = response.json()
        
        # MiniMax response format: result["content"][0]["text"]
        content = result.get("content", [])
        if content and isinstance(content, list):
            # Find the text content (skip thinking)
            for item in content:
                if item.get("type") == "text":
                    return item.get("text", "")
        
        return "No summary available"
    except Exception as e:
        print(f"Error calling MiniMax: {e}")
        return "Summary not available"


def summarize_youtube_video(title: str, transcript: str, max_words: int = 4000) -> str:
    """Summarize a YouTube video from transcript - comprehensive enough to replace watching"""
    # Truncate transcript if too long (increased limit for more detail)
    words = transcript.split()
    if len(words) > max_words:
        transcript = " ".join(words[:max_words])
    
    prompt = f"""You are writing a comprehensive article-style summary that allows readers to fully understand and benefit from this video WITHOUT watching it.

Write in a detailed, informative style similar to a well-researched blog post or magazine article - not bullet points, but flowing prose with clear structure.

Title: {title}

Transcript:
{transcript}

Write a comprehensive summary that includes:

1. **Introduction** (2-3 paragraphs): Set the context, introduce the main topic(s) and speaker(s), explain why this content matters now.

2. **Key Concepts & Arguments** (multiple paragraphs): For each major topic covered, explain:
   - What the speaker is discussing in depth
   - The reasoning behind their points
   - Any specific examples, data, or case studies mentioned
   - Nuances and qualifications the speaker makes

3. **Detailed Takeaways** (3-5 key insights): Explain each takeaway with context - not just what the point is, but WHY it's important and HOW to apply it.

4. **Who This Is For**: Clearly explain what audience would benefit most and what specific value they'll get.

Write as if you're creating a replaceable article - someone should be able to read ONLY your summary and understand the full essence of the video. Include specific names, companies, products, frameworks, and quotes where mentioned."""

    system_prompt = """You are an expert content creator and journalist.
Your goal is to create summaries so comprehensive and well-written that readers never need to watch the original video.
- Write in engaging, semi-formal prose (like a Longform article)
- Use hierarchical headings for structure
- Include specific examples, names, numbers, and quotes
- Explain not just WHAT but WHY and HOW
- Maintain the speaker's voice and perspective
- Never use bullet points as the primary format - use flowing paragraphs
- Be thorough but not rambling - every sentence should add value"""

    return call_minimax(prompt, system_prompt)


def summarize_article(title: str, content: str, url: str = "") -> str:
    """Summarize a news article - comprehensive enough to replace reading the original"""
    prompt = f"""Write a comprehensive article summary that allows readers to fully understand this story WITHOUT clicking through to the original article.

Title: {title}
URL: {url}

Content:
{content[:3000]}

Write a complete summary that includes:

1. **The Full Story** (2-3 paragraphs): Cover the complete narrative - what happened, when, where, who was involved. Don't summarize the summary.

2. **Why This Matters**: Explain the broader implications. How does this affect the industry, users, market, or society? What's the significance?

3. **Key Details**: Include specific numbers, dates, quotes, and facts that matter. Readers should get the important specifics.

4. **Context & Background**: What led to this? Is this part of a bigger trend or story? Provide the context readers need.

5. **What's Next**: Any announced plans, reactions, or what to watch for?

Write as a complete, standalone article - not an abbreviated version of the original."""

    system_prompt = """You are an expert tech/business journalist.
Create article summaries that are so complete and well-written that readers can skip the original article entirely.
- Write in journalistic style with clear inverted-pyramid structure
- Include specific details, numbers, quotes, and facts
- Explain the "so what" - why readers should care
- Provide necessary context and background
- Use semi-formal, engaging prose
- Never truncate the story - cover it fully"""

    return call_minimax(prompt, system_prompt)


def summarize_podcast_episode(title: str, transcript: str = "", description: str = "") -> str:
    """Summarize a podcast episode - comprehensive enough to replace listening, same as YouTube"""
    # Use transcript if available, otherwise description
    source_text = transcript if transcript else description
    max_words = 4000
    
    # Truncate if too long
    words = source_text.split()
    if len(words) > max_words:
        source_text = " ".join(words[:max_words])
    
    prompt = f"""You are writing a comprehensive article-style summary that allows readers to fully understand and benefit from this podcast episode WITHOUT listening to it.

Write in a detailed, informative style similar to a well-researched blog post or magazine article - not bullet points, but flowing prose with clear structure.

Title: {title}

{'Transcript:' if transcript else 'Description:'}
{source_text}

Write a comprehensive summary that includes:

1. **Introduction** (2-3 paragraphs): Set the context, introduce the main topic(s) and guest(s)/host(s), explain why this episode matters and what's notable about it.

2. **Key Concepts & Arguments** (multiple paragraph): For each major topic covered, explain:
   - What is being discussed in depth
   - The reasoning behind the points made
   - Any specific examples, data, case studies, or stories mentioned
   - Nuances and qualifications made by the speaker(s)

3. **Detailed Takeaways** (3-5 key insights): Explain each takeaway with context - not just what the point is, but WHY it's important and HOW to apply it.

4. **Notable Quotes** (2-3 memorable quotes): Capture insightful or memorable quotes exactly as stated.

5. **Who This Is For**: Clearly explain what audience would benefit most and what specific value they'll get.

Write as if you're creating a replaceable article - someone should be able to read ONLY your summary and understand the full essence of the episode. Include specific names, companies, products, frameworks, and quotes where mentioned."""

    system_prompt = """You are an expert content creator and journalist.
Your goal is to create summaries so comprehensive and well-written that listeners never need to hear the original episode.
- Write in engaging, semi-formal prose (like a Longform article)
- Use hierarchical headings for structure
- Include specific examples, names, numbers, and quotes
- Explain not just WHAT but WHY and HOW
- Maintain the speaker's voice and perspective
- Never use bullet points as the primary format - use flowing paragraphs
- Be thorough but not rambling - every sentence should add value"""

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
