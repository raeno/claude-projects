from unittest.mock import patch
from pathlib import Path
from podcast2obsidian.transcriber import transcribe


@patch("podcast2obsidian.transcriber._mlx_worker")
def test_transcribe_mlx_backend(mock_worker):
    def side_effect(audio_path, hf_repo, language, out_queue):
        out_queue.put(("done", " Hello world. "))

    mock_worker.side_effect = side_effect

    result = transcribe(
        Path("/fake/audio.mp3"),
        server_config={"backend": "mlx", "whisper_model": "tiny"},
        language="en",
    )

    assert result == "Hello world."


@patch("podcast2obsidian.transcriber._mlx_worker")
def test_transcribe_defaults_to_mlx(mock_worker):
    def side_effect(audio_path, hf_repo, language, out_queue):
        out_queue.put(("done", "test"))

    mock_worker.side_effect = side_effect

    transcribe(Path("/fake/audio.mp3"))

    mock_worker.assert_called_once()


@patch("podcast2obsidian.transcriber._faster_whisper_worker")
def test_transcribe_faster_whisper_backend(mock_worker):
    def side_effect(
        audio_path, model_name, language, compute_type, cpu_threads, out_queue
    ):
        out_queue.put(("duration", 10.0))
        out_queue.put(("done", ""))

    mock_worker.side_effect = side_effect

    result = transcribe(
        Path("/fake/audio.mp3"),
        server_config={
            "backend": "faster-whisper",
            "whisper_model": "large-v3",
            "compute_type": "int8",
            "cpu_threads": 6,
        },
        language="ru",
    )

    assert isinstance(result, str)
