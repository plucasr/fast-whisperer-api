from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from youtube_fetch import get_youtube_transcript
import uvicorn

app = FastAPI(title="YouTube Transcript API")


class TranscriptRequest(BaseModel):
    url: str
    languages: list[str] = ["en", "pt", "es"]


class TranscriptResponse(BaseModel):
    success: bool
    transcript: str | None
    length: int | None
    error: str | None = None


@app.get("/")
def root():
    return {
        "message": "YouTube Transcript API",
        "endpoints": {"POST /transcript": "Get transcript from YouTube URL"},
    }


@app.post("/transcript", response_model=TranscriptResponse)
def fetch_transcript(request: TranscriptRequest):
    """
    Fetch transcript from a YouTube video URL.

    Args:
        url: YouTube video URL
        languages: List of preferred language codes (optional)

    Returns:
        TranscriptResponse with transcript text or error message
    """
    try:
        transcript = get_youtube_transcript(request.url, request.languages)

        if transcript:
            return TranscriptResponse(
                success=True, transcript=transcript, length=len(transcript)
            )
        else:
            return TranscriptResponse(
                success=False,
                transcript=None,
                length=None,
                error="Failed to retrieve transcript. Video may not have transcripts available.",
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.get("/transcript")
def fetch_transcript_get(url: str, languages: str = "en,pt,es"):
    """
    Fetch transcript from a YouTube video URL (GET method).

    Args:
        url: YouTube video URL
        languages: Comma-separated language codes (optional)

    Returns:
        TranscriptResponse with transcript text or error message
    """
    lang_list = [lang.strip() for lang in languages.split(",")]

    try:
        transcript = get_youtube_transcript(url, lang_list)

        if transcript:
            return TranscriptResponse(
                success=True, transcript=transcript, length=len(transcript)
            )
        else:
            return TranscriptResponse(
                success=False,
                transcript=None,
                length=None,
                error="Failed to retrieve transcript. Video may not have transcripts available.",
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
