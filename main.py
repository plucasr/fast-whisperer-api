import os
import uuid
import shutil
import traceback
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
# NOTE: Removed Faster Whisper import as it's not strictly used for text processing
# You can keep it if you plan to still use it for audio/file processing in other endpoints.
# from faster_whisper import WhisperModel

# --- New Import for Subtitles ---
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
from urllib.parse import urlparse, parse_qs
# ---------------------------------

# --- Configuration ---
load_dotenv()

# Load the Whisper model from environment variable or use a default
# WARNING: Since we are not using the model for transcription, this should be removed
# if the transcription logic is ONLY based on subtitles.
# MODEL_NAME = os.getenv("WHISPER_MODEL", "tiny.en")

# Create a directory for temporary audio files if it doesn't exist
TEMP_AUDIO_DIR = Path("temp_audio")
TEMP_AUDIO_DIR.mkdir(exist_ok=True)

# Cookie paths are now obsolete and removed for simplicity
# SECRETS_COOKIE_PATH = Path("/etc/secrets/cookies.txt")
# COOKIE_FILE_PATH = Path("./cookies.txt")
# SECRETS_DIR = Path("/etc/secrets")

# --- Helper Functions (Simplified) ---
# Removed: list_secrets_directory, check_cookies_file, copy_cookies_file
# You can remove these functions entirely from your code.


def extract_video_id(url: str) -> str:
    """Extracts the YouTube video ID from various URL formats."""
    parsed_url = urlparse(url)
    if parsed_url.hostname in ("www.youtube.com", "youtube.com", "m.youtube.com"):
        if parsed_url.path == "/watch":
            # Case: https://www.youtube.com/watch?v=VIDEO_ID
            query = parse_qs(parsed_url.query)
            return query.get("v", [None])[0]
    elif parsed_url.hostname == "youtu.be":
        # Case: https://youtu.be/VIDEO_ID
        return parsed_url.path[1:]

    # Handle other cases or return None
    return None


# --- Model Loading (Simplified) ---
# Removed the Whisper model loading if not used for audio.
# If you plan to use Whisper to clean up the transcript text, keep it.
whisper_model = None  # Set to None for this subtitle-only implementation

# --- FastAPI Application ---
app = FastAPI(
    title="YouTube Transcription API (Subtitle-Based)",
    description="An API to transcribe (fetch subtitles) from YouTube videos.",
    version="0.1.0",
)


@app.on_event("startup")
async def startup_event():
    """
    Runs at application startup (now simplified as cookie handling is removed).
    """
    print("Startup complete. Running in subtitle-fetching mode.")


# --- Pydantic Models ---
class TranscriptionRequest(BaseModel):
    youtube_url: HttpUrl


class TranscriptionResponse(BaseModel):
    transcription: str
    youtube_url: HttpUrl


# --- API Endpoints ---
@app.get("/")
def read_root():
    """
    Root endpoint to welcome users to the API.
    """
    return {"message": "Welcome to the YouTube Transcription API"}


@app.post("/transcribe", response_model=TranscriptionResponse)
async def create_transcription(request: TranscriptionRequest):
    """
    Fetches the transcript/subtitles from a YouTube URL and returns the text.
    """

    video_url = str(request.youtube_url)
    video_id = extract_video_id(video_url)

    if not video_id:
        raise HTTPException(
            status_code=400, detail="Invalid YouTube URL: Could not extract video ID."
        )

    try:
        # Try to use list_transcripts (newer API) if available, otherwise fall back to get_transcript
        raw_transcript = None
        
        # Method 1: Try using list_transcripts (for newer versions of youtube-transcript-api)
        try:
            if hasattr(YouTubeTranscriptApi, 'list_transcripts'):
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                
                # Try to find the best English transcript (Manual preferred, Auto fallback)
                try:
                    # Try to find a manual or auto-generated English track
                    transcript = transcript_list.find_transcript(["en", "en-US"])
                    print(
                        f"Transcript found: Language='{transcript.language}', Generated={transcript.is_generated}"
                    )
                    raw_transcript = transcript.fetch()
                except Exception as find_error:
                    # Fallback: Check if there's any auto-generated transcript available
                    try:
                        # Find the first available generated transcript
                        transcript = next(t for t in transcript_list if t.is_generated)
                        print(
                            f"Only auto-generated track found: Language='{transcript.language}'"
                        )
                        raw_transcript = transcript.fetch()
                    except StopIteration:
                        # If no transcripts are found, fall through to get_transcript method
                        print("No transcripts found via list_transcripts, trying get_transcript...")
                        pass
            else:
                print("list_transcripts not available, using get_transcript method...")
        except Exception as list_error:
            print(f"Error with list_transcripts: {list_error}, trying get_transcript method...")
        
        # Method 2: Fallback to get_transcript (simpler, works with older versions)
        if raw_transcript is None:
            try:
                # Try English first
                raw_transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'en-US'])
                print("Fetched English transcript using get_transcript")
            except Exception:
                try:
                    # Try auto-generated transcript
                    raw_transcript = YouTubeTranscriptApi.get_transcript(video_id)
                    print("Fetched auto-generated transcript using get_transcript")
                except Exception as get_error:
                    raise HTTPException(
                        status_code=404,
                        detail=f"No subtitles (manual or auto-generated) are available for this video. Error: {str(get_error)}"
                    )
        
        # Format the content into a single block of text
        if raw_transcript:
            # raw_transcript is a list of dicts with 'text', 'start', 'duration'
            # Format it into a single block of text
            full_transcription = " ".join([item['text'] for item in raw_transcript])
        else:
            raise HTTPException(
                status_code=404,
                detail="No subtitles could be retrieved for this video."
            )

        print("Transcription (from subtitles) complete.")

        return TranscriptionResponse(
            transcription=full_transcription, youtube_url=request.youtube_url
        )

    except TranscriptsDisabled:
        raise HTTPException(
            status_code=404,
            detail="Transcripts are explicitly disabled for this video by the creator.",
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log the error for debugging with full details
        error_type = type(e).__name__
        error_msg = str(e)
        error_traceback = traceback.format_exc()
        
        print(f"\n{'=' * 50}")
        print(f"ERROR OCCURRED")
        print(f"{'=' * 50}")
        print(f"Error Type: {error_type}")
        print(f"Error Message: {error_msg}")
        print(f"Error Args: {e.args}")
        if hasattr(e, 'errno'):
            print(f"Error Code: {e.errno}")
        print(f"\nFull Traceback:\n{error_traceback}")
        print(f"{'=' * 50}\n")
        
        raise HTTPException(
            status_code=500, detail=f"An internal error occurred: {error_msg}"
        )


# --- Clean up the 'finally' block as it's no longer needed ---
# Note: The original file cleanup logic is removed because we don't download files.
