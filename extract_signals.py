#!/usr/bin/env python3
"""Extract investment thesis signals from blog posts"""
import json
import re
from pathlib import Path
from datetime import datetime

BLOG_DIR = Path("/home/openclaw/.openclaw/agents/coding/workspace/projects/personal-blog")
POSTS_FILE = BLOG_DIR / "posts.js"
SIGNALS_FILE = BLOG_DIR / "signals.js"
SIGNALS_HTML = BLOG_DIR / "signals.html"

# Investment theme keywords
THEME_KEYWORDS = {
    "AI Infrastructure": [
        "nuclear", "data center power", "gpu shortage", "energy", "electricity grid",
        "power consumption", "energy consumption", "data center", "nvidia", "chip",
        "semiconductor", " wafer", "co-location", "grid", "electricity"
    ],
    "Longevity": [
        "anti-aging", "senolytic", "longevity", "nad+", "rapamycin", "telomere",
        "aging", "life extension", " lifespan", "youth", "healthspan", "bmta",
        "calorie restriction", "metformin", "nmn", "resveratrol"
    ],
    "Spatial Computing": [
        "vision pro", "ar glasses", "spatial computing", "metaverse", "augmented reality",
        "virtual reality", "mixed reality", "apple vision", "hololens", "magic leap",
        "meta quest", "vr headset", "xr"
    ],
    "Robotics": [
        "humanoid robot", "figure ai", "tesla optimus", "warehouse automation",
        "robot", "automation", "boston dynamics", "agv", "amr", "cobots",
        "industrial robot", "robotics", "自动化", "マシーン"
    ]
}

THEME_EMOJI = {
    "AI Infrastructure": "⚡",
    "Longevity": "🧬",
    "Spatial Computing": "👁️",
    "Robotics": "🤖"
}


def load_posts():
    """Load posts from posts.js"""
    content = POSTS_FILE.read_text()
    
    # Extract JSON array
    match = re.search(r'(?:var|const) posts = (\[[\s\S]*\]);?', content)
    if not match:
        print("Could not find posts array in posts.js")
        return []
    
    try:
        posts = json.loads(match.group(1))
        return posts
    except json.JSONDecodeError as e:
        print(f"Failed to parse posts.js: {e}")
        return []


def match_theme(post_title: str, post_excerpt: str = "") -> list:
    """Check if post matches any investment theme keywords"""
    text = (post_title + " " + post_excerpt).lower()
    matched_themes = []
    
    for theme, keywords in THEME_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text:
                if theme not in matched_themes:
                    matched_themes.append(theme)
                break
    
    return matched_themes


def extract_signals(posts: list) -> dict:
    """Extract posts matching investment themes"""
    signals = {
        "AI Infrastructure": [],
        "Longevity": [],
        "Spatial Computing": [],
        "Robotics": []
    }
    
    for post in posts:
        title = post.get("title", "")
        excerpt = post.get("excerpt", "")
        url = post.get("url", "")
        date = post.get("date", "")
        category = post.get("category", "")
        
        matched_themes = match_theme(title, excerpt)
        
        for theme in matched_themes:
            signals[theme].append({
                "date": date,
                "title": title,
                "excerpt": excerpt[:200] if excerpt else "",
                "url": url,
                "category": category
            })
    
    # Sort each theme by date (newest first)
    for theme in signals:
        signals[theme].sort(key=lambda x: x.get("date", ""), reverse=True)
    
    return signals


def generate_signals_js(signals: dict):
    """Generate signals.js file"""
    # Flatten signals for JS array
    js_content = f"""// Investment Thesis Signals - Auto-generated
// Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}

const signals = {json.dumps(signals, indent=2)};

const themes = {json.dumps(list(THEME_KEYWORDS.keys()), indent=2)};
"""
    
    SIGNALS_FILE.write_text(js_content)
    print(f"✅ Generated signals.js with {sum(len(v) for v in signals.values())} signals")


