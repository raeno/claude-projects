import os
import queue
import threading
from pathlib import Path

from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

# Map short model names to MLX HF repos
_MLX_MODEL_MAP = {
    "tiny": "mlx-community/whisper-tiny-mlx",
    "base": "mlx-community/whisper-base-mlx",
    "small": "mlx-community/whisper-small-mlx",
    "medium": "mlx-community/whisper-medium-mlx",
    "large-v3": "mlx-community/whisper-large-v3-mlx",
}

# Pause longer than this (seconds) between segments → new paragraph
PAUSE_THRESHOLD = 1.5


def _segments_to_paragraphs(segments: list[tuple[float, float, str]]) -> str:
    """Convert timestamped segments into paragraphed text.

    Args:
        segments: list of (start, end, text) tuples, sorted by start time.

    Returns:
        Text with paragraph breaks where pauses exceed PAUSE_THRESHOLD.
    """
    if not segments:
        return ""

    paragraphs = []
    current = [segments[0][2]]

    for i in range(1, len(segments)):
        prev_end = segments[i - 1][1]
        curr_start = segments[i][0]
        gap = curr_start - prev_end

        if gap >= PAUSE_THRESHOLD:
            paragraphs.append("".join(current).strip())
            current = []

        current.append(segments[i][2])

    paragraphs.append("".join(current).strip())
    return "\n\n".join(p for p in paragraphs if p)


def _mlx_worker(audio_path, hf_repo, language, out_queue):
    """Run MLX transcription in a thread."""
    try:
        import mlx_whisper

        result = mlx_whisper.transcribe(
            audio_path,
            path_or_hf_repo=hf_repo,
            language=language,
            verbose=False,
        )
        # Extract segments with timestamps for paragraph splitting
        segments = []
        for seg in result.get("segments", []):
            segments.append((seg["start"], seg["end"], seg["text"]))
        out_queue.put(("done", segments))
    except Exception as e:
        out_queue.put(("error", e))


def _faster_whisper_worker(
    audio_path, model_name, language, compute_type, cpu_threads, out_queue
):
    """Run faster-whisper transcription in a thread."""
    try:
        from faster_whisper import WhisperModel

        model = WhisperModel(
            model_name, compute_type=compute_type, cpu_threads=cpu_threads
        )
        segments, info = model.transcribe(
            audio_path, language=language, beam_size=1, vad_filter=True
        )
        out_queue.put(("duration", info.duration))
        for segment in segments:
            out_queue.put(("segment", segment.start, segment.end, segment.text))
        out_queue.put(("done", ""))
    except Exception as e:
        out_queue.put(("error", e))


def transcribe(
    audio_path: Path,
    server_config: dict | None = None,
    language: str = "ru",
    hf_token: str = "",
) -> str:
    """Transcribe audio using the backend from server_config."""
    if hf_token:
        os.environ["HF_TOKEN"] = hf_token

    if server_config is None:
        server_config = {"backend": "mlx", "whisper_model": "large-v3"}

    backend = server_config.get("backend", "mlx")
    model_name = server_config.get("whisper_model", "large-v3")

    if backend == "mlx":
        return _transcribe_mlx(str(audio_path), model_name, language)
    else:
        compute_type = server_config.get("compute_type", "int8")
        cpu_threads = server_config.get("cpu_threads", 4)
        return _transcribe_faster_whisper(
            str(audio_path), model_name, language, compute_type, cpu_threads
        )


def _transcribe_mlx(audio_path: str, model_name: str, language: str) -> str:
    hf_repo = _MLX_MODEL_MAP.get(model_name, model_name)

    out_queue: queue.Queue = queue.Queue()
    worker = threading.Thread(
        target=_mlx_worker,
        args=(audio_path, hf_repo, language, out_queue),
        daemon=True,
    )
    worker.start()

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]Transcribing (MLX GPU)"),
        TimeElapsedColumn(),
    ) as progress:
        progress.add_task("transcribe", total=None)
        while True:
            try:
                msg = out_queue.get(timeout=0.2)
            except queue.Empty:
                continue
            if msg[0] == "done":
                segments = msg[1]
                return _segments_to_paragraphs(segments)
            if msg[0] == "error":
                raise msg[1]


def _transcribe_faster_whisper(
    audio_path: str,
    model_name: str,
    language: str,
    compute_type: str,
    cpu_threads: int,
) -> str:
    out_queue: queue.Queue = queue.Queue()
    worker = threading.Thread(
        target=_faster_whisper_worker,
        args=(audio_path, model_name, language, compute_type, cpu_threads, out_queue),
        daemon=True,
    )
    worker.start()

    # Wait for duration
    msg = out_queue.get()
    if msg[0] == "error":
        raise msg[1]
    duration = msg[1]

    segments = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]Transcribing (CPU)"),
        BarColumn(),
        TextColumn("{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task("transcribe", total=duration)
        while True:
            try:
                msg = out_queue.get(timeout=0.2)
            except queue.Empty:
                continue
            if msg[0] == "done":
                progress.update(task, completed=duration)
                break
            if msg[0] == "error":
                raise msg[1]
            _, start, end, text = msg
            segments.append((start, end, text))
            progress.update(task, completed=end)

    return _segments_to_paragraphs(segments)
