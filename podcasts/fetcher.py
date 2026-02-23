#!/usr/bin/env python3
"""Podcast Fetcher"""
import subprocess
import json
import sys
from pathlib import Path
from typing import List, Dict

YAML_FILE = Path(__file__).parent.parent / "sources.yaml"


def load_sources():
    """Load sources from YAML config"""
    import yaml
    with open(YAML_FILE) as f:
        return yaml.safe_load(f)


def fetch_rss(url: str) -> List[Dict]:
    """Fetch podcast RSS feed"""
    try:
        result = subprocess.run([
            "curl", "-s", url
        ], capture_output=True, text=True, timeout=30)
        
        # Parse RSS (simplified)
        import xml.etree.ElementTree as ET
        
        # Save to temp file
        with open("/tmp/podcast_rss.xml", "w") as f:
            f.write(result.stdout)
        
        tree = ET.parse("/tmp/podcast_rss.xml")
        root = tree.getroot()
        
        # Namespace
        ns = {'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd'}
        
        items = root.findall('.//item')
        
        episodes = []
        for item in items[:5]:  # Latest 5 episodes
            title = item.find('title')
            link = item.find('link')
            pub_date = item.find('pubDate')
            enclosure = item.find('enclosure')
            
            episode = {
                "title": title.text if title is not None else "Untitled",
                "url": link.text if link is not None else "",
                "pub_date": pub_date.text if pub_date is not None else "",
                "audio_url": enclosure.get('url') if enclosure is not None else ""
            }
            episodes.append(episode)
        
        return episodes
    
    except Exception as e:
        print(f"Error fetching RSS: {e}")
        return []


def fetch_all_podcasts(sources: dict) -> dict:
    """Fetch latest episodes from all configured podcasts"""
    podcasts = sources.get("podcasts", [])
    
    results = {}
    
    for podcast in podcasts:
        name = podcast.get("name", "Unknown")
        rss_url = podcast.get("rss")
        category = podcast.get("category", "Podcast")
        
        if rss_url:
            episodes = fetch_rss(rss_url)
            if episodes:
                results[name] = {
                    "category": category,
                    "episodes": episodes
                }
                print(f"✅ {name}: {len(episodes)} episodes")
            else:
                print(f"❌ {name}: No episodes")
    
    return results


if __name__ == "__main__":
    sources = load_sources()
    results = fetch_all_podcasts(sources)
    print(f"\nTotal podcasts: {len(results)}")
