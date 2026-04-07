from unittest.mock import patch, MagicMock
from pathlib import Path
from podcast2obsidian.transcriber import transcribe


@patch("podcast2obsidian.transcriber.WhisperModel")
def test_transcribe_returns_joined_text(mock_model_class):
    mock_model = MagicMock()
    mock_model_class.return_value = mock_model

    # Simulate segments as named tuples with .text
    segment1 = MagicMock()
    segment1.text = "Hello world."
    segment2 = MagicMock()
    segment2.text = " This is a test."

    mock_model.transcribe.return_value = ([segment1, segment2], MagicMock())

    result = transcribe(Path("/fake/audio.mp3"), model_name="tiny", language="en")

    assert result == "Hello world. This is a test."
    mock_model_class.assert_called_once_with("tiny")
    mock_model.transcribe.assert_called_once_with(str(Path("/fake/audio.mp3")), language="en")


@patch("podcast2obsidian.transcriber.WhisperModel")
def test_transcribe_uses_default_model(mock_model_class):
    mock_model = MagicMock()
    mock_model_class.return_value = mock_model
    mock_model.transcribe.return_value = ([], MagicMock())

    transcribe(Path("/fake/audio.mp3"))

    mock_model_class.assert_called_once_with("large-v3")
