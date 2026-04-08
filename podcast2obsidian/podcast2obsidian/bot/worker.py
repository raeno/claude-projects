import asyncio
import hashlib
import logging
import tempfile
from pathlib import Path

from aiogram import Bot

from podcast2obsidian.bot import db
from podcast2obsidian.bot.cookies import get_cookies_for_url
from podcast2obsidian.config import get_server_config
from podcast2obsidian.downloader import download, fetch_subtitles
from podcast2obsidian.enricher import enrich
from podcast2obsidian.formatter import format_note, save_note, slugify_title
from podcast2obsidian.transcriber import transcribe

logger = logging.getLogger(__name__)

STATUSES = {
    "pending": "⏳ В очереди",
    "downloading": "📥 Скачиваю...",
    "transcribing": "🎙 Транскрибирую...",
    "enriching": "🤖 Обогащаю...",
    "saving": "💾 Сохраняю...",
    "done": "✅ Готово!",
    "error": "❌ Ошибка",
}


async def update_telegram_status(
    bot: Bot, chat_id: int, message_id: int, status: str, extra: str = ""
) -> None:
    """Edit the status message in Telegram."""
    text = STATUSES.get(status, status)
    if extra:
        text = f"{text}\n{extra}"
    try:
        await bot.edit_message_text(text, chat_id=chat_id, message_id=message_id)
    except Exception:
        pass  # Message may have been deleted


def _is_cancelled(conn, task_id: int) -> bool:
    """Check if task was cancelled by user."""
    row = conn.execute("SELECT status FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return row and row["status"] == "cancelled"


async def process_task(bot: Bot, conn, task: dict, config: dict) -> None:
    """Process a single task with per-step status updates."""
    task_id = task["id"]
    chat_id = task["chat_id"]
    msg_id = task["status_message_id"]
    url = task["url"]
    lang = config.get("language", "ru")
    server_cfg = get_server_config(config)
    cookies = get_cookies_for_url(url)

    try:
        db.update_status(conn, task_id, "processing")

        # Step 1: Subtitles / Download
        await update_telegram_status(bot, chat_id, msg_id, "downloading")
        sub_result = await asyncio.to_thread(fetch_subtitles, url, cookies, lang)

        if _is_cancelled(conn, task_id):
            await update_telegram_status(bot, chat_id, msg_id, "🚫 Отменено")
            return

        if sub_result:
            info, transcript = sub_result
            title = info.get("title", "Unknown")
            podcast_name = (
                info.get("album")
                or info.get("playlist_title")
                or info.get("uploader", "Unknown")
            )
            source_url = info.get("webpage_url", url)
        else:
            cache_dir = (
                Path.home()
                / ".cache"
                / "podcast2obsidian"
                / hashlib.sha256(url.encode()).hexdigest()[:16]
            )
            cache_dir.mkdir(parents=True, exist_ok=True)

            cached_files = list(cache_dir.glob("*.*"))
            if cached_files:
                result = await asyncio.to_thread(
                    download, url, cache_dir, cookies, True
                )
            else:
                result = await asyncio.to_thread(download, url, cache_dir, cookies)

            title = result.title
            podcast_name = result.podcast_name
            source_url = result.source_url

            if _is_cancelled(conn, task_id):
                await update_telegram_status(bot, chat_id, msg_id, "🚫 Отменено")
                return

            # Step 2: Transcribe
            await update_telegram_status(bot, chat_id, msg_id, "transcribing")
            transcript = await asyncio.to_thread(
                transcribe,
                result.audio_path,
                server_cfg,
                lang,
                config.get("hf_token", ""),
            )

        if _is_cancelled(conn, task_id):
            await update_telegram_status(bot, chat_id, msg_id, "🚫 Отменено")
            return

        # Step 3: Enrich
        await update_telegram_status(bot, chat_id, msg_id, "enriching")
        enrichment = await asyncio.to_thread(
            enrich, transcript, config["openai_api_key"], config["openai_model"]
        )

        # Step 4: Format & save
        await update_telegram_status(bot, chat_id, msg_id, "saving")
        slug = slugify_title(title)
        note = format_note(
            title=title,
            podcast_name=podcast_name,
            source_url=source_url,
            theses=enrichment.theses,
            references=enrichment.references,
            transcript=transcript,
        )

        vault_path = Path(config.get("vault_path", "")).expanduser()
        if vault_path and str(vault_path) != ".":
            note_path = str(save_note(note, slug, vault_path))
        else:
            tmp_dir = Path(tempfile.mkdtemp(prefix="p2o_"))
            note_path = str(save_note(note, slug, tmp_dir))

        # Save to DB
        db.save_result(conn, task_id, transcript, note, note_path)

        # Send file
        from aiogram.types import BufferedInputFile

        file = BufferedInputFile(
            note.encode("utf-8"),
            filename=Path(note_path).name,
        )
        await bot.send_document(chat_id, file)
        await update_telegram_status(bot, chat_id, msg_id, "done")

    except Exception as e:
        logger.exception("Task %d failed", task_id)
        db.save_error(conn, task_id, str(e))
        await update_telegram_status(bot, chat_id, msg_id, "error", extra=str(e)[:200])


async def worker_loop(bot: Bot, conn, config: dict) -> None:
    """Main worker loop — polls for pending tasks."""
    logger.info("Worker started")
    while True:
        task = db.get_next_pending(conn)
        if task:
            # Update status with queue position
            pending = db.get_pending_count(conn)
            if pending > 1 and task["status_message_id"]:
                await update_telegram_status(
                    bot,
                    task["chat_id"],
                    task["status_message_id"],
                    "pending",
                    extra=f"Позиция: {1}/{pending}",
                )
            await process_task(bot, conn, task, config)
        else:
            await asyncio.sleep(2)