def generate_signals_html(signals: dict):
    """Generate signals.html page"""
    
    # Count total signals
    total_signals = sum(len(v) for v in signals.values())
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Thesis Signals | Nick's Blog</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #e2e8f0; line-height: 1.6; }}
        .container {{ max-width: 900px; margin: 0 auto; padding: 24px; }}
        header {{ text-align: center; padding: 48px 0 32px; border-bottom: 1px solid #1e293b; margin-bottom: 32px; }}
        header h1 {{ font-size: 48px; font-weight: 800; margin-bottom: 8px; }}
        header h1 span {{ color: #22d3ee; }}
        header p {{ color: #64748b; font-size: 18px; }}
        .back-link {{ display: inline-block; margin-bottom: 24px; color: #64748b; text-decoration: none; }}
        .back-link:hover {{ color: #22d3ee; }}
        .signal-count {{ font-size: 14px; color: #22d3ee; margin-top: 8px; }}
        .theme-section {{ margin-bottom: 48px; }}
        .theme-header {{ display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }}
        .theme-icon {{ font-size: 28px; }}
        .theme-title {{ font-size: 24px; font-weight: 700; color: #f8fafc; }}
        .theme-count {{ font-size: 14px; color: #64748b; }}
        .cards {{ display: flex; flex-direction: column; gap: 16px; }}
        .card {{ background: #1e293b; border-radius: 12px; padding: 20px; border: 1px solid #334155; transition: all 0.2s; }}
        .card:hover {{ border-color: #22d3ee; transform: translateY(-2px); }}
        .card a {{ text-decoration: none; color: inherit; display: block; }}
        .card-meta {{ font-size: 13px; color: #64748b; margin-bottom: 6px; }}
        .card-title {{ font-size: 18px; font-weight: 600; color: #f8fafc; margin-bottom: 8px; }}
        .card-excerpt {{ font-size: 14px; color: #94a3b8; line-height: 1.5; }}
        .no-signals {{ text-align: center; padding: 40px; color: #64748b; }}
        footer {{ text-align: center; padding: 48px 0; color: #475569; font-size: 14px; border-top: 1px solid #1e293b; margin-top: 40px; }}
    </style>
</head>
<body>
    <div class="container">
        <a href="index.html" class="back-link">← Back to Blog</a>
        <header>
            <h1>Thesis <span>Signals</span></h1>
            <p>Investment thesis tracking for emerging tech themes</p>
            <div class="signal-count">{total_signals} signals detected</div>
        </header>
"""
    
    for theme, posts in signals.items():
        emoji = THEME_EMOJI.get(theme, "📊")
        
        html += f"""
        <div class="theme-section">
            <div class="theme-header">
                <span class="theme-icon">{emoji}</span>
                <h2 class="theme-title">{theme}</h2>
                <span class="theme-count">({len(posts)} posts)</span>
            </div>
            <div class="cards">
"""
        
        if not posts:
            html += f'                <div class="card"><div class="no-signals">No signals found for {theme}</div></div>\n'
        else:
            for post in posts[:10]:  # Limit to 10 per theme
                excerpt = post.get("excerpt", "")[:150].replace('"', '&quot;').replace("<", "&lt;")
                title = post.get("title", "").replace('"', '&quot;').replace("<", "&lt;")
                
                html += f"""
                <div class="card">
                    <a href="{post.get('url', '#')}">
                        <div class="card-meta">{post.get('date', '')} • {post.get('category', '')}</div>
                        <div class="card-title">{title}</div>
                        <div class="card-excerpt">{excerpt}</div>
                    </a>
                </div>
"""
        
        html += """
            </div>
        </div>
"""
    
    html += f"""
        <footer>
            <p>Built with OpenClaw • Auto-updated daily • Last updated: {datetime.now().strftime('%B %d, %Y at %H:%M')}</p>
        </footer>
    </div>
</body>
</html>
"""
    
    SIGNALS_HTML.write_text(html)
    print(f"✅ Generated signals.html")


def main():
    print("🎯 Extracting Thesis Signals...")
    
    # Load posts
    posts = load_posts()
    print(f"📊 Loaded {len(posts)} posts")
    
    # Extract signals
    signals = extract_signals(posts)
    
    total = sum(len(v) for v in signals.values())
    print(f"🎯 Found {total} signals across {len(signals)} themes:")
    for theme, posts_list in signals.items():
        print(f"   {THEME_EMOJI.get(theme, '📊')} {theme}: {len(posts_list)}")
    
    # Generate files
    generate_signals_js(signals)
    generate_signals_html(signals)
    
    print("✅ Signal extraction complete!")


if __name__ == "__main__":
    main()
