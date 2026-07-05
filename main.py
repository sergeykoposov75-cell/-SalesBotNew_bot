import asyncio
import logging
import sys
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

import config
from handlers import start, cancel, handle_message
from utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


async def main() -> None:
    if not config.BOT_TOKEN:
        logger.critical("BOT_TOKEN is not set. Check .env file.")
        return

    logger.info(
        "Starting bot... model=%s proxy=%s",
        config.MISTRAL_MODEL,
        bool(config.PROXY_URL),
    )

    app = Application.builder().token(config.BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot started polling. Press Ctrl+C to stop.")

    try:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)

        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.critical("Fatal error during polling: %s", e)
    finally:
        await app.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
