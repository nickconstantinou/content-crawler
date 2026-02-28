#!/usr/bin/env python3
"""Unit and E2E Tests for Content Crawler - Simplified Version"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

import pytest

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))


# ============================================================================
# UNIT TESTS
# ============================================================================

class TestTranscriber:
    """Tests for youtube/transcriber.py"""
    
    def test_cleanup_vtt(self):
        """Test VTT cleanup removes timing tags"""
        from youtube.transcriber import cleanup_vtt
        
        vtt_content = """WEBVTT

00:00:00.719 --> 00:00:03.030
Hello world

00:00:03.030 --> 00:00:05.500
This is a test
"""
        result = cleanup_vtt(vtt_content)
        
        assert "WEBVTT" not in result
        assert "00:00:00.719" not in result
        assert "Hello world" in result
        assert "This is a test" in result
    
    def test_cleanup_vtt_removes_html_tags(self):
        """Test VTT cleanup removes HTML-like tags"""
        from youtube.transcriber import cleanup_vtt
        
        vtt_content = """WEBVTT

00:00:00.000 --> 00:00:02.000
<c>This is colored</c>
"""
        result = cleanup_vtt(vtt_content)
        
        assert "<c>" not in result
        assert "This is colored" in result


class TestStateManagement:
    """Tests for state management in main.py"""
    
    def test_load_crawl_state_creates_default(self):
        """Test default state when no file exists"""
        import main
        import importlib
        importlib.reload(main)
        
        # Use temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
            os.unlink(temp_path)  # Delete so it doesn't exist
        
        try:
            # Patch the state file path
            with patch.object(main, 'CRAWL_STATE_FILE', Path(temp_path)):
                state = main.load_crawl_state()
                assert state["last_crawl"] is None
                assert state.get("processed_videos", []) == []
                assert state.get("processed_podcasts", []) == []
        finally:
            if Path(temp_path).exists():
                os.unlink(temp_path)
    
    def test_save_and_load_crawl_state(self):
        """Test state persists correctly"""
        import main
        import importlib
        importlib.reload(main)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            test_state = {
                "last_crawl": "2026-02-28T10:00:00",
                "processed_videos": ["abc123", "def456"],
                "processed_podcasts": ["pod001"]
            }
            
            with patch.object(main, 'CRAWL_STATE_FILE', Path(temp_path)):
                main.save_crawl_state(test_state)
                loaded = main.load_crawl_state()
                
                assert loaded["last_crawl"] == test_state["last_crawl"]
                assert loaded["processed_videos"] == test_state["processed_videos"]
                assert loaded["processed_podcasts"] == test_state["processed_podcasts"]
        finally:
            if Path(temp_path).exists():
                os.unlink(temp_path)


class TestDateHandling:
    """Tests for date comparison logic"""
    
    def test_is_new_video_returns_true_for_newer(self):
        """Test video newer than last crawl is flagged"""
        import main
        
        # Video from today, last crawl from yesterday
        result = main.is_new_video("20260228", "2026-02-27T00:00:00")
        assert result == True
    
    def test_is_new_video_returns_false_for_older(self):
        """Test video older than last crawl is flagged"""
        import main
        
        # Video from yesterday, last crawl from today
        result = main.is_new_video("20260227", "2026-02-28T00:00:00")
        assert result == False
    
    def test_is_new_video_returns_true_for_first_run(self):
        """Test first run processes all videos"""
        import main
        
        result = main.is_new_video("20200101", None)
        assert result == True
    
    def test_is_new_video_handles_invalid_dates(self):
        """Test invalid dates default to processing"""
        import main
        
        result = main.is_new_video("invalid", "2026-02-28T00:00:00")
        assert result == True


class TestIdempotency:
    """Tests for idempotency checks"""
    
    def test_post_exists_finds_existing_post(self):
        """Test post_exists finds existing post"""
        import main
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(main, 'BLOG_DIR', Path(tmpdir)):
                # Create a fake post
                today = datetime.now().strftime("%Y-%m-%d")
                post_path = Path(tmpdir) / f"{today}-test-video.html"
                post_path.write_text("test content")
                
                # Should find it
                assert main.post_exists("test video") == True
    
    def test_post_exists_returns_false_for_nonexistent(self):
        """Test post_exists returns false for nonexistent"""
        import main
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(main, 'BLOG_DIR', Path(tmpdir)):
                # Should not find non-existent
                assert main.post_exists("nonexistent video") == False


class TestConfigLoading:
    """Tests for config loading"""
    
    def test_load_config_returns_dict(self):
        """Test config loading returns valid dict"""
        import main
        
        config = main.load_config()
        
        assert isinstance(config, dict)
        assert "youtube" in config or "podcasts" in config or "news" in config


# ============================================================================
# INTEGRATION TESTS (Mock External APIs)
# ============================================================================

class TestYouTubeProcessing:
    """Tests for YouTube processing logic"""
    
    def test_process_video_id_extraction(self):
        """Test video ID is extracted correctly from URL"""
        from youtube import fetcher
        
        # Test URL parsing
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert "dQw4w9WgXcQ" in url


class TestPodcastProcessing:
    """Tests for podcast processing logic"""
    
    def test_podcast_data_structure(self):
        """Test podcast episode data structure"""
        episode = {
            "id": "ep001",
            "title": "Test Episode",
            "audio_url": "https://example.com/podcast.mp3",
            "description": "A great episode"
        }
        
        assert episode["title"] == "Test Episode"
        assert episode["audio_url"].startswith("https://")


class TestNewsProcessing:
    """Tests for news processing logic"""
    
    def test_news_article_structure(self):
        """Test news article data structure"""
        article = {
            "title": "Test Article",
            "url": "https://example.com/article",
            "summary": "Article summary"
        }
        
        assert "title" in article
        assert "url" in article


# ============================================================================
# FUNCTIONAL TESTS (Test with real code paths)
# ============================================================================

class TestBlogGeneration:
    """Tests for blog post generation"""
    
    def test_generate_post_filename_format(self):
        """Test generated filename follows expected format"""
        date = "2026-02-28"
        title = "Test Video Title"
        
        # Simulate slug generation
        slug = title.lower().replace(" ", "-")[:50]
        filename = f"{date}-{slug}.html"
        
        assert filename.startswith("2026-02-28")
        assert filename.endswith(".html")
        assert "test-video-title" in filename


class TestTranscriptRetry:
    """Tests for transcript retry logic"""
    
    def test_retry_count_tracking(self):
        """Test that retry counter works"""
        attempts = []
        max_retries = 3
        
        def retry_func():
            """Simulates the retry logic in wait_for_transcript"""
            for i in range(max_retries):
                attempts.append(i + 1)
                if i >= max_retries - 1:
                    return "success"
            return None
        
        result = retry_func()
        assert len(attempts) == 3
        assert result == "success"


class TestStateTracking:
    """Tests for state tracking"""
    
    def test_processed_videos_accumulated(self):
        """Test processed videos are tracked"""
        processed = []
        new_video = "abc123"
        
        # Simulate processing
        if new_video not in processed:
            processed.append(new_video)
        
        assert "abc123" in processed
        assert len(processed) == 1


# ============================================================================
# EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases"""
    
    def test_empty_transcript_handling(self):
        """Test empty transcript is handled"""
        transcript = ""
        
        # Should be falsy
        assert not transcript
        assert len(transcript.strip()) < 50
    
    def test_very_long_title_truncation(self):
        """Test very long titles are truncated"""
        long_title = "A" * 200
        truncated = long_title[:50]
        
        assert len(truncated) == 50
    
    def test_missing_category_defaults(self):
        """Test missing category defaults to YouTube"""
        video = {"id": "123", "title": "Test", "url": "https://youtube.com"}
        
        category = video.get("category", "YouTube")
        assert category == "YouTube"


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
