#!/usr/bin/env python3
"""YouTube Video Transcription"""
import subprocess
import sys
import re
import glob
from pathlib import Path
from typing import List, Optional

USE_WHISPER = False


def cleanup_vtt(text: str) -> str:
    """Remove VTT timing tags and convert to plain text"""
    # Remove WEBVTT header
    text = re.sub(r'^WEBVTT.*$', '', text, flags=re.MULTILINE)
    # Remove timing lines like 00:00:00.719 --> 00:00:03.030
    text = re.sub(r'\d{2}:\d{2}:\d{2}\.\d{3}.*', '', text, flags=re.MULTILINE)
    # Remove VTT tags like <00:00:01.040><c>
    text = re.sub(r'<[^>]+>', '', text)
    # Clean up extra whitespace
    text = re.sub(r'\n\n+', '\n', text)
    return text.strip()


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
        result = subprocess.run([
            "yt-dlp",
            "--write-subs",
            "--write-auto-subs",
            "--sub-lang", "en",
            "--skip-download",
            "--output", "/tmp/transcript",
            video_url
        ], capture_output=True, text=True, timeout=120)
        
        # Find the transcript file (.vtt or .srt)
        subs = glob.glob("/tmp/transcript*.en.vtt") + glob.glob("/tmp/transcript*.en.srt")
        
        if subs:
            transcript = ""
            for sub_file in sorted(subs):
                with open(sub_file) as f:
                    transcript += f.read() + "\n"
            # Clean up VTT formatting
            transcript = cleanup_vtt(transcript)
            return transcript
        
        return None
    
    except Exception as e:
        print(f"yt-dlp transcript error: {e}")
        return None


def transcribe_chunk(chunk_path: str) -> str:
    """Transcribe a single audio chunk"""
    if USE_WHISPER:
        text = transcribe_with_whisper(chunk_path)
        if text:
            return text
    return ""


def transcribe_video(video_url: str, chunk_paths: List[str]) -> str:
    """Transcribe all chunks and combine"""
    if not chunk_paths:
        return transcribe_with_ytdlp(video_url) or ""
    
    full_transcript = ""
    
    for i, chunk in enumerate(chunk_paths):
        print(f"Transcribing chunk {i+1}/{len(chunk_paths)}...")
        text = transcribe_chunk(chunk)
        if text:
            full_transcript += text + "\n"
    
    if not full_transcript.strip():
        print("Falling back to yt-dlp transcript...")
        full_transcript = transcribe_with_ytdlp(video_url) or ""
    
    return full_transcript


if __name__ == "__main__":
    if len(sys.argv) > 1:
        video_url = sys.argv[1]
        transcript = transcribe_video(video_url, [])
        print(f"Transcript length: {len(transcript)} chars")
        print(transcript[:500])
