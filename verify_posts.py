#!/usr/bin/env python3
"""
Post-deployment verifier using Playwright
Checks that each blog post loads correctly
"""
import sys
import os
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

BLOG_URL = "https://nickconstantinou.github.io/dashboard"


def verify_post(url: str) -> bool:
    """Verify a single post loads correctly"""
    try:
        from playwright.sync_api import sync_playwright
        import os
        
        with sync_playwright() as p:
            # Use system Chrome
            chrome_path = "/usr/bin/google-chrome-stable"
            
            browser = p.chromium.launch(
                headless=True,
                executable_path=chrome_path if os.path.exists(chrome_path) else None,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            page = browser.new_page()
            
            # Try to load the post
            full_url = f"{BLOG_URL}/{url}" if not url.startswith('http') else url
            
            response = page.goto(full_url, wait_until="domcontentloaded", timeout=15000)
            
            if response and response.status == 200:
                # Check for basic content
                title = page.title()
                print(f"  ✅ {full_url}")
                print(f"     Title: {title[:50]}")
                browser.close()
                return True
            else:
                print(f"  ❌ {full_url} - Status: {response.status if response else 'No response'}")
                browser.close()
                return False
                
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def verify_posts_from_js():
    """Verify all posts in posts.js load correctly"""
    from blog import updater
    
    posts = updater.load_posts()
    
    print(f"\n=== Verifying {len(posts)} posts ===")
    
    success = 0
    failed = 0
    
    for post in posts:
        url = post.get("url", "")
        title = post.get("title", "Untitled")
        
        print(f"\nChecking: {title}")
        
        if verify_post(url):
            success += 1
        else:
            failed += 1
    
    print(f"\n=== Results ===")
    print(f"✅ Success: {success}")
    print(f"❌ Failed: {failed}")
    
    return failed == 0


if __name__ == "__main__":
    verify_posts_from_js()
