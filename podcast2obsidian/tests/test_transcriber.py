from unittest.mock import patch
from pathlib import Path
from podcast2obsidian.transcriber import transcribe, _segments_to_paragraphs


def test_segments_to_paragraphs_splits_on_pause():
    segments = [
        (0.0, 2.0, "First sentence."),
        (2.1, 4.0, " Second sentence."),
        # 3-second pause here
        (7.0, 9.0, "After a long pause."),
        (9.1, 11.0, " Still same paragraph."),
    ]
    result = _segments_to_paragraphs(segments)
    assert "First sentence. Second sentence." in result
    assert "After a long pause. Still same paragraph." in result
    assert result.count("\n\n") == 1


def test_segments_to_paragraphs_no_pause():
    segments = [
        (0.0, 2.0, "One."),
        (2.1, 4.0, " Two."),
        (4.2, 6.0, " Three."),
    ]
    result = _segments_to_paragraphs(segments)
    assert "\n\n" not in result
    assert result == "One. Two. Three."


def test_segments_to_paragraphs_empty():
    assert _segments_to_paragraphs([]) == ""


@patch("podcast2obsidian.transcriber._mlx_worker")
def test_transcribe_mlx_returns_paragraphed_text(mock_worker):
    def side_effect(audio_path, hf_repo, language, out_queue):
        segments = [
            (0.0, 2.0, "Hello."),
            (5.0, 7.0, " World."),
        ]
        out_queue.put(("done", segments))

    mock_worker.side_effect = side_effect

    result = transcribe(
        Path("/fake/audio.mp3"),
        server_config={"backend": "mlx", "whisper_model": "tiny"},
        language="en",
    )

    assert "Hello." in result
    assert "World." in result
    assert "\n\n" in result


@patch("podcast2obsidian.transcriber._mlx_worker")
def test_transcribe_defaults_to_mlx(mock_worker):
    def side_effect(audio_path, hf_repo, language, out_queue):
        out_queue.put(("done", [(0.0, 1.0, "test")]))

    mock_worker.side_effect = side_effect

    transcribe(Path("/fake/audio.mp3"))

    mock_worker.assert_called_once()


@patch("podcast2obsidian.transcriber._faster_whisper_worker")
def test_transcribe_faster_whisper_backend(mock_worker):
    def side_effect(
        audio_path, model_name, language, compute_type, cpu_threads, out_queue
    ):
        out_queue.put(("duration", 10.0))
        out_queue.put(("segment", 0.0, 2.0, "Hello."))
        out_queue.put(("segment", 5.0, 7.0, " World."))
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

    assert "Hello." in result
    assert "World." in result
    assert "\n\n" in result
