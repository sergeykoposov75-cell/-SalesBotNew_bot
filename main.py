import asyncio
import logging
import os
import signal
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

import config
from handlers import start, cancel, handle_message
from utils import setup_logging


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        pass


def run_http_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    logging.getLogger(__name__).info("Health check server running on port %d", port)
    server.serve_forever()


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

    stop_signal = asyncio.Event()

    if sys.platform != "win32":
        loop = asyncio.get_running_loop()
        try:
            loop.add_signal_handler(signal.SIGINT, stop_signal.set)
            loop.add_signal_handler(signal.SIGTERM, stop_signal.set)
        except NotImplementedError:
            signal.signal(signal.SIGINT, lambda s, f: stop_signal.set())
            signal.signal(signal.SIGTERM, lambda s, f: stop_signal.set())

    async with app:
        logger.info("Bot started polling. Press Ctrl+C to stop.")
        await app.start()
        await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)

        await stop_signal.wait()
        logger.info("Shutting down...")

    logger.info("Bot stopped.")


if __name__ == "__main__":
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
