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
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
)
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
        # 1. List all available transcripts using the modern method (requires updated library)
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # 2. Try to find the best English track (Manual preferred, then Auto)
        try:
            # We explicitly search for English ('en' or 'en-US')
            # This will automatically prioritize manual over auto-generated.
            transcript = transcript_list.find_transcript(["en", "en-US"])
            print(
                f"INFO: Found English transcript. Generated: {transcript.is_generated}"
            )

        except NoTranscriptFound:
            print(
                "WARNING: English track not found. Searching for any available auto-generated track."
            )

            # 3. Fallback: Search for ANY auto-generated track, regardless of language
            try:
                # Find the first available generated transcript
                transcript = next(t for t in transcript_list if t.is_generated)
                print(
                    f"INFO: Using auto-generated track in language: {transcript.language}"
                )

            except (StopIteration, NoTranscriptFound):
                # 4. Final Fail: No usable transcript (manual or auto) was found.
                raise HTTPException(
                    status_code=404,
                    detail="No subtitles (manual or auto-generated) are available for this video.",
                )

        # 5. Fetch and Format the Transcript
        raw_transcript = transcript.fetch()
        full_transcription = " ".join([item["text"] for item in raw_transcript])

        print("INFO: Transcription (from subtitles) complete.")

        return TranscriptionResponse(
            transcription=full_transcription, youtube_url=request.youtube_url
        )

    # 6. Catch Specific Library Errors
    except TranscriptsDisabled:
        raise HTTPException(
            status_code=404,
            detail="Transcripts are explicitly disabled for this video by the creator.",
        )
    except Exception as e:
        # Catch network errors, IP blocks, or other general failures
        error_type = type(e).__name__
        print(f"FATAL ERROR: {error_type} - {str(e)}")
        print(f"Full Traceback:\n{traceback.format_exc()}")

        # NOTE: If this Exception is still raised, and it's not a library error,
        # it might be due to YouTube blocking the IP of your cloud service (Render).
        raise HTTPException(
            status_code=500,
            detail=f"An internal error occurred: {error_type}. (Check dependency version/IP status)",
        )


# --- Clean up the 'finally' block as it's no longer needed ---
# Note: The original file cleanup logic is removed because we don't download files.
