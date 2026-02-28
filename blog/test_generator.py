"""Tests for blog generator functions"""
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import sys

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from blog.generator import (
    slugify,
    generate_youtube_post,
    generate_news_post,
    save_post,
    save_to_obsidian,
)


class TestSlugify:
    """Tests for slugify() function"""

    def test_basic_slug(self):
        """Basic slug conversion"""
        assert slugify("Hello World") == "hello-world"

    def test_special_chars_removed(self):
        """Special characters are removed"""
        assert slugify("Test! @#$% Post") == "test-post"

    def test_multiple_spaces_hyphens(self):
        """Multiple spaces become single hyphens"""
        assert slugify("hello   world  test") == "hello-world-test"

    def test_truncation(self):
        """Slug is truncated to 50 chars"""
        long_title = "a" * 60
        assert len(slugify(long_title)) == 50


class TestGenerateYoutubePost:
    """Tests for generate_youtube_post() function"""

    def test_generates_valid_html(self):
        """Returns valid HTML structure"""
        filename, html = generate_youtube_post(
            title="Test Video",
            summary="This is a **test** summary.",
            category="AI",
            video_url="https://www.youtube.com/watch?v=abc123",
            date="2026-02-25"
        )

        assert filename == "2026-02-25-test-video.html"
        assert "<!DOCTYPE html>" in html
        assert "<title>Test Video | Nick's Blog</title>" in html
        assert 'class="meta">2026-02-25 • AI</p>' in html

    def test_video_embed_extraction(self):
        """Extracts video ID for embed"""
        filename, html = generate_youtube_post(
            title="Test",
            summary="Summary",
            category="Tech",
            video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        )

        assert "dQw4w9WgXcQ" in html

    def test_default_date(self):
        """Uses current date if not provided"""
        filename, html = generate_youtube_post(
            title="Test",
            summary="Summary",
            category="AI",
            video_url="https://youtube.com/watch?v=abc"
        )

        today = datetime.now().strftime("%Y-%m-%d")
        assert filename.startswith(today)


class TestGenerateNewsPost:
    """Tests for generate_news_post() function"""

    def test_generates_news_html(self):
        """Generates HTML for news articles"""
        articles = [
            {"title": "Article 1", "url": "https://example.com/1"},
            {"title": "Article 2", "url": "https://example.com/2"},
        ]

        filename, html = generate_news_post(
            source="HackerNews",
            articles=articles,
            date="2026-02-25"
        )

        assert filename == "2026-02-25-hackernews-news.html"
        assert "Article 1" in html
        assert "Article 2" in html

    def test_empty_articles(self):
        """Handles empty articles list"""
        filename, html = generate_news_post(
            source="Test",
            articles=[]
        )

        assert filename is not None


class TestSavePost:
    """Tests for save_post() function"""

    def test_saves_file(self):
        """Saves content to file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            posts_dir = Path(tmpdir)

            filepath = save_post(
                "test.html",
                "<html>Test</html>",
                posts_dir=posts_dir
            )

            assert filepath.exists()
            assert filepath.read_text() == "<html>Test</html>"

    def test_creates_directory(self):
        """Creates posts directory if not exists"""
        with tempfile.TemporaryDirectory() as tmpdir:
            posts_dir = Path(tmpdir) / "new" / "dir"

            save_post("test.html", "content", posts_dir=posts_dir)

            assert posts_dir.exists()
            assert (posts_dir / "test.html").exists()


class TestSaveToObsidian:
    """Tests for save_to_obsidian() function"""

    def test_saves_markdown_to_vault(self):
        """Saves Markdown with frontmatter to Obsidian vault"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Patch the OBSIDIAN_VAULT path
            import blog.generator
            original_vault = blog.generator.OBSIDIAN_VAULT
            blog.generator.OBSIDIAN_VAULT = Path(tmpdir)

            try:
                filepath = save_to_obsidian(
                    title="Test Video",
                    summary="This is a test summary.",
                    category="AI",
                    video_url="https://youtube.com/watch?v=abc",
                    date="2026-02-25"
                )

                assert filepath.exists()
                content = filepath.read_text()

                # Check frontmatter
                assert "---" in content
                assert "date: 2026-02-25" in content
                assert 'title: "Test Video"' in content
                assert "type: blog" in content

                # Check content
                assert "This is a test summary." in content
                assert "https://youtube.com/watch?v=abc" in content
            finally:
                blog.generator.OBSIDIAN_VAULT = original_vault

    def test_sets_type_behind_scenes(self):
        """Sets type to behind-the-scenes for behind the scenes category"""
        with tempfile.TemporaryDirectory() as tmpdir:
            import blog.generator
            original_vault = blog.generator.OBSIDIAN_VAULT
            blog.generator.OBSIDIAN_VAULT = Path(tmpdir)

            try:
                filepath = save_to_obsidian(
                    title="Behind the Scenes",
                    summary="Summary",
                    category="Behind The Scenes",
                    date="2026-02-25"
                )

                content = filepath.read_text()
                assert "type: behind-the-scenes" in content
            finally:
                blog.generator.OBSIDIAN_VAULT = original_vault

    def test_avoids_overwrite(self):
        """Increments counter when file exists"""
        with tempfile.TemporaryDirectory() as tmpdir:
            import blog.generator
            original_vault = blog.generator.OBSIDIAN_VAULT
            blog.generator.OBSIDIAN_VAULT = Path(tmpdir)

            try:
                # Create first file
                save_to_obsidian(
                    title="Test",
                    summary="Summary 1",
                    category="AI",
                    date="2026-02-25"
                )

                # Create second - should get -1 suffix
                filepath2 = save_to_obsidian(
                    title="Test",
                    summary="Summary 2",
                    category="AI",
                    date="2026-02-25"
                )

                assert "-1.md" in filepath2.name
            finally:
                blog.generator.OBSIDIAN_VAULT = original_vault


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
