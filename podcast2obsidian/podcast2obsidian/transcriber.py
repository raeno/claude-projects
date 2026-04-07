from pathlib import Path

from faster_whisper import WhisperModel


def transcribe(
    audio_path: Path,
    model_name: str = "large-v3",
    language: str = "ru",
) -> str:
    """Transcribe audio file using faster-whisper. Returns plain text."""
    model = WhisperModel(model_name)
    segments, _ = model.transcribe(str(audio_path), language=language)
    return "".join(segment.text for segment in segments).strip()
