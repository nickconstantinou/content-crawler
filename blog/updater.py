#!/usr/bin/env python3
"""Update posts.js with new blog posts"""
import json
import sys
from pathlib import Path
from datetime import datetime

BLOG_DIR = Path("/home/openclaw/.openclaw/workspace/projects/personal-blog")
POSTS_FILE = BLOG_DIR / "posts.js"


def load_posts():
    """Load existing posts from posts.js"""
    content = POSTS_FILE.read_text()
    
    # Extract JSON array from posts.js
    start = content.find("const posts = [")
    if start == -1:
        return []
    
    end = content.find("];", start)
    if end == -1:
        return []
    
    json_str = content[start+len("const posts = ["):end]
    
    try:
        posts = json.loads(f"[{json_str}]")
        return posts
    except:
        return []


def add_post(posts: list, new_post: dict) -> list:
    """Add new post to list, sorted by date"""
    # Check if post already exists
    for existing in posts:
        if existing.get("url") == new_post.get("url"):
            print(f"Post already exists: {new_post.get('title')}")
            return posts
    
    # Add new post
    posts.append(new_post)
    
    # Sort by date (newest first)
    posts.sort(key=lambda x: x.get("date", ""), reverse=True)
    
    return posts


def save_posts(posts: list):
    """Save posts back to posts.js"""
    json_str = json.dumps(posts, indent=2)
    
    # Read current content
    content = POSTS_FILE.read_text()
    
    # Replace posts array
    start = content.find("const posts = [")
    end = content.find("];", start) + 2
    
    new_content = content[:start] + "const posts = " + json_str + ";\n" + content[end:]
    
    POSTS_FILE.write_text(new_content)
    print(f"✅ Updated posts.js with {len(posts)} posts")


def add_to_posts_js(title: str, url: str, date: str = None, category: str = "AI", excerpt: str = ""):
    """Add a post to posts.js"""
    if date is None:
        date = datetime.now().strftime("%B %d, %Y")
    
    posts = load_posts()
    
    new_post = {
        "date": date,
        "category": category,
        "title": title,
        "excerpt": excerpt[:100] if excerpt else title,
        "tags": [category],
        "url": url
    }
    
    posts = add_post(posts, new_post)
    save_posts(posts)


if __name__ == "__main__":
    # Test - add a dummy post
    add_to_posts_js(
        "Test Post",
        "test.html",
        category="Test",
        excerpt="This is a test post"
    )
