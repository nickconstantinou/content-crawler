#!/usr/bin/env python3
"""Content Crawler Main Orchestrator - Improved Version"""
import os
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta
import json
import time

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from youtube import fetcher, downloader, transcriber
from podcasts import fetcher as podcast_fetcher
from news import fetcher as news_fetcher
from summarizer import generator
from blog import generator as blog_generator, updater

YAML_FILE = Path(__file__).parent / "sources.yaml"
BLOG_DIR = Path("/home/openclaw/.openclaw/workspace/projects/personal-blog")
CRAWL_STATE_FILE = Path("/home/openclaw/.openclaw/workspace/data/crawl-state.json")
LOG_FILE = Path("/home/openclaw/.openclaw/workspace/data/crawler.log")

# Setup logging
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def load_crawl_state():
    """Load last crawl timestamp"""
    CRAWL_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if CRAWL_STATE_FILE.exists():
        with open(CRAWL_STATE_FILE) as f:
            return json.load(f)
    return {"last_crawl": None, "processed_videos": [], "processed_podcasts": []}


def save_crawl_state(state):
    """Save crawl state"""
    with open(CRAWL_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def is_new_video(upload_date: str, last_crawl: str) -> bool:
    """Check if video is newer than last crawl"""
    if not last_crawl:
        return True  # First run, process everything
    
    try:
        # yt-dlp returns dates as YYYYMMDD
        video_date = datetime.strptime(upload_date, "%Y%m%d")
        crawl_date = datetime.fromisoformat(last_crawl)
        return video_date > crawl_date
    except (ValueError, TypeError):
        return True  # If can't parse, process anyway


def load_config():
    """Load sources from YAML config"""
    import yaml
    with open(YAML_FILE) as f:
        return yaml.safe_load(f)


def post_exists(title: str) -> bool:
    """Check if a post with this title already exists"""
    # Check blog directory for today's post with similar title
    today = datetime.now().strftime("%Y-%m-%d")
    slug = title.lower().replace(" ", "-")[:50]
    
    # Check both .html and .md extensions
    potential_files = [
        BLOG_DIR / f"{today}-{slug}.html",
        BLOG_DIR / f"{today}-{slug}.md",
    ]
    
    for pf in potential_files:
        if pf.exists():
            return True
    return False


def wait_for_transcript(video_url: str, max_retries: int = 3, delay: int = 5) -> str:
    """Wait for transcript with retry logic"""
    for attempt in range(max_retries):
        logger.info(f"Fetching transcript (attempt {attempt + 1}/{max_retries})...")
        transcript = transcriber.transcribe_video(video_url, [])
        
        if transcript and len(transcript.strip()) > 50:
            logger.info(f"Transcript fetched successfully ({len(transcript)} chars)")
            return transcript
        
        if attempt < max_retries - 1:
            logger.warning(f"No transcript yet, waiting {delay}s...")
            time.sleep(delay)
    
    # Final fallback: try without chunks
    logger.warning("No transcript after retries, using fallback")
    return transcriber.transcribe_with_ytdlp(video_url) or ""


def process_youtube_channel(channel_data: dict, config: dict, state: dict):
    """Process a YouTube channel - fetch, download, transcribe, summarize
    
    Args:
        channel_data: Channel configuration
        config: Full config
        state: Crawl state with processed video IDs
    """
    name = channel_data["name"]
    category = channel_data.get("category", "YouTube")
    videos = channel_data.get("videos", [])
    
    chunk_minutes = config.get("settings", {}).get("video_chunk_minutes", 10)
    processed_videos = state.get("processed_videos", [])
    
    videos_to_process = []
    videos_skipped = 0
    
    last_crawl = state.get("last_crawl")
    
    for video in videos:
        video_id = video["id"]
        title = video["title"]
        url = video["url"]
        upload_date = video.get("upload_date", "")
        
        # Idempotency check: already processed?
        if video_id in processed_videos:
            logger.info(f"⏭️ Already processed: {title}")
            videos_skipped += 1
            continue
        
        # Delta check - skip videos older than last crawl
        if last_crawl and upload_date:
            if not is_new_video(upload_date, last_crawl):
                videos_skipped += 1
                logger.info(f"⏭️ Skipping (older than last crawl): {title}")
                continue
        
        videos_to_process.append(video)
    
    logger.info(f"📊 {name}: {len(videos_to_process)} new, {videos_skipped} skipped")
    
    new_processed = []
    
    for video in videos_to_process:
        video_id = video["id"]
        title = video["title"]
        url = video["url"]
        
        logger.info(f"\n📺 Processing: {title}")
        
        try:
            # Idempotency: check if post already exists
            if post_exists(title):
                logger.info(f"Post already exists, skipping: {title}")
                processed_videos.append(video_id)
                continue
            
            # Download and chunk
            chunks = downloader.download_and_chunk(url, video_id, chunk_minutes)
            
            # Transcribe with retry
            transcript = wait_for_transcript(url, max_retries=3, delay=5)
            
            if not transcript or len(transcript.strip()) < 50:
                logger.warning(f"No transcript for {title}, skipping post")
                processed_videos.append(video_id)
                continue
            
            # Summarize
            logger.info("Generating summary...")
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
            logger.info(f"Saved post: {filename}")
            
            # Also save to Obsidian vault
            try:
                blog_generator.save_to_obsidian(
                    title=title,
                    summary=summary,
                    category=category,
                    video_url=url,
                    date=datetime.now().strftime("%Y-%m-%d")
                )
            except Exception as e:
                logger.warning(f"Obsidian save failed: {e}")
            
            # Add to posts.js
            url_path = f"{filename}"
            updater.add_to_posts_js(
                title=title,
                url=url_path,
                category=category,
                excerpt=summary[:150] if summary else "No summary"
            )
            
            # Mark as processed
            processed_videos.append(video_id)
            new_processed.append(video_id)
            logger.info(f"✅ Completed: {title}")
            
        except Exception as e:
            logger.error(f"Error processing {title}: {e}")
            continue
    
    # Update state with processed videos
    state["processed_videos"] = processed_videos
    
    return len(new_processed)


def process_podcast(podcast_data: dict, config: dict, state: dict):
    """Process a podcast - fetch, transcribe, summarize, create post"""
    name = podcast_data["name"]
    category = podcast_data.get("category", "Podcast")
    episodes = podcast_data.get("episodes", [])
    processed_podcasts = state.get("processed_podcasts", [])
    
    for episode in episodes[:1]:  # Just latest episode
        episode_id = episode.get("id", episode.get("title", "unknown"))
        title = episode.get("title", "Untitled")
        audio_url = episode.get("audio_url", "")
        
        # Idempotency check
        if episode_id in processed_podcasts:
            logger.info(f"⏭️ Already processed podcast: {title}")
            continue
        
        logger.info(f"\n🎙️ Processing: {title}")
        
        try:
            # Check if post exists
            if post_exists(title):
                logger.info(f"Post already exists, skipping: {title}")
                processed_podcasts.append(episode_id)
                continue
            
            # Try to get transcript via yt-dlp (podcasts often have subs on Spotify/YouTube)
            transcript = ""
            if audio_url:
                transcript = transcriber.transcribe_with_ytdlp(audio_url) or ""
            
            # Use description if no transcript
            description = episode.get("description", "")
            
            if transcript and len(transcript.strip()) > 100:
                # Full transcription - use YouTube summary style
                summary = generator.summarize_youtube_video(title, transcript)
            else:
                # Fallback to description-based summary
                logger.info("No transcript available, using description")
                summary = generator.summarize_podcast_episode(title, description)
            
            # Generate blog post
            filename, html = blog_generator.generate_youtube_post(
                title=title,
                summary=f"<p>{summary}</p>",
                category=category,
                video_url=audio_url,
                date=datetime.now().strftime("%Y-%m-%d")
            )
            
            # Save post
            blog_generator.save_post(filename, html)
            
            # Add to posts.js
            url_path = f"{filename}"
            updater.add_to_posts_js(
                title=title,
                url=url_path,
                category=category,
                excerpt=summary[:150] if summary else "No summary"
            )
            
            processed_podcasts.append(episode_id)
            logger.info(f"✅ Completed podcast: {title}")
            
        except Exception as e:
            logger.error(f"Error processing podcast {title}: {e}")
            continue
    
    # Update state with processed podcasts
    state["processed_podcasts"] = processed_podcasts
    
    return len(processed_podcasts) - len(state.get("processed_podcasts", []))


def process_news(news_data: dict):
    """Process news source - fetch, summarize, create post"""
    name = news_data["name"]
    category = news_data.get("category", "News")
    articles = news_data.get("articles", [])
    
    if not articles:
        return
    
    logger.info(f"\n📰 Processing: {name}")
    
    try:
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
        
        logger.info(f"✅ News complete: {name}")
        
    except Exception as e:
        logger.error(f"Error processing news {name}: {e}")


def run_full_crawl():
    """Run the full content crawl with error handling"""
    logger.info("🚀 Starting Content Crawl")
    logger.info(f"Time: {datetime.now()}")
    logger.info("=" * 50)
    
    # Load last crawl state
    state = load_crawl_state()
    last_crawl = state.get("last_crawl")
    logger.info(f"📅 Last crawl: {last_crawl or 'First run'}")
    
    # Load config
    try:
        config = load_config()
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return
    
    # Process YouTube
    logger.info("\n📡 Fetching YouTube channels...")
    try:
        yt_channels = fetcher.fetch_all_channels(config)
    except Exception as e:
        logger.error(f"Failed to fetch YouTube channels: {e}")
        yt_channels = {}
    
    new_videos = 0
    for channel_id, channel_data in yt_channels.items():
        try:
            processed = process_youtube_channel(channel_data, config, state)
            if processed:
                new_videos += processed
        except Exception as e:
            logger.error(f"Error processing channel {channel_id}: {e}")
    
    # Process Podcasts
    logger.info("\n📡 Fetching Podcasts...")
    try:
        podcasts = podcast_fetcher.fetch_all_podcasts(config)
        for name, podcast_data in podcasts.items():
            try:
                process_podcast(podcast_data, config, state)
            except Exception as e:
                logger.error(f"Error processing podcast {name}: {e}")
    except Exception as e:
        logger.error(f"Error fetching podcasts: {e}")
    
    # Process News
    logger.info("\n📡 Fetching News...")
    try:
        news_sources = news_fetcher.fetch_all_news(config)
        for name, news_data in news_sources.items():
            try:
                process_news(news_data)
            except Exception as e:
                logger.error(f"Error processing news {name}: {e}")
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
    
    logger.info("\n" + "=" * 50)
    logger.info(f"✅ Content crawl complete! Processed {new_videos} new videos")

    # Update state with processed videos/podcasts before saving
    state["processed_videos"] = state.get("processed_videos", [])
    state["processed_podcasts"] = state.get("processed_podcasts", [])
    
    # Save crawl state
    state["last_crawl"] = datetime.now().isoformat()
    save_crawl_state(state)
    logger.info(f"📅 Saved crawl state")
    
    # Git commit and push
    logger.info("\n📤 Pushing to GitHub...")
    try:
        os.chdir(BLOG_DIR)
        os.system('git add -A')
        os.system('git commit -m "Content crawl: $(date +%Y-%m-%d)" || true')
        os.system('git push origin main')
        logger.info("✅ Git push complete")
    except Exception as e:
        logger.error(f"Git push failed: {e}")


if __name__ == "__main__":
    run_full_crawl()
