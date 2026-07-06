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

# ===== Telegram-бот =====
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан!")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN)

# ===== База знаний =====
FAQ = {
    "сколько стоит": "Цены на наши продукты начинаются от 5 000 ₽/мес. Точная стоимость зависит от выбранного тарифа и количества пользователей. Можете назвать продукт, который вас интересует, — я уточню.",
    "цена": "Цены на наши продукты начинаются от 5 000 ₽/мес. Точная стоимость зависит от выбранного тарифа.",
    "техподдержка": "Техподдержка работает в онлайн-чате в рабочее время (ответ до 2 часов). На тарифах Pro и Enterprise — круглосуточная поддержка 24/7, телефонная линия и выделенный менеджер.",
    "бесплатно": "Да, мы даём 14 дней бесплатного доступа ко всем функциям без ограничений.",
    "тестовый": "Да, мы даём 14 дней бесплатного доступа ко всем функциям без ограничений.",
    "интегрировать": "CloudCRM поддерживает интеграцию через REST API и Webhook. Мы предоставляем готовые модули для WordPress, Bitrix и Tilda. Наши специалисты помогут с настройкой в течение 1-2 дней.",
    "интеграция": "CloudCRM поддерживает интеграцию через REST API и Webhook.",
    "сравнение": "Сравнение тарифов:\n• CloudCRM: Basic — 5 000 ₽/мес — до 10 пользователей, Pro — 15 000 ₽/мес — до 50 пользователей, Enterprise — индивидуально.\n• AnalyticsPro: Start — 10 000 ₽/мес — до 5 дашбордов, Business — 30 000 ₽/мес — без ограничений.\n• DevOpsStack: Base — 20 000 ₽/мес — до 20 проектов.",
    "тариф": "Сравнение тарифов: ... (все тарифы описаны в ответе выше).",
    "консультант": "Хорошо, я передам ваш запрос менеджеру. Чтобы менеджер мог подготовить индивидуальное предложение, скажите, как к вам обращаться? (или отправьте /cancel, чтобы отказаться)"
}

# ===== Состояния для сбора контакта =====
user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(
        message,
        "Я — виртуальный ассистент отдела продаж. Чем могу помочь?\n\n"
        "Я могу ответить на вопросы:\n"
        "• характеристиках продуктов\n"
        "• ценах и тарифах\n"
        "• условиях оплаты\n"
        "• сроках внедрения\n"
        "• сравнении тарифов\n"
        "• техподдержке\n"
        "• тестовом периоде\n\n"
        "Если захотите связаться с менеджером — просто напишите об этом."
    )

@bot.message_handler(commands=['cancel'])
def cancel(message):
    user_data.pop(message.chat.id, None)
    bot.reply_to(message, "Диалог завершён. Если захотите продолжить — напишите /start или просто задайте вопрос.")

@bot.message_handler(func=lambda message: True)
def handle_all(message):
    chat_id = message.chat.id
    text = message.text.lower()

    # Проверяем, есть ли активный сбор контакта
    if chat_id in user_data:
        state = user_data[chat_id]["state"]
        if state == "waiting_name":
            user_data[chat_id]["name"] = message.text
            user_data[chat_id]["state"] = "waiting_phone"
            bot.reply_to(message, "Спасибо! Укажите ваш номер телефона, чтобы менеджер мог с вами связаться (например, +7 999 123-45-67):")
            return
        elif state == "waiting_phone":
            user_data[chat_id]["phone"] = message.text
            user_data[chat_id]["state"] = "waiting_email"
            bot.reply_to(message, "Отлично! Укажите ваш email для отправки коммерческого предложения:")
            return
        elif state == "waiting_email":
            user_data[chat_id]["email"] = message.text
            # Сохраняем данные (можно записать в файл или базу)
            logger.info(f"Новый клиент: {user_data[chat_id]}")
            bot.reply_to(
                message,
                "Спасибо! Ваши данные переданы менеджеру, он свяжется с вами в ближайшее время.\n\n"
                "Если появятся новые вопросы — просто напишите /start."
            )
            user_data.pop(chat_id, None)
            return

    # === Обработка типовых вопросов ===
    response = None
    for key, answer in FAQ.items():
        if key in text:
            response = answer
            break

    if response:
        # Если ответ найден, отправляем его с вопросом о завершении
        bot.reply_to(
            message,
            response + "\n\nЕсть ли ещё вопросы? Если хотите связаться с менеджером — просто напишите об этом или отправьте /done."
        )
    else:
        # Если не знаем ответа — начинаем сбор контакта
        bot.reply_to(
            message,
            "К сожалению, я не смог найти точный ответ на ваш вопрос. Чтобы менеджер мог подготовить индивидуальное предложение, скажите, как к вам обращаться? (или отправьте /cancel, чтобы отказаться)"
        )
        user_data[chat_id] = {"state": "waiting_name"}

@bot.message_handler(commands=['done'])
def done(message):
    bot.reply_to(message, "Рад был помочь! Если возникнут новые вопросы — я здесь. /start — для начала.")

def start_bot():
    logger.info("Бот запущен и готов к работе!")
    bot.infinity_polling()

if __name__ == "__main__":
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    try:
        start_bot()
    except KeyboardInterrupt:
        logger.info("Бот остановлен.")