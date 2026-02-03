"""YouTube transcript fetching client using youtube-transcript-api."""

import os
import re
from typing import Optional
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)


def extract_video_id(url: str) -> Optional[str]:
    """Extract YouTube video ID from various URL formats.

    Supports:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - https://www.youtube.com/v/VIDEO_ID
    - Just the video ID itself
    """
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$',  # Just the video ID
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


def get_youtube_api():
    """Create YouTubeTranscriptApi instance with proxy if configured."""
    proxy_username = os.environ.get("WEBSHARE_PROXY_USERNAME")
    proxy_password = os.environ.get("WEBSHARE_PROXY_PASSWORD")

    if proxy_username and proxy_password:
        # Use Webshare rotating proxies to avoid YouTube IP blocking
        proxy_config = WebshareProxyConfig(
            proxy_username=proxy_username,
            proxy_password=proxy_password,
        )
        return YouTubeTranscriptApi(proxy_config=proxy_config)
    else:
        # No proxy configured - works locally but may be blocked on cloud
        return YouTubeTranscriptApi()


def fetch_transcript(url: str) -> dict:
    """Fetch transcript for a YouTube video.

    Args:
        url: YouTube video URL or video ID

    Returns:
        dict with keys:
            - success: bool
            - video_id: str (if successful)
            - transcript: str (if successful)
            - error: str (if failed)
    """
    video_id = extract_video_id(url)

    if not video_id:
        return {
            "success": False,
            "error": "Could not extract video ID from URL. Please provide a valid YouTube URL."
        }

    try:
        # Create API instance with optional proxy support
        api = get_youtube_api()

        # Try to get transcript with language fallbacks
        transcript_list = api.list(video_id)

        # Try to find English transcript first
        transcript = None
        for lang in ['en', 'en-US', 'en-GB']:
            try:
                transcript = transcript_list.find_transcript([lang])
                break
            except NoTranscriptFound:
                continue

        # If no English, try auto-generated
        if transcript is None:
            try:
                transcript = transcript_list.find_generated_transcript(['en'])
            except NoTranscriptFound:
                pass

        # If still nothing, get any available transcript and translate
        if transcript is None:
            try:
                transcript = next(iter(transcript_list))
                if transcript.language_code != 'en':
                    transcript = transcript.translate('en')
            except StopIteration:
                return {
                    "success": False,
                    "video_id": video_id,
                    "error": "No transcripts available for this video."
                }

        # Fetch the actual transcript data
        transcript_data = transcript.fetch()

        # Combine all text segments
        full_text = " ".join(snippet.text for snippet in transcript_data)

        return {
            "success": True,
            "video_id": video_id,
            "transcript": full_text
        }

    except TranscriptsDisabled:
        return {
            "success": False,
            "video_id": video_id,
            "error": "Transcripts are disabled for this video."
        }
    except VideoUnavailable:
        return {
            "success": False,
            "video_id": video_id,
            "error": "Video is unavailable. It may be private or deleted."
        }
    except Exception as e:
        return {
            "success": False,
            "video_id": video_id,
            "error": f"Failed to fetch transcript: {str(e)}"
        }


if __name__ == "__main__":
    # Quick test
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    result = fetch_transcript(test_url)
    print(result)
