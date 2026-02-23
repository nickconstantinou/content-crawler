#!/usr/bin/env python3
"""News Fetcher"""
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


def fetch_hackernews() -> List[Dict]:
    """Fetch top stories from Hacker News"""
    try:
        result = subprocess.run([
            "curl", "-s",
            "https://hn.algolia.com/api/v1/search_by_date?tags=story&hitsPerPage=5"
        ], capture_output=True, text=True, timeout=30)
        
        data = json.loads(result.stdout)
        hits = data.get("hits", [])
        
        stories = []
        for hit in hits:
            stories.append({
                "title": hit.get("title"),
                "url": hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                "points": hit.get("points", 0),
                "author": hit.get("author", ""),
            })
        
        return stories
    
    except Exception as e:
        print(f"Error fetching HN: {e}")
        return []


def fetch_rss(url: str) -> List[Dict]:
    """Fetch RSS feed"""
    try:
        result = subprocess.run([
            "curl", "-s", url
        ], capture_output=True, text=True, timeout=30)
        
        # Simple RSS parsing
        import xml.etree.ElementTree as ET
        
        with open("/tmp/news_rss.xml", "w") as f:
            f.write(result.stdout)
        
        tree = ET.parse("/tmp/news_rss.xml")
        root = tree.getroot()
        
        items = root.findall('.//item')
        
        articles = []
        for item in items[:5]:
            title = item.find('title')
            link = item.find('link')
            desc = item.find('description')
            
            article = {
                "title": title.text if title is not None else "Untitled",
                "url": link.text if link is not None else "",
                "description": desc.text[:200] if desc is not None and desc.text else ""
            }
            articles.append(article)
        
        return articles
    
    except Exception as e:
        print(f"Error fetching RSS: {e}")
        return []


def fetch_all_news(sources: dict) -> dict:
    """Fetch news from all configured sources"""
    news_sources = sources.get("news", [])
    
    results = {}
    
    for source in news_sources:
        name = source.get("name", "Unknown")
        category = source.get("category", "News")
        
        if "algolia" in source.get("url", ""):
            # Hacker News
            articles = fetch_hackernews()
        else:
            articles = fetch_rss(source.get("rss", ""))
        
        if articles:
            results[name] = {
                "category": category,
                "articles": articles
            }
            print(f"✅ {name}: {len(articles)} articles")
        else:
            print(f"❌ {name}: No articles")
    
    return results


if __name__ == "__main__":
    sources = load_sources()
    results = fetch_all_news(sources)
    print(f"\nTotal news sources: {len(results)}")
