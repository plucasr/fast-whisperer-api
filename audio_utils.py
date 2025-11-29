import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from faster_whisper import WhisperModel


class AudioProcessor:
    """Audio processing utilities for transcription"""

    SUPPORTED_FORMATS = {
        ".mp3",
        ".wav",
        ".m4a",
        ".flac",
        ".ogg",
        ".wma",
        ".aac",
        ".webm",
        ".mp4",
        ".mov",
    }

    def __init__(
        self, model_size: str = "small", device: str = "cpu", compute_type: str = "int8"
    ):
        """
        Initialize the audio processor with Whisper model

        Args:
            model_size: Whisper model size ("tiny", "small", "medium", "large", "large-v3")
            device: Device to run inference on ("cpu", "cuda")
            compute_type: Compute type ("int8", "float16", "float32")
        """
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        self.model_size = model_size

    def is_supported_format(self, filename: str) -> bool:
        """Check if the file format is supported"""
        return Path(filename).suffix.lower() in self.SUPPORTED_FORMATS

    def validate_audio_file(
        self, filename: str, max_size_mb: int = 100
    ) -> Tuple[bool, str]:
        """
        Validate audio file format and size

        Args:
            filename: Name of the audio file
            max_size_mb: Maximum file size in MB

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not filename:
            return False, "No filename provided"

        # Check file extension
        if not self.is_supported_format(filename):
            supported = ", ".join(self.SUPPORTED_FORMATS)
            return False, f"Unsupported file format. Supported formats: {supported}"

        return True, ""

    async def transcribe_file(
        self,
        file_path: str,
        language: Optional[str] = None,
        include_word_timestamps: bool = True,
        beam_size: int = 5,
    ) -> Dict[str, Any]:
        """
        Transcribe an audio file

        Args:
            file_path: Path to the audio file
            language: Language code (e.g., 'en', 'pt', 'es'). Auto-detect if None
            include_word_timestamps: Whether to include word-level timestamps
            beam_size: Beam size for decoding (higher = more accurate but slower)

        Returns:
            Dictionary containing transcription results
        """
        try:
            # Transcribe with Whisper
            segments, info = self.model.transcribe(
                file_path,
                language=language,
                beam_size=beam_size,
                word_timestamps=include_word_timestamps,
            )

            # Process segments
            segments_list = []
            full_transcript = []
            total_words = 0

            for segment in segments:
                segment_text = segment.text.strip()
                if segment_text:  # Skip empty segments
                    segment_dict = {
                        "start": round(segment.start, 2),
                        "end": round(segment.end, 2),
                        "text": segment_text,
                    }

                    # Add word-level timestamps if available
                    if hasattr(segment, "words") and segment.words:
                        words = []
                        for word in segment.words:
                            words.append(
                                {
                                    "word": word.word,
                                    "start": round(word.start, 2),
                                    "end": round(word.end, 2),
                                    "probability": round(word.probability, 3),
                                }
                            )
                        segment_dict["words"] = words
                        total_words += len(words)

                    segments_list.append(segment_dict)
                    full_transcript.append(segment_text)

            # Join transcript
            transcript_text = " ".join(full_transcript)

            # Calculate confidence score (average of segment confidences if available)
            avg_confidence = None
            if segments_list and "words" in segments_list[0]:
                all_word_probs = []
                for seg in segments_list:
                    if "words" in seg:
                        all_word_probs.extend([w["probability"] for w in seg["words"]])
                if all_word_probs:
                    avg_confidence = round(sum(all_word_probs) / len(all_word_probs), 3)

            return {
                "success": True,
                "transcript": transcript_text,
                "language": info.language,
                "language_probability": round(info.language_probability, 3),
                "duration": round(info.duration, 2),
                "segments": segments_list,
                "word_count": len(transcript_text.split()) if transcript_text else 0,
                "character_count": len(transcript_text),
                "segment_count": len(segments_list),
                "average_confidence": avg_confidence,
                "model_info": {
                    "model_size": self.model_size,
                    "detected_language": info.language,
                    "detection_probability": round(info.language_probability, 3),
                },
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Transcription failed: {str(e)}",
                "transcript": None,
                "language": None,
                "duration": None,
                "segments": None,
            }

    async def transcribe_uploaded_file(
        self,
        file_content: bytes,
        filename: str,
        language: Optional[str] = None,
        include_word_timestamps: bool = True,
    ) -> Dict[str, Any]:
        """
        Transcribe an uploaded file from bytes

        Args:
            file_content: Raw file content as bytes
            filename: Original filename (for format detection)
            language: Language code for transcription
            include_word_timestamps: Whether to include word timestamps

        Returns:
            Dictionary containing transcription results
        """
        # Validate file
        is_valid, error_msg = self.validate_audio_file(filename)
        if not is_valid:
            return {
                "success": False,
                "error": error_msg,
                "transcript": None,
                "language": None,
                "duration": None,
                "segments": None,
            }

        # Create temporary file
        file_extension = Path(filename).suffix.lower()
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=file_extension
        ) as tmp_file:
            try:
                # Write content to temporary file
                tmp_file.write(file_content)
                tmp_file.flush()

                # Transcribe
                result = await self.transcribe_file(
                    tmp_file.name,
                    language=language,
                    include_word_timestamps=include_word_timestamps,
                )

                return result

            finally:
                # Clean up temporary file
                try:
                    os.unlink(tmp_file.name)
                except OSError:
                    pass


def get_supported_languages() -> Dict[str, str]:
    """Get list of supported languages by Whisper"""
    return {
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
        "fi": "Finnish",
    }


def estimate_transcription_time(
    duration_seconds: float, model_size: str = "small"
) -> float:
    """
    Estimate transcription time based on audio duration and model size

    Args:
        duration_seconds: Audio duration in seconds
        model_size: Whisper model size

    Returns:
        Estimated transcription time in seconds
    """
    # Rough estimates based on CPU performance (these can vary significantly)
    time_multipliers = {
        "tiny": 0.1,
        "small": 0.2,
        "medium": 0.4,
        "large": 0.8,
        "large-v3": 1.0,
    }

    multiplier = time_multipliers.get(model_size, 0.2)
    return duration_seconds * multiplier
