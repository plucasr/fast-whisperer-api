# Lexios Transcription API Endpoints

This document provides a comprehensive overview of all available endpoints for the Lexios Transcription API.

## Base URL
`http://localhost:8000`

---

## 1. Root Information

Get basic API information and available endpoints.

- **URL:** `/`
- **Method:** `GET`
- **Success Response:**
  - **Code:** `200 OK`
  - **Content:**
    ```json
    {
      "message": "Lexios Transcription API",
      "version": "1.0.0",
      "endpoints": {
        "POST /transcript": "Get transcript from YouTube URL",
        "POST /transcribe-audio": "Transcribe uploaded audio file",
        "GET /supported-languages": "Get list of supported languages",
        "GET /health": "Health check endpoint"
      }
    }
    ```

---

## 2. Health Check

Check service status and configuration.

- **URL:** `/health`
- **Method:** `GET`
- **Success Response:**
  - **Code:** `200 OK`
  - **Content:**
    ```json
    {
      "status": "healthy",
      "whisper_model": "small",
      "supported_formats": [".mp3", ".wav", ".m4a", ".flac", ".ogg", ".wma", ".aac", ".webm", ".mp4", ".mov"],
      "api_version": "1.0.0"
    }
    ```

---

## 3. Audio File Transcription

Upload and transcribe audio files using Whisper.

- **URL:** `/transcribe-audio`
- **Method:** `POST`
- **Content-Type:** `multipart/form-data`
- **Request Parameters:**
  - `file`: Audio file (required)
  - `language`: Language code (optional, auto-detect if not provided)
  - `include_word_timestamps`: Boolean (optional, default: true)

- **Example Request (curl):**
  ```bash
  curl -X POST "http://localhost:8000/transcribe-audio" \
    -F "file=@audio.mp3" \
    -F "language=en" \
    -F "include_word_timestamps=true"
  ```

- **Success Response:**
  - **Code:** `200 OK`
  - **Content:**
    ```json
    {
      "success": true,
      "transcript": "Your transcribed text here...",
      "language": "en",
      "language_probability": 0.99,
      "duration": 45.2,
      "word_count": 123,
      "character_count": 567,
      "segment_count": 8,
      "average_confidence": 0.95,
      "segments": [
        {
          "start": 0.0,
          "end": 3.5,
          "text": "Hello world",
          "words": [
            {
              "word": "Hello",
              "start": 0.0,
              "end": 1.2,
              "probability": 0.98
            },
            {
              "word": "world",
              "start": 1.3,
              "end": 2.1,
              "probability": 0.99
            }
          ]
        }
      ],
      "model_info": {
        "model_size": "small",
        "detected_language": "en",
        "detection_probability": 0.99
      }
    }
    ```

- **Error Response:**
  - **Code:** `200 OK` (with error in response)
  - **Content:**
    ```json
    {
      "success": false,
      "transcript": null,
      "language": null,
      "duration": null,
      "segments": null,
      "error": "Transcription failed: [error details]"
    }
    ```

- **Validation Errors:**
  - **Code:** `400 Bad Request`
  - **Content:**
    ```json
    {
      "detail": "Unsupported file type: .txt. Supported types: .mp3, .wav, .m4a, .flac, .ogg, .wma, .aac, .webm, .mp4, .mov"
    }
    ```

---

## 4. YouTube Transcript (POST)

Get transcript from a YouTube video URL.

- **URL:** `/transcript`
- **Method:** `POST`
- **Content-Type:** `application/json`
- **Request Body:**
  ```json
  {
    "url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "languages": ["en", "pt", "es"]
  }
  ```

- **Success Response:**
  - **Code:** `200 OK`
  - **Content:**
    ```json
    {
      "success": true,
      "transcript": "Full transcript text here...",
      "length": 1234
    }
    ```

- **Error Response:**
  - **Code:** `200 OK` (with error in response)
  - **Content:**
    ```json
    {
      "success": false,
      "transcript": null,
      "length": null,
      "error": "Failed to retrieve transcript. Video may not have transcripts available."
    }
    ```

---

## 5. YouTube Transcript (GET)

Get transcript from a YouTube video URL using query parameters.

- **URL:** `/transcript`
- **Method:** `GET`
- **Query Parameters:**
  - `url`: YouTube video URL (required)
  - `languages`: Comma-separated language codes (optional, default: "en,pt,es")

- **Example Request:**
  ```
  GET /transcript?url=https://www.youtube.com/watch?v=VIDEO_ID&languages=en,pt,es
  ```

- **Response:** Same as POST version above.

---

## 6. Supported Languages

Get list of all supported language codes.

- **URL:** `/supported-languages`
- **Method:** `GET`
- **Success Response:**
  - **Code:** `200 OK`
  - **Content:**
    ```json
    {
      "languages": {
        "auto": "Auto-detect",
        "en": "English",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "it": "Italian",
        "pt": "Portuguese",
        "ru": "Russian",
        "ja": "Japanese",
        "ko": "Korean",
        "zh": "Chinese",
        "ar": "Arabic",
        "hi": "Hindi",
        "th": "Thai",
        "vi": "Vietnamese",
        "nl": "Dutch",
        "tr": "Turkish",
        "pl": "Polish",
        "sv": "Swedish",
        "da": "Danish",
        "no": "Norwegian",
        "fi": "Finnish"
      },
      "note": "Use language code as parameter, or omit for auto-detection"
    }
    ```

---

## Supported Audio Formats

The following audio formats are supported for transcription:

- MP3 (.mp3)
- WAV (.wav)
- M4A (.m4a)
- FLAC (.flac)
- OGG (.ogg)
- WMA (.wma)
- AAC (.aac)
- WebM (.webm)
- MP4 (.mp4)
- MOV (.mov)

---

## Error Handling

The API uses standard HTTP status codes and provides detailed error messages:

- **400 Bad Request**: Invalid request parameters or unsupported file format
- **422 Unprocessable Entity**: Request validation failed
- **500 Internal Server Error**: Server-side processing error

For audio transcription, errors are returned within the response body with `success: false` to provide more detailed error information.

---

## Rate Limiting

Currently, no rate limiting is implemented. For production use, consider implementing rate limiting based on your requirements.

---

## CORS Support

The API includes CORS middleware configured to allow all origins. In production, configure specific allowed origins for security.

---

## Testing

Use the provided test script to verify API functionality:

```bash
# Simple connectivity test
python test_api.py simple

# Full test suite
python test_api.py
```
