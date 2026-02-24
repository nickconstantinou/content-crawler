#!/usr/bin/env python3
"""Content Crawler Main Orchestrator"""
import os
import sys
from pathlib import Path
from datetime import datetime
import json

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from youtube import fetcher, downloader, transcriber
from podcasts import fetcher as podcast_fetcher
from news import fetcher as news_fetcher
from summarizer import generator
from blog import generator as blog_generator, updater

YAML_FILE = Path(__file__).parent / "sources.yaml"
BLOG_DIR = Path("/home/openclaw/openclaw-workspace/personal-blog")


def load_config():
    """Load sources from YAML config"""
    import yaml
    with open(YAML_FILE) as f:
        return yaml.safe_load(f)


def process_youtube_channel(channel_data: dict, config: dict):
    """Process a YouTube channel - fetch, download, transcribe, summarize"""
    name = channel_data["name"]
    category = channel_data.get("category", "YouTube")
    videos = channel_data.get("videos", [])
    
    chunk_minutes = config.get("settings", {}).get("video_chunk_minutes", 10)
    
    for video in videos:
        video_id = video["id"]
        title = video["title"]
        url = video["url"]
        
        print(f"\n📺 Processing: {title}")
        
        # Download and chunk
        chunks = downloader.download_and_chunk(url, video_id, chunk_minutes)
        
        # Transcribe
        transcript = transcriber.transcribe_video(url, chunks)
        
        if True:  # Always create post
            # Summarize
            summary = generator.summarize_youtube_video(title, transcript)
            
            # Generate blog post
            filename, html = blog_generator.generate_youtube_post(
                title=title,
                summary=summary,
                category=category,
                video_url=url,
                date=datetime.now().strftime("%Y-%m-%d")
            )
            
            # Save post
            filepath = blog_generator.save_post(filename, html)
            
            # Add to posts.js
            url_path = f"{filename}"
            updater.add_to_posts_js(
                title=title,
                url=url_path,
                category=category,
                excerpt=summary[:150]
            )
        else:
            print(f"⚠️ No transcript available for {title}")


def process_podcast(podcast_data: dict, config: dict):
    """Process a podcast - fetch, summarize, create post"""
    name = podcast_data["name"]
    category = podcast_data.get("category", "Podcast")
    episodes = podcast_data.get("episodes", [])
    
    for episode in episodes[:1]:  # Just latest episode
        title = episode.get("title", "Untitled")
        audio_url = episode.get("audio_url", "")
        
        print(f"\n🎙️ Processing: {title}")
        
        if audio_url:
            # Summarize based on description
            description = episode.get("description", "")
            summary = generator.summarize_podcast_episode(title, description)
            
            # Generate blog post
            filename, html = blog_generator.generate_youtube_post(
                title=title,
                summary=f"<p>{summary}</p>",
                category=category,
                video_url=audio_url,  # For video ID extraction
                date=datetime.now().strftime("%Y-%m-%d")
            )
            
            # Save post
            blog_generator.save_post(filename, html)


def process_news(news_data: dict):
    """Process news source - fetch, summarize, create post"""
    name = news_data["name"]
    category = news_data.get("category", "News")
    articles = news_data.get("articles", [])
    
    if not articles:
        return
    
    print(f"\n📰 Processing: {name}")
    
    # Generate news roundup post
    filename, html = blog_generator.generate_news_post(
        source=name,
        articles=articles,
        date=datetime.now().strftime("%Y-%m-%d")
    )
    
    # Save post
    blog_generator.save_post(filename, html)
    
    # Add to posts.js
    url_path = f"{filename}"
    updater.add_to_posts_js(
        title=f"{name} News Round-up",
        url=url_path,
        category=category,
        excerpt=f"Latest {name} stories"
    )


def run_full_crawl():
    """Run the full content crawl"""
    print("🚀 Starting Content Crawl")
    print(f"Time: {datetime.now()}")
    print("=" * 50)
    
    config = load_config()
    
    # Process YouTube
    print("\n📡 Fetching YouTube channels...")
    yt_channels = fetcher.fetch_all_channels(config)
    
    for channel_id, channel_data in yt_channels.items():
        try:
            process_youtube_channel(channel_data, config)
        except Exception as e:
            print(f"Error processing {channel_id}: {e}")
    
    # Process Podcasts
    print("\n📡 Fetching Podcasts...")
    try:
        podcasts = podcast_fetcher.fetch_all_podcasts(config)
        for name, podcast_data in podcasts.items():
            try:
                process_podcast(podcast_data, config)
            except Exception as e:
                print(f"Error processing podcast {name}: {e}")
    except Exception as e:
        print(f"Error fetching podcasts: {e}")
    
    # Process News
    print("\n📡 Fetching News...")
    try:
        news_sources = news_fetcher.fetch_all_news(config)
        for name, news_data in news_sources.items():
            try:
                process_news(news_data)
            except Exception as e:
                print(f"Error processing news {name}: {e}")
    except Exception as e:
        print(f"Error fetching news: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Content crawl complete!")
    
    # Git commit and push
    print("\n📤 Pushing to GitHub...")
    os.chdir(BLOG_DIR)
    os.system('git add -A')
    os.system('git commit -m "Content crawl: $(date +%Y-%m-%d)" || true')
    os.system('git push origin master')


if __name__ == "__main__":
    run_full_crawl()
