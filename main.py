import os
import uuid
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from faster_whisper import WhisperModel
import yt_dlp

# --- Configuration ---
load_dotenv()

# Load the Whisper model from environment variable or use a default
MODEL_NAME = os.getenv("WHISPER_MODEL", "tiny.en")

# Create a directory for temporary audio files if it doesn't exist
TEMP_AUDIO_DIR = Path("temp_audio")
TEMP_AUDIO_DIR.mkdir(exist_ok=True)

# Path for cookies.txt from Render.com secrets or fallback to local file
COOKIE_FILE_PATH = Path("/etc/secrets/cookies.txt")

# --- Model Loading ---
# This is a heavy object, so we load it once and reuse it for all requests.
# This might take a moment when the application starts.
try:
    print(f"Loading Whisper model: {MODEL_NAME}...")
    whisper_model = WhisperModel(MODEL_NAME, device="cpu", compute_type="int8")
    print("Whisper model loaded successfully.")
except Exception as e:
    print(f"Error loading Whisper model: {e}")
    # If the model fails to load, the app can't function.
    whisper_model = None


# --- FastAPI Application ---
app = FastAPI(
    title="YouTube Transcription API",
    description="An API to transcribe audio from YouTube videos using faster-whisper.",
    version="0.1.0",
)


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
    Downloads audio from a YouTube URL, transcribes it, and returns the text.
    """
    if not whisper_model:
        raise HTTPException(status_code=500, detail="Whisper model is not available.")

    # Generate a unique filename for the temporary audio file
    unique_id = uuid.uuid4()
    audio_filename = f"{unique_id}.mp3"
    audio_filepath = TEMP_AUDIO_DIR / audio_filename
    
    # Configure yt-dlp to download audio-only in mp3 format
    ydl_opts = {
        "format": "bestaudio/best",
        "cookiefile": str(COOKIE_FILE_PATH),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "outtmpl": str(audio_filepath.with_suffix("")),  # yt-dlp adds the extension
        "quiet": True,
    }

    try:
        # Download the audio from YouTube
        print(f"Downloading audio from: {request.youtube_url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([str(request.youtube_url)])
        print(f"Audio downloaded to: {audio_filepath}")

        if not audio_filepath.exists():
            raise HTTPException(
                status_code=500, detail="Failed to download audio file."
            )

        # Transcribe the downloaded audio file
        print(f"Transcribing audio file: {audio_filepath}")
        segments, info = whisper_model.transcribe(str(audio_filepath), beam_size=5)
        print(
            f"Transcription language: {info.language} with probability {info.language_probability}"
        )

        # Concatenate the transcribed segments
        transcription_parts = [segment.text for segment in segments]
        full_transcription = "".join(transcription_parts).strip()
        print("Transcription complete.")

        return TranscriptionResponse(
            transcription=full_transcription, youtube_url=request.youtube_url
        )

    except Exception as e:
        # Log the error for debugging
        print(f"An error occurred: {e}")
        raise HTTPException(
            status_code=500, detail=f"An internal error occurred: {str(e)}"
        )

    finally:
        # Clean up the temporary audio file
        if audio_filepath.exists():
            try:
                os.remove(audio_filepath)
                print(f"Cleaned up temporary file: {audio_filepath}")
            except OSError as e:
                # Log if cleanup fails but don't crash the request
                print(f"Error removing file {audio_filepath}: {e}")
