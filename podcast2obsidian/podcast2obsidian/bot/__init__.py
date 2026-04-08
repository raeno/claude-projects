import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from podcast2obsidian.bot import db, handlers
from podcast2obsidian.bot.worker import worker_loop
from podcast2obsidian.config import load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


def run() -> None:
    """Start the Telegram bot and worker."""
    config = load_config()

    token = config.get("telegram_bot_token", "")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not set. Add it to .env or config.toml.")
        return

    allowed_str = config.get("telegram_allowed_users", "")
    allowed_users = set()
    if allowed_str:
        allowed_users = {
            int(uid.strip()) for uid in allowed_str.split(",") if uid.strip()
        }
    if not allowed_users:
        logger.warning("TELEGRAM_ALLOWED_USERS not set — bot will reject all messages.")

    # Init DB
    db.init_db()
    conn = db.get_db()

    # Configure handlers
    handlers.configure(allowed_users, conn)

    # Create bot and dispatcher
    bot = Bot(token=token)
    dp = Dispatcher()
    dp.include_router(handlers.router)

    async def main():
        # Set bot menu commands
        await bot.set_my_commands(
            [
                BotCommand(command="start", description="Начало работы"),
                BotCommand(command="cancel", description="Отменить текущие задачи"),
                BotCommand(command="history", description="Последние 10 обработок"),
                BotCommand(command="cookies", description="Список доступных cookies"),
            ]
        )

        # Start worker as background task
        worker_task = asyncio.create_task(worker_loop(bot, conn, config))
        logger.info("Bot starting...")
        try:
            await dp.start_polling(bot)
        finally:
            worker_task.cancel()
            conn.close()
            # Force exit — kills any lingering whisper threads
            import os

            os._exit(0)

    asyncio.run(main())
