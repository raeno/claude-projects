import logging
import re

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import Message

from podcast2obsidian.bot import db
from podcast2obsidian.bot.cookies import list_cookies, save_cookies

logger = logging.getLogger(__name__)

router = Router()

# Set by __init__.py at startup
_allowed_users: set[int] = set()
_db_conn = None


def configure(allowed_users: set[int], conn) -> None:
    """Configure handlers with allowed users and DB connection."""
    global _allowed_users, _db_conn
    _allowed_users = allowed_users
    _db_conn = conn


def _is_allowed(user_id: int) -> bool:
    return user_id in _allowed_users


def _is_url(text: str) -> bool:
    return bool(re.match(r"https?://", text.strip()))


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    if not _is_allowed(message.from_user.id):
        await message.reply("⛔ Нет доступа.")
        return

    cookies = list_cookies()
    cookies_text = ", ".join(cookies) if cookies else "нет"

    await message.reply(
        "🎙 **podcast2obsidian bot**\n\n"
        "Отправь ссылку на подкаст — получишь .md файл с транскрипцией, "
        "ключевыми тезисами и референсами.\n\n"
        "**Команды:**\n"
        "/cancel — отменить текущие задачи\n"
        "/history — последние 10 обработок\n"
        "/cookies — список доступных cookies\n\n"
        "**Cookies:** отправь файл cookies.txt с подписью домена "
        "(например `yandex` или `youtube`).\n\n"
        f"Доступные cookies: {cookies_text}",
        parse_mode="Markdown",
    )


@router.message(Command("history"))
async def cmd_history(message: Message) -> None:
    if not _is_allowed(message.from_user.id):
        return

    history = db.get_user_history(_db_conn, message.from_user.id)
    if not history:
        await message.reply("История пуста.")
        return

    lines = []
    for t in history:
        status_icon = {
            "done": "✅",
            "error": "❌",
            "pending": "⏳",
            "processing": "🔄",
        }.get(t["status"], "❓")
        date = t["created_at"][:16] if t["created_at"] else ""
        lines.append(f"{status_icon} `{date}` {t['url'][:50]}")

    await message.reply("\n".join(lines), parse_mode="Markdown")


@router.message(Command("cancel"))
async def cmd_cancel(message: Message) -> None:
    """Cancel pending/processing tasks for this user."""
    if not _is_allowed(message.from_user.id):
        return

    cancelled = db.cancel_user_tasks(_db_conn, message.from_user.id)
    if cancelled:
        await message.reply(f"🚫 Отменено задач: {cancelled}")
    else:
        await message.reply("Нет активных задач для отмены.")


@router.message(Command("cookies"))
async def cmd_cookies(message: Message) -> None:
    if not _is_allowed(message.from_user.id):
        return

    cookies = list_cookies()
    if cookies:
        await message.reply(f"🍪 Доступные cookies: {', '.join(cookies)}")
    else:
        await message.reply("Нет cookies. Отправь файл с подписью домена.")


@router.message(F.document)
async def handle_document(message: Message, bot: Bot) -> None:
    """Handle cookie file uploads."""
    if not _is_allowed(message.from_user.id):
        return

    caption = (message.caption or "").strip().lower()
    if not caption:
        await message.reply(
            "Укажи домен в подписи к файлу (например `yandex` или `youtube`)."
        )
        return

    file = await bot.download(message.document)
    content = file.read()
    path = save_cookies(caption, content)
    await message.reply(f"🍪 Cookies сохранены: `{path.name}`", parse_mode="Markdown")


@router.message(F.text)
async def handle_url(message: Message) -> None:
    """Handle URL messages — create a processing task."""
    if not _is_allowed(message.from_user.id):
        await message.reply("⛔ Нет доступа.")
        return

    url = message.text.strip()
    if not _is_url(url):
        await message.reply("Отправь ссылку на подкаст (https://...)")
        return

    # Send initial status message
    pending_count = db.get_pending_count(_db_conn) + 1
    status_msg = await message.reply(f"⏳ В очереди ({pending_count})")

    # Create task
    db.create_task(
        _db_conn,
        user_id=message.from_user.id,
        chat_id=message.chat.id,
        url=url,
        status_message_id=status_msg.message_id,
    )
