#!/usr/bin/env python3
"""YouTube Video Transcription"""
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

# Try whisper, fall back to yt-dlp transcript
USE_WHISPER = False  # Set to True if whisper is installed


def transcribe_with_whisper(audio_path: str) -> Optional[str]:
    """Transcribe audio using whisper (if available)"""
    try:
        import whisper
        model = whisper.load_model("base")
        result = model.transcribe(audio_path)
        return result["text"]
    except ImportError:
        return None
    except Exception as e:
        print(f"Whisper error: {e}")
        return None


def transcribe_with_ytdlp(video_url: str) -> Optional[str]:
    """Transcribe using yt-dlp's built-in transcript feature"""
    try:
        # Get transcript
        result = subprocess.run([
            "yt-dlp",
            "--write-subs",
            "--write-auto-subs",
            "--sub-lang", "en",
            "--skip-download",
            "--output", "/tmp/transcript",
            video_url
        ], capture_output=True, text=True, timeout=120)
        
        # Find the transcript file
        import glob
        subs = glob.glob("/tmp/transcript.*.en.srt") + glob.glob("/tmp/transcript.*.en.vtt")
        
        if subs:
            # Read and combine transcript
            transcript = ""
            for sub_file in sorted(subs):
                with open(sub_file) as f:
                    transcript += f.read() + "\n"
            return transcript
        
        return None
    
    except Exception as e:
        print(f"yt-dlp transcript error: {e}")
        return None


def transcribe_chunk(chunk_path: str) -> str:
    """Transcribe a single audio chunk"""
    # Try whisper first
    if USE_WHISPER:
        text = transcribe_with_whisper(chunk_path)
        if text:
            return text
    
    # Fall back to yt-dlp (won't work for chunks, but try anyway)
    # For chunks, we need a different approach
    # For now, return empty - chunks need whisper
    return ""


def transcribe_video(video_url: str, chunk_paths: List[str]) -> str:
    """Transcribe all chunks and combine"""
    if not chunk_paths:
        # Try direct transcript if no chunks
        return transcribe_with_ytdlp(video_url) or ""
    
    full_transcript = ""
    
    for i, chunk in enumerate(chunk_paths):
        print(f"Transcribing chunk {i+1}/{len(chunk_paths)}...")
        text = transcribe_chunk(chunk)
        if text:
            full_transcript += text + "\n"
    
    # If whisper not available, try yt-dlp on full video as fallback
    if not full_transcript.strip():
        print("Falling back to yt-dlp transcript...")
        full_transcript = transcribe_with_ytdlp(video_url) or ""
    
    return full_transcript


if __name__ == "__main__":
    # Test
    if len(sys.argv) > 1:
        video_url = sys.argv[1]
        transcript = transcribe_video(video_url, [])
        print(f"Transcript length: {len(transcript)} chars")
