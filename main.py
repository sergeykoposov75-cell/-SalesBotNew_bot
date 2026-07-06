import os
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
from dotenv import load_dotenv

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

# ===== Telegram-бот (синхронный) =====
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан!")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Привет! Я бот отдела продаж. Чем могу помочь?")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    bot.reply_to(message, "Я получил ваше сообщение и обрабатываю его.")

def start_bot():
    logger.info("Бот запущен и готов к работе!")
    bot.infinity_polling()

if __name__ == "__main__":
    # Запускаем HTTP-сервер в отдельном потоке
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()

    # Запускаем бота (синхронно, без asyncio)
    try:
        start_bot()
    except KeyboardInterrupt:
        logger.info("Бот остановлен.")