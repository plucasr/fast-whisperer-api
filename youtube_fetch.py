from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)
import re


def get_youtube_transcript(url, languages=["en", "pt", "es"]):
    """
    Fetches the transcript for a YouTube video.

    Args:
        url (str): The YouTube video URL
        languages (list): List of preferred language codes (default: ['en', 'pt', 'es'])

    Returns:
        str: The full transcript text, or None if unavailable
    """
    try:
        # Extract video ID from URL
        video_id = extract_video_id(url)

        if not video_id:
            print("Invalid YouTube URL")
            return None

        print(f"Fetching transcript for video ID: {video_id}")

        # Create an instance and list available transcripts
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)

        # Try to find a transcript in one of the preferred languages
        transcript = None
        try:
            transcript = transcript_list.find_transcript(languages)
        except NoTranscriptFound:
            # If no manual transcript found, try auto-generated
            try:
                transcript = transcript_list.find_generated_transcript(languages)
            except NoTranscriptFound:
                print(f"No transcript found in languages: {languages}")
                return None

        # Fetch the actual transcript data
        transcript_data = transcript.fetch()

        # Combine all transcript segments into a single string
        transcript_text = " ".join([segment.text for segment in transcript_data])

        return transcript_text

    except TranscriptsDisabled:
        print(f"Transcripts are disabled for this video (ID: {video_id})")
        return None
    except VideoUnavailable:
        print(f"Video is unavailable (ID: {video_id})")
        return None
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        return None


def extract_video_id(url):
    """
    Extracts the video ID from various YouTube URL formats.

    Args:
        url (str): YouTube URL

    Returns:
        str: Video ID or None if invalid
    """
    # Common YouTube URL patterns
    patterns = [
        r"(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)",
        r"youtube\.com\/embed\/([^&\n?#]+)",
        r"youtube\.com\/v\/([^&\n?#]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


# Example usage
if __name__ == "__main__":
    # Example YouTube URL - replace with your video
    video_url = "https://www.youtube.com/watch?v=muCxEjpYzks"

    print("YouTube Transcript Fetcher")
    print("-" * 50)

    transcript = get_youtube_transcript(video_url)

    if transcript:
        print("\nTranscript retrieved successfully!")
        print(f"\nFirst 200 characters:\n{transcript[:200]}...")
        print(f"\nTotal length: {len(transcript)} characters")
    else:
        print("\nFailed to retrieve transcript.")
