import os
import uuid
import shutil
import traceback
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

# Path for cookies.txt from Render.com secrets (read-only)
SECRETS_COOKIE_PATH = Path("/etc/secrets/cookies.txt")
# Writable cookies file path in app root directory
COOKIE_FILE_PATH = Path("./cookies.txt")
SECRETS_DIR = Path("/etc/secrets")

# --- Helper Functions ---
def list_secrets_directory():
    """
    Lists and logs all files in the /etc/secrets/ directory.
    """
    print(f"\n{'='*50}")
    print(f"Listing contents of: {SECRETS_DIR}")
    print(f"{'='*50}")
    
    try:
        if SECRETS_DIR.exists() and SECRETS_DIR.is_dir():
            files = list(SECRETS_DIR.iterdir())
            if files:
                print(f"Found {len(files)} file(s) in {SECRETS_DIR}:")
                for file in files:
                    file_type = "Directory" if file.is_dir() else "File"
                    size = file.stat().st_size if file.is_file() else None
                    size_str = f" ({size} bytes)" if size is not None else ""
                    print(f"  - {file.name} ({file_type}){size_str}")
            else:
                print(f"Directory {SECRETS_DIR} exists but is empty.")
        else:
            print(f"Directory {SECRETS_DIR} does not exist or is not a directory.")
    except PermissionError:
        print(f"Permission denied: Cannot access {SECRETS_DIR}")
    except Exception as e:
        print(f"Error listing {SECRETS_DIR}: {e}")
    
    print(f"{'='*50}\n")


def check_cookies_file():
    """
    Checks if the cookies.txt file exists in secrets and logs the result.
    """
    print(f"\n{'='*50}")
    print(f"Checking for cookies file: {SECRETS_COOKIE_PATH}")
    print(f"{'='*50}")
    
    try:
        if SECRETS_COOKIE_PATH.exists():
            if SECRETS_COOKIE_PATH.is_file():
                file_size = SECRETS_COOKIE_PATH.stat().st_size
                print(f"✓ cookies.txt exists in secrets")
                print(f"  Path: {SECRETS_COOKIE_PATH.absolute()}")
                print(f"  Size: {file_size} bytes")
            else:
                print(f"✗ Path exists but is not a file: {SECRETS_COOKIE_PATH}")
        else:
            print(f"✗ cookies.txt does not exist at: {SECRETS_COOKIE_PATH}")
    except PermissionError:
        print(f"✗ Permission denied: Cannot access {SECRETS_COOKIE_PATH}")
    except Exception as e:
        print(f"✗ Error checking cookies file: {e}")
    
    print(f"{'='*50}\n")


def copy_cookies_file():
    """
    Copies the cookies file from /etc/secrets/ to a writable location in the app root.
    """
    print(f"\n{'='*50}")
    print(f"Copying cookies file to writable location")
    print(f"{'='*50}")
    
    try:
        if SECRETS_COOKIE_PATH.exists() and SECRETS_COOKIE_PATH.is_file():
            shutil.copy2(SECRETS_COOKIE_PATH, COOKIE_FILE_PATH)
            file_size = COOKIE_FILE_PATH.stat().st_size
            print(f"✓ Successfully copied cookies.txt")
            print(f"  From: {SECRETS_COOKIE_PATH.absolute()}")
            print(f"  To: {COOKIE_FILE_PATH.absolute()}")
            print(f"  Size: {file_size} bytes")
        else:
            print(f"⚠ Source cookies file not found at {SECRETS_COOKIE_PATH}")
            print(f"  Continuing without cookies file.")
    except PermissionError as e:
        print(f"✗ Permission denied: Cannot copy cookies file")
        print(f"  Error: {e}")
    except Exception as e:
        print(f"✗ Error copying cookies file: {e}")
        print(f"  Traceback: {traceback.format_exc()}")
    
    print(f"{'='*50}\n")


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


@app.on_event("startup")
async def startup_event():
    """
    Runs at application startup to check and log secrets configuration.
    """
    list_secrets_directory()
    check_cookies_file()
    copy_cookies_file()


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
    
    # Only add cookiefile if it exists
    if COOKIE_FILE_PATH.exists() and COOKIE_FILE_PATH.is_file():
        ydl_opts["cookiefile"] = str(COOKIE_FILE_PATH)
        print(f"Using cookies file: {COOKIE_FILE_PATH.absolute()}")
    else:
        print(f"Warning: Cookies file not found at {COOKIE_FILE_PATH}. Continuing without cookies.")

    try:
        # Download the audio from YouTube
        print(f"Downloading audio from: {request.youtube_url}")
        print(f"yt-dlp options: {ydl_opts}")
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([str(request.youtube_url)])
            print(f"Audio downloaded to: {audio_filepath}")
        except OSError as os_error:
            # Log detailed OS-level errors
            print(f"OS Error during download: {os_error}")
            print(f"Error type: {type(os_error).__name__}")
            print(f"Error code: {getattr(os_error, 'errno', 'N/A')}")
            print(f"Full traceback:\n{traceback.format_exc()}")
            raise
        except Exception as download_error:
            # Log other download errors
            print(f"Error during download: {download_error}")
            print(f"Error type: {type(download_error).__name__}")
            print(f"Full traceback:\n{traceback.format_exc()}")
            raise

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

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log the error for debugging with full details
        error_type = type(e).__name__
        error_msg = str(e)
        error_traceback = traceback.format_exc()
        
        print(f"\n{'='*50}")
        print(f"ERROR OCCURRED")
        print(f"{'='*50}")
        print(f"Error Type: {error_type}")
        print(f"Error Message: {error_msg}")
        print(f"Error Args: {e.args}")
        if hasattr(e, 'errno'):
            print(f"Error Code: {e.errno}")
        print(f"\nFull Traceback:\n{error_traceback}")
        print(f"{'='*50}\n")
        
        raise HTTPException(
            status_code=500, detail=f"An internal error occurred: {error_msg}"
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
