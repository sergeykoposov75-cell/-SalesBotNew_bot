import asyncio
import logging
import os
import threading
import signal
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ===== HTTP-сервер для health check =====
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_http_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    logging.info(f"Health check server running on port {port}")
    server.serve_forever()

# ===== Telegram-бот =====
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан!")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот отдела продаж. Чем могу помочь?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Я получил ваше сообщение и обрабатываю его.")

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Бот запущен и готов к работе!")

    # Создаём событие для сигнала остановки
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    # Настраиваем обработку сигналов (Ctrl+C, завершение процесса)
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)

    # Запускаем polling в фоновой задаче
    polling_task = asyncio.create_task(app.run_polling())

    # Ждём сигнала остановки
    await stop_event.wait()
    logger.info("Получен сигнал остановки, завершаем работу...")

    # Останавливаем бота корректно
    await app.updater.stop()
    await app.stop()

    # Отменяем задачу polling и ждём её завершения
    polling_task.cancel()
    try:
        await polling_task
    except asyncio.CancelledError:
        pass

    logger.info("Бот остановлен.")

if __name__ == "__main__":
    # Запускаем HTTP-сервер в отдельном потоке (для health check)
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Принудительная остановка.")
