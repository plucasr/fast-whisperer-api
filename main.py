from typing import Any, Dict, List, Optional

import uvicorn
from audio_utils import AudioProcessor, get_supported_languages
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Lexios Transcription API")

# Add CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize audio processor
audio_processor = AudioProcessor(model_size="small", device="cpu", compute_type="int8")


class AudioTranscriptionResponse(BaseModel):
    success: bool
    transcript: Optional[str]
    language: Optional[str]
    language_probability: Optional[float] = None
    duration: Optional[float]
    segments: Optional[List[Dict[str, Any]]] = None
    word_count: Optional[int] = None
    character_count: Optional[int] = None
    segment_count: Optional[int] = None
    average_confidence: Optional[float] = None
    model_info: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@app.get("/")
def root():
    return {
        "message": "Lexios Transcription API",
        "version": "1.0.0",
        "endpoints": {
            "POST /transcribe": "Transcribe uploaded audio file",
            "GET /supported-languages": "Get list of supported languages",
            "GET /health": "Health check endpoint",
        },
    }


@app.post("/transcribe", response_model=AudioTranscriptionResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    language: Optional[str] = Form(None),
    include_word_timestamps: bool = Form(True),
):
    """
    Transcribe an uploaded audio file using Whisper.

    Args:
        file: Audio file (mp3, wav, m4a, flac, etc.)
        language: Optional language code (e.g., 'en', 'pt', 'es'). Auto-detect if not provided.
        include_word_timestamps: Whether to include word-level timestamps (default: True)

    Returns:
        AudioTranscriptionResponse with transcript and detailed metadata
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    try:
        # Read file content
        content = await file.read()

        # Transcribe using AudioProcessor
        result = await audio_processor.transcribe_uploaded_file(
            file_content=content,
            filename=file.filename,
            language=language,
            include_word_timestamps=include_word_timestamps,
        )

        # Return result as response model
        if result["success"]:
            return AudioTranscriptionResponse(
                success=True,
                transcript=result["transcript"],
                language=result["language"],
                language_probability=result.get("language_probability"),
                duration=result["duration"],
                segments=result["segments"],
                word_count=result.get("word_count"),
                character_count=result.get("character_count"),
                segment_count=result.get("segment_count"),
                average_confidence=result.get("average_confidence"),
                model_info=result.get("model_info"),
            )
        else:
            return AudioTranscriptionResponse(
                success=False,
                transcript=None,
                language=None,
                duration=None,
                segments=None,
                error=result["error"],
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@app.get("/supported-languages")
def get_languages():
    """Get list of supported languages"""
    return {
        "languages": get_supported_languages(),
        "note": "Use language code as parameter, or omit for auto-detection",
    }


@app.get("/health")
def health_check():
    """Health check endpoint with system info"""
    return {
        "status": "healthy",
        "whisper_model": audio_processor.model_size,
        "supported_formats": list(AudioProcessor.SUPPORTED_FORMATS),
        "api_version": "1.0.0",
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
