#!/usr/bin/env python3
"""YouTube Channel Video Fetcher"""
import subprocess
import json
import sys
from pathlib import Path

YAML_FILE = Path(__file__).parent.parent / "sources.yaml"


def load_sources():
    """Load sources from YAML config"""
    import yaml
    with open(YAML_FILE) as f:
        return yaml.safe_load(f)


def get_latest_videos(channel_id: str, max_results: int = 3) -> list:
    """Fetch latest videos from a YouTube channel using yt-dlp"""
    try:
        # Use yt-dlp to get latest videos from channel
        result = subprocess.run([
            "yt-dlp",
            "--flat-playlist",
            "--playlist-end", str(max_results),
            "-J",
            f"https://www.youtube.com/channel/{channel_id}/videos"
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode != 0:
            print(f"Error fetching channel {channel_id}: {result.stderr[:200]}")
            return []
        
        data = json.loads(result.stdout)
        entries = data.get("entries", [])
        
        videos = []
        for entry in entries:
            video_id = entry.get("id")
            title = entry.get("title")
            
            if video_id and title and title != "[Private video]":
                videos.append({
                    "id": video_id,
                    "title": title,
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "upload_date": entry.get("upload_date"),
                    "duration": entry.get("duration"),
                })
        
        return videos[:max_results]
    
    except Exception as e:
        print(f"Error fetching videos from {channel_id}: {e}")
        return []


def fetch_all_channels(sources: dict) -> dict:
    """Fetch latest videos from all configured YouTube channels"""
    channels = sources.get("youtube", {}).get("channels", [])
    max_videos = sources.get("settings", {}).get("max_videos_per_channel", 3)
    
    results = {}
    
    for channel in channels:
        channel_id = channel["id"]
        name = channel["name"]
        category = channel.get("category", "YouTube")
        
        videos = get_latest_videos(channel_id, max_videos)
        
        if videos:
            results[channel_id] = {
                "name": name,
                "category": category,
                "videos": videos
            }
            print(f"✅ {name}: {len(videos)} videos")
        else:
            print(f"❌ {name}: No videos found")
    
    return results


if __name__ == "__main__":
    sources = load_sources()
    results = fetch_all_channels(sources)
    print(f"\nTotal channels processed: {len(results)}")
