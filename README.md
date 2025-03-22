# Lexios Transcription API

A FastAPI-based transcription service that provides both YouTube transcript fetching and audio file transcription using OpenAI's Whisper model via faster-whisper.

## Features

- **Audio Transcription**: Upload audio files and get high-quality transcriptions
- **YouTube Transcripts**: Extract existing transcripts from YouTube videos
- **Multiple Formats**: Support for MP3, WAV, M4A, FLAC, OGG, AAC, WebM, and more
- **Language Detection**: Automatic language detection or manual specification
- **Word-level Timestamps**: Detailed timing information for each word
- **CORS Support**: Ready for web application integration

## Installation

1. Clone the repository and navigate to the whisper service directory:
```bash
cd lexios-whisperer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Health Check
- **GET** `/health` - Check service status and configuration

### Root
- **GET** `/` - API information and available endpoints

### Audio Transcription
- **POST** `/transcribe-audio` - Transcribe uploaded audio file

**Parameters:**
- `file`: Audio file (multipart/form-data)
- `language`: Optional language code (e.g., 'en', 'pt', 'es')
- `include_word_timestamps`: Boolean, include word-level timing (default: true)

**Response:**
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

### YouTube Transcription
- **POST** `/transcript` - Get transcript from YouTube URL
- **GET** `/transcript` - Get transcript from YouTube URL (query parameters)

**Parameters:**
- `url`: YouTube video URL
- `languages`: Preferred language codes (array for POST, comma-separated for GET)

### Supported Languages
- **GET** `/supported-languages` - List all supported language codes

## Usage Examples

### Upload Audio File (Python)
```python
import requests

url = "http://localhost:8000/transcribe-audio"
files = {"file": open("audio.mp3", "rb")}
data = {"language": "en", "include_word_timestamps": True}

response = requests.post(url, files=files, data=data)
result = response.json()

if result["success"]:
    print(f"Transcript: {result['transcript']}")
    print(f"Language: {result['language']}")
    print(f"Duration: {result['duration']} seconds")
else:
    print(f"Error: {result['error']}")
```

### Upload Audio File (curl)
```bash
curl -X POST "http://localhost:8000/transcribe-audio" \
  -F "file=@audio.mp3" \
  -F "language=en" \
  -F "include_word_timestamps=true"
```

### YouTube Transcript
```python
import requests

url = "http://localhost:8000/transcript"
data = {
    "url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "languages": ["en", "pt", "es"]
}

response = requests.post(url, json=data)
result = response.json()

if result["success"]:
    print(f"Transcript: {result['transcript']}")
else:
    print(f"Error: {result['error']}")
```

## Configuration

The API uses the following default configuration:

- **Whisper Model**: `small` (faster processing, good quality)
- **Device**: `cpu` (change to `cuda` if you have GPU support)
- **Compute Type**: `int8` (optimized for CPU)

To change the model configuration, modify the `AudioProcessor` initialization in `main.py`:

```python
# For better accuracy but slower processing
audio_processor = AudioProcessor(model_size="medium", device="cpu", compute_type="int8")

# For GPU acceleration (if available)
audio_processor = AudioProcessor(model_size="small", device="cuda", compute_type="float16")
```

## Supported Audio Formats

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

## Supported Languages

The API supports 50+ languages including:

- English (en)
- Spanish (es)
- Portuguese (pt)
- French (fr)
- German (de)
- Italian (it)
- Russian (ru)
- Japanese (ja)
- Korean (ko)
- Chinese (zh)
- Arabic (ar)
- And many more...

Use `GET /supported-languages` to see the complete list.

## Testing

Run the test suite:

```bash
# Simple connectivity test
python test_api.py simple

# Full test suite (requires async support)
python test_api.py
```

## Performance Notes

- **Model Size**: Larger models (medium, large) provide better accuracy but slower processing
- **CPU vs GPU**: GPU acceleration significantly improves processing speed
- **File Size**: Processing time scales with audio duration
- **Memory**: Larger models require more RAM

## Error Handling

The API provides detailed error messages for common issues:

- Unsupported file formats
- File size limitations
- Transcription failures
- Invalid YouTube URLs
- Network timeouts

## Docker Support

Build and run with Docker:

```bash
docker build -t lexios-transcription .
docker run -p 8000:8000 lexios-transcription
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details.