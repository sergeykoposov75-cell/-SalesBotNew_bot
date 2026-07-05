import asyncio
import logging
import signal
import sys
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

import config
from handlers import start, cancel, handle_message
from utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

def main() -> None:
    if not config.BOT_TOKEN:
        logger.critical("BOT_TOKEN is not set. Check .env file.")
        sys.exit(1)

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

    def shutdown(sig, frame):
        logger.info("Shutting down...")
        app.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    import asyncio

    if __name__ == "__main__":
        asyncio.run(main())(application.run_polling())
    logger.critical("Fatal error during polling: %s", e)
    sys.exit(1)

    
