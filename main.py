import os
import logging
import time
import telebot
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан! Создайте файл .env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# ========== БАЗА ЗНАНИЙ ==========
FAQ = {
    "сколько стоит": "Цены на наши продукты начинаются от 5 000 ₽/мес. Точная стоимость зависит от выбранного тарифа и количества пользователей.",
    "цена": "Цены на наши продукты начинаются от 5 000 ₽/мес.",
    "техподдержка": "Техподдержка работает в онлайн-чате в рабочее время (ответ до 2 часов). На тарифах Pro и Enterprise — круглосуточная поддержка 24/7.",
    "бесплатно": "Да, мы даём 14 дней бесплатного доступа ко всем функциям без ограничений.",
    "тестовый": "Да, мы даём 14 дней бесплатного доступа.",
    "интегрировать": "CloudCRM поддерживает интеграцию через REST API и Webhook. Готовые модули для WordPress, Bitrix и Tilda.",
    "интеграция": "CloudCRM поддерживает интеграцию через REST API и Webhook.",
    "сравнение": "Сравнение тарифов:\n• CloudCRM: Basic — 5 000 ₽/мес — до 10 пользователей, Pro — 15 000 ₽/мес — до 50 пользователей, Enterprise — индивидуально.\n• AnalyticsPro: Start — 10 000 ₽/мес — до 5 дашбордов, Business — 30 000 ₽/мес.\n• DevOpsStack: Base — 20 000 ₽/мес — до 20 проектов.",
    "тариф": "Сравнение тарифов: ... (полный список выше).",
    "консультант": "Хорошо, я передам ваш запрос менеджеру. Напишите, как к вам обращаться? (или /cancel)",
    "менеджер": "Хорошо, я передам ваш запрос менеджеру. Напишите, как к вам обращаться? (или /cancel)",
    "помощь": "К сожалению, я не знаю ответа. Давайте я передам ваш вопрос менеджеру. Напишите, как к вам обращаться? (или /cancel)",
}

user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(
        message,
        "Я — виртуальный ассистент отдела продаж. Чем могу помочь?\n\n"
        "Я отвечаю на вопросы о:\n"
        "• ценах и тарифах\n"
        "• техподдержке\n"
        "• интеграциях\n"
        "• тестовом периоде\n"
        "• сравнении тарифов\n\n"
        "Если хотите связаться с менеджером — напишите об этом."
    )
    logger.info(f"CMD /start from user={message.chat.id}")

@bot.message_handler(commands=['cancel'])
def cancel(message):
    user_data.pop(message.chat.id, None)
    bot.reply_to(message, "Диалог завершён. Для начала напишите /start.")
    logger.info(f"CMD /cancel from user={message.chat.id}")

@bot.message_handler(commands=['done'])
def done(message):
    bot.reply_to(message, "Рад был помочь! Если появятся вопросы — я здесь.")
    logger.info(f"CMD /done from user={message.chat.id}")

@bot.message_handler(func=lambda message: True)
def handle_all(message):
    chat_id = message.chat.id
    text = message.text.lower()
    logger.info(f"Сообщение от {chat_id}: {message.text[:100]}")

    # Проверяем активный сбор контакта
    if chat_id in user_data:
        state = user_data[chat_id]["state"]
        if state == "waiting_name":
            user_data[chat_id]["name"] = message.text
            user_data[chat_id]["state"] = "waiting_phone"
            bot.reply_to(message, "Спасибо! Укажите ваш номер телефона (например, +7 999 123-45-67):")
            return
        elif state == "waiting_phone":
            user_data[chat_id]["phone"] = message.text
            user_data[chat_id]["state"] = "waiting_email"
            bot.reply_to(message, "Отлично! Укажите ваш email:")
            return
        elif state == "waiting_email":
            user_data[chat_id]["email"] = message.text
            logger.info(f"Новый клиент: {user_data[chat_id]}")
            bot.reply_to(
                message,
                "Спасибо! Ваши данные переданы менеджеру, он свяжется с вами в ближайшее время.\n\n"
                "Если появятся новые вопросы — напишите /start."
            )
            user_data.pop(chat_id, None)
            return

    # Поиск в базе знаний
    response = None
    for key, answer in FAQ.items():
        if key in text:
            response = answer
            break

    if response:
        bot.reply_to(
            message,
            response + "\n\nЕсть ли ещё вопросы? Если хотите связаться с менеджером — напишите об этом или отправьте /done."
        )
        return

    # Если не знаем — начинаем сбор контакта
    bot.reply_to(
        message,
        "К сожалению, я не знаю точного ответа. Давайте я передам ваш вопрос менеджеру. Напишите, как к вам обращаться? (или /cancel)"
    )
    user_data[chat_id] = {"state": "waiting_name"}

def start_bot():
    logger.info("Бот запущен и готов к работе!")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
        except Exception as e:
            logger.error(f"Ошибка в polling: {e}. Перезапуск через 10 секунд...")
            time.sleep(10)

if __name__ == "__main__":
    start_bot()