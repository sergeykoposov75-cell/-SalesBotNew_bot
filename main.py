import os
import logging
import time
import telebot
from dotenv import load_dotenv

# Импортируем нашу базу знаний
from knowledge_base import KB, search_knowledge_base, classify_intent, INTENT_NAMES

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан! Создайте файл .env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# ========== СОСТОЯНИЯ ДЛЯ СБОРА КОНТАКТА ==========
user_data = {}

# ========== ОБРАБОТЧИКИ КОМАНД ==========
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, KB["intro"])
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

# ========== ОСНОВНАЯ ЛОГИКА ==========
@bot.message_handler(func=lambda message: True)
def handle_all(message):
    chat_id = message.chat.id
    text = message.text
    logger.info(f"Сообщение от {chat_id}: {text[:100]}")

    # Проверяем активный сбор контакта
    if chat_id in user_data:
        state = user_data[chat_id]["state"]
        if state == "waiting_name":
            user_data[chat_id]["name"] = text
            user_data[chat_id]["state"] = "waiting_phone"
            bot.reply_to(message, "Спасибо! Укажите ваш номер телефона (например, +7 999 123-45-67):")
            return
        elif state == "waiting_phone":
            user_data[chat_id]["phone"] = text
            user_data[chat_id]["state"] = "waiting_email"
            bot.reply_to(message, "Отлично! Укажите ваш email:")
            return
        elif state == "waiting_email":
            user_data[chat_id]["email"] = text
            logger.info(f"Новый клиент: {user_data[chat_id]}")
            bot.reply_to(
                message,
                "Спасибо! Ваши данные переданы менеджеру, он свяжется с вами в ближайшее время.\n\n"
                "Если появятся новые вопросы — напишите /start."
            )
            user_data.pop(chat_id, None)
            return

    # Проверяем, есть ли запрос на менеджера (классифицируем как contact)
    intent = classify_intent(text)
    if intent == "contact":
        bot.reply_to(
            message,
            "Хорошо, я передам ваш запрос менеджеру. Напишите, как к вам обращаться? (или /cancel)"
        )
        user_data[chat_id] = {"state": "waiting_name"}
        return

    # Поиск ответа в базе знаний
    answer = search_knowledge_base(text)
    if answer:
        # Добавляем подсказку о завершении
        bot.reply_to(
            message,
            answer + "\n\nЕсть ли ещё вопросы? Если хотите связаться с менеджером — напишите об этом или отправьте /done."
        )
        return

    # Если ничего не подошло — сбор контакта
    bot.reply_to(
        message,
        "К сожалению, я не знаю точного ответа. Давайте я передам ваш вопрос менеджеру. Напишите, как к вам обращаться? (или /cancel)"
    )
    user_data[chat_id] = {"state": "waiting_name"}

# ========== ЗАПУСК ==========
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