#!/usr/bin/env python3
"""Blog Post Generator"""
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

BLOG_DIR = Path("/home/openclaw/openclaw-workspace/personal-blog")
POSTS_DIR = BLOG_DIR / "blog" / "_posts"


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug"""
    import re
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text[:50]


def generate_youtube_post(title: str, summary: str, category: str, video_url: str, date: str = None) -> str:
    """Generate blog post HTML for YouTube video"""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    slug = slugify(title)
    filename = f"{date}-{slug}.html"
    
    # Extract first paragraph as excerpt
    paragraphs = summary.split('\n\n')
    excerpt = paragraphs[0][:200] if paragraphs else summary[:200]
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} | Nick's Blog</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet">
  <style>
    :root {{ --primary: #0F172A; --accent: #F97316; --bg: #FFFFFF; --bg-alt: #F8FAFC; --text: #1E293B; --text-muted: #64748B; --border: #E2E8F0; }}
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: 'Inter', sans-serif; color: var(--text); background: var(--bg); line-height: 1.7; }}
    h1, h2, h3 {{ font-family: 'Space Grotesk', sans-serif; font-weight: 700; line-height: 1.3; }}
    .container {{ max-width: 720px; margin: 0 auto; padding: 0 24px; }}
    header {{ padding: 32px 0; border-bottom: 1px solid var(--border); }}
    .logo {{ font-family: 'Space Grotesk', sans-serif; font-size: 24px; font-weight: 700; color: var(--primary); text-decoration: none; }}
    .logo span {{ color: var(--accent); }}
    .back-link {{ display: inline-block; margin: 24px 0; color: var(--text-muted); text-decoration: none; }}
    article {{ padding: 32px 0; }}
    .meta {{ font-size: 14px; color: var(--text-muted); margin-bottom: 8px; }}
    h1 {{ font-size: 36px; margin-bottom: 24px; color: var(--primary); }}
    p {{ margin-bottom: 16px; }}
    .video-wrapper {{ position: relative; padding-bottom: 56.25%; margin-bottom: 24px; }}
    .video-wrapper iframe {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; }}
    footer {{ padding: 32px 0; border-top: 1px solid var(--border); text-align: center; margin-top: 40px; }}
    footer p {{ font-size: 14px; color: var(--text-muted); }}
  </style>
</head>
<body>
  <header>
    <div class="container">
      <a href="index.html" class="logo">← Nick's <span>Blog</span></a>
    </div>
  </header>
  <div class="container">
    <a href="index.html" class="back-link">← Back to Blog</a>
    <article>
      <p class="meta">{date} • {category}</p>
      <h1>{title}</h1>
      
      <div class="video-wrapper">
        <iframe src="https://www.youtube.com/embed/{video_url.split('=')[-1]}" frameborder="0" allowfullscreen></iframe>
      </div>
      
      {summary}
      
    </article>
  </div>
  <footer>
    <div class="container">
      <p>Nick's Blog — Built with Griptide 🧙‍♂️</p>
    </div>
  </footer>
</body>
</html>'''
    
    return filename, html


def generate_news_post(source: str, articles: list, date: str = None) -> str:
    """Generate blog post for news roundup"""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    slug = slugify(source)
    filename = f"{date}-{slug}-news.html"
    
    articles_html = ""
    for i, article in enumerate(articles, 1):
        articles_html += f'''
      <h2>{i}. {article.get('title', 'Untitled')}</h2>
      <p><a href="{article.get('url', '#')}" target="_blank">Read more →</a></p>
'''
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{source} News | Nick's Blog</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 720px; margin: 0 auto; padding: 24px; }}
    h1 {{ margin-bottom: 24px; }}
    h2 {{ margin-top: 24px; }}
    a {{ color: #F97316; }}
  </style>
</head>
<body>
  <a href="index.html">← Back</a>
  <h1>{source} News - {date}</h1>
  {articles_html}
</body>
</html>'''
    
    return filename, html


def save_post(filename: str, content: str, posts_dir: Path = None):
    """Save blog post to disk"""
    if posts_dir is None:
        posts_dir = POSTS_DIR
    
    posts_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = posts_dir / filename
    with open(filepath, "w") as f:
        f.write(content)
    
    print(f"✅ Saved: {filename}")
    return filepath


if __name__ == "__main__":
    # Test
    test_summary = """This is a test summary of a YouTube video about AI agents.

## Key Takeaways
- AI agents are changing software development
- They can take autonomous actions
- The future looks bright

This is a second paragraph with more details about the video content."""
    
    filename, html = generate_youtube_post(
        "The Future of AI Agents",
        test_summary,
        "AI",
        "https://www.youtube.com/watch?v=abc123"
    )
    print(f"Would create: {filename}")
