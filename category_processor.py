#!/usr/bin/env python3
"""
Category-Based Content Processor
Processes one category per run to avoid rate limits
"""
import os
import sys
from pathlib import Path
from datetime import datetime
import json

sys.path.insert(0, str(Path(__file__).parent))

from youtube import fetcher
from news import fetcher as news_fetcher
from summarizer import generator
from blog import generator as blog_generator, updater

YAML_FILE = Path(__file__).parent / "sources.yaml"
STATE_FILE = Path(__file__).parent / ".crawler_state.json"


def load_config():
    """Load sources from YAML config"""
    import yaml
    with open(YAML_FILE) as f:
        return yaml.safe_load(f)


def load_state():
    """Load crawler state"""
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"last_category": None, "processed_categories": []}


def save_state(state):
    """Save crawler state"""
    STATE_FILE.write_text(json.dumps(state, indent=2))


def get_next_category(sources, state):
    """Get the next category to process"""
    channels = sources.get("youtube", {}).get("channels", [])
    
    # Build category list
    categories = {}
    for channel in channels:
        cat = channel.get("category", "General")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(channel)
    
    # Get category list
    category_list = list(categories.keys())
    
    # Find next unprocessed category
    last = state.get("last_category")
    if last and last in category_list:
        idx = category_list.index(last)
        next_idx = (idx + 1) % len(category_list)
        return category_list[next_idx], categories[category_list[next_idx]]
    
    # Start from beginning
    if category_list:
        return category_list[0], categories[category_list[0]]
    
    return None, []


def process_category_channels(channels, config):
    """Process all channels in a category"""
    results = []
    
    for channel in channels:
        channel_id = channel["id"]
        name = channel["name"]
        category = channel.get("category", "YouTube")
        
        print(f"Processing {name}...")
        
        try:
            videos = fetcher.get_latest_videos(channel_id, max_results=5)
            
            for video in videos:
                # Get video details
                video_data = {
                    "title": video.get("title", ""),
                    "url": video.get("url", ""),
                    "id": video.get("id", ""),
                    "channel": name,
                    "category": category
                }
                results.append(video_data)
                
        except Exception as e:
            print(f"Error processing {name}: {e}")
    
    return results


def create_category_summary(videos_by_category):
    """Create a summary blog post for a category"""
    category = list(videos_by_category.keys())[0]
    videos = videos_by_category[category]
    
    if not videos:
        return None
    
    # Create summary content
    video_list = "\n".join([
        f"- [{v['title']}]({v['url']}) ({v['channel']})"
        for v in videos
    ])
    
    prompt = f"""Create a compelling blog post summary for this category: {category}

Videos in this category:
{video_list}

Create an engaging introduction and group these videos into themes if possible."""
    
    summary = generator.call_minimax(prompt, f"You are a tech content curator. Create engaging summaries for {category} content.")
    
    # Generate blog post
    date = datetime.now().strftime("%Y-%m-%d")
    slug = category.lower().replace("/", "-").replace(" ", "-")
    filename = f"{date}-{slug}-roundup.html"
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{category} Roundup | Nick's Blog</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 720px; margin: 0 auto; padding: 24px; line-height: 1.6; }}
    h1 {{ margin-bottom: 8px; }}
    .meta {{ color: #666; margin-bottom: 24px; }}
    .video-list {{ list-style: none; padding: 0; }}
    .video-item {{ margin-bottom: 16px; padding: 16px; border: 1px solid #eee; border-radius: 8px; }}
    .video-item a {{ font-weight: 600; text-decoration: none; color: #333; }}
    .video-item a:hover {{ color: #f97316; }}
    .channel {{ color: #666; font-size: 14px; }}
  </style>
</head>
<body>
  <a href="index.html">← Back to Blog</a>
  <h1>{category} Roundup</h1>
  <p class="meta">{date}</p>
  
  <p>{summary[:500]}...</p>
  
  <h2>Videos</h2>
  <ul class="video-list">
    {"".join([f'''
    <li class="video-item">
      <a href="{v['url']}" target="_blank">{v['title']}</a>
      <br><span class="channel">{v['channel']}</span>
    </li>''' for v in videos])}
  </ul>
  
  <footer>
    <p>Nick's Blog — Auto-generated</p>
  </footer>
</body>
</html>'''
    
    return filename, html, category


def run_one_category():
    """Process one category per run"""
    print("=" * 50)
    print("Category Content Processor")
    print("=" * 50)
    
    config = load_config()
    state = load_state()
    
    # Get next category
    category, channels = get_next_category(config, state)
    
    if not category:
        print("No categories to process!")
        return
    
    print(f"\nProcessing category: {category}")
    print(f"Channels: {[c['name'] for c in channels]}")
    
    # Process channels
    videos = process_category_channels(channels, config)
    
    if videos:
        # Create summary
        filename, html, cat = create_category_summary({category: videos})
        
        # Save post
        blog_generator.save_post(filename, html)
        
        # Update posts.js - URL should be in ROOT, not blog/_posts/
        url_path = filename
        updater.add_to_posts_js(
            title=f"{category} Roundup",
            url=url_path,
            category=cat,
            excerpt=f"Latest {category} videos"
        )
        
        print(f"\n✅ Created: {filename}")
    else:
        print("No videos found")
    
    # Update state
    state["last_category"] = category
    state["processed_categories"] = list(set(state.get("processed_categories", []) + [category]))
    save_state(state)
    
    print(f"\nState updated: last_category = {category}")


if __name__ == "__main__":
    run_one_category()
