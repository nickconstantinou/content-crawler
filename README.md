# Content Crawler

Config-driven content fetching, transcription, and blog post generation.

## Setup

```bash
pip install -r requirements.txt
```

## Configuration

Edit `sources.yaml` to add new content sources:

```yaml
youtube:
  channels:
    - id: "CHANNEL_ID"
      name: "Channel Name"
      category: "Category"

podcasts:
  - rss: "https://feed.url"
    name: "Podcast Name"

news:
  - rss: "https://rss.url"
    name: "News Source"
```

## Usage

```bash
# Run full crawl
python main.py
```

## Environment Variables

- `MINIMAX_API_KEY` - MiniMax API key for summaries
- `GITHUB_TOKEN` - GitHub token for pushing

## Dependencies

- pyyaml
- requests
- ffmpeg (for audio chunking)
- yt-dlp (for YouTube/podcast fetching)
