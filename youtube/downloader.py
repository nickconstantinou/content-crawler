#!/usr/bin/env python3
"""YouTube Video Downloader + Chunking"""
import subprocess
import os
import sys
from pathlib import Path
from typing import List, Optional

# Base directory for downloads
DOWNLOADS_DIR = Path(__file__).parent.parent / "downloads"


def download_audio(video_url: str, output_path: str) -> Optional[str]:
    """Download audio from YouTube video"""
    try:
        result = subprocess.run([
            "yt-dlp",
            "-x",  # Extract audio
            "--audio-format", "mp3",
            "--audio-quality", "0",  # Best quality
            "-o", output_path,
            video_url
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            return output_path
        else:
            print(f"Download failed: {result.stderr}")
            return None
    
    except Exception as e:
        print(f"Error downloading {video_url}: {e}")
        return None


def get_video_duration(video_url: str) -> int:
    """Get video duration in seconds"""
    try:
        result = subprocess.run([
            "yt-dlp",
            "--get-duration",
            video_url
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            duration_str = result.stdout.strip()
            # Parse duration (could be HH:MM:SS or seconds)
            parts = duration_str.split(":")
            if len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            elif len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            else:
                return int(parts[0])
        return 0
    except:
        return 0


def chunk_audio(audio_path: str, chunk_minutes: int = 10) -> List[str]:
    """Split audio file into chunks using ffmpeg"""
    import re
    
    # Get duration in seconds
    result = subprocess.run([
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_path
    ], capture_output=True, text=True)
    
    try:
        total_seconds = float(result.stdout.strip())
    except:
        print(f"Could not get duration for {audio_path}")
        return [audio_path]
    
    chunk_seconds = chunk_minutes * 60
    num_chunks = int(total_seconds / chunk_seconds) + 1
    
    chunk_paths = []
    base_path = audio_path.replace(".mp3", "")
    
    for i in range(num_chunks):
        start_time = i * chunk_seconds
        chunk_path = f"{base_path}_chunk{i+1}.mp3"
        
        # Skip if chunk already exists
        if os.path.exists(chunk_path):
            chunk_paths.append(chunk_path)
            continue
        
        result = subprocess.run([
            "ffmpeg",
            "-i", audio_path,
            "-ss", str(start_time),
            "-t", str(chunk_seconds),
            "-acodec", "copy",
            "-y",  # Overwrite
            chunk_path
        ], capture_output=True, text=True)
        
        if result.returncode == 0 and os.path.exists(chunk_path):
            chunk_paths.append(chunk_path)
    
    return chunk_paths


def download_and_chunk(video_url: str, video_id: str, chunk_minutes: int = 10) -> List[str]:
    """Download video audio and chunk it"""
    # Create directory for this video
    video_dir = DOWNLOADS_DIR / video_id
    video_dir.mkdir(parents=True, exist_ok=True)
    
    audio_path = str(video_dir / "audio.mp3")
    
    # Download audio
    result = download_audio(video_url, audio_path)
    if not result:
        return []
    
    # Chunk audio
    chunks = chunk_audio(audio_path, chunk_minutes)
    
    print(f"Downloaded and chunked {video_id} into {len(chunks)} pieces")
    return chunks


def cleanup_old_downloads(days: int = 7):
    """Remove downloads older than N days"""
    import time
    import shutil
    
    if not DOWNLOADS_DIR.exists():
        return
    
    now = time.time()
    cutoff = now - (days * 86400)
    
    for item in DOWNLOADS_DIR.iterdir():
        if item.is_dir():
            mtime = item.stat().st_mtime
            if mtime < cutoff:
                shutil.rmtree(item)
                print(f"Cleaned up: {item.name}")


if __name__ == "__main__":
    # Test
    if len(sys.argv) > 1:
        video_url = sys.argv[1]
        chunks = download_and_chunk(video_url, "test_video")
        print(f"Created {len(chunks)} chunks")
