import os
import logging
import telebot
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан! Создайте файл .env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# ========== БАЗА ЗНАНИЙ (из examples_dialogs.txt) ==========
FAQ = {
    "сколько стоит": "Цены на наши продукты начинаются от 5 000 ₽/мес. Точная стоимость зависит от выбранного тарифа и количества пользователей. Можете назвать продукт, который вас интересует, — я уточню.",
    "цена": "Цены на наши продукты начинаются от 5 000 ₽/мес. Точная стоимость зависит от выбранного тарифа.",
    "техподдержка": "Техподдержка работает в онлайн-чате в рабочее время (ответ до 2 часов). На тарифах Pro и Enterprise — круглосуточная поддержка 24/7, телефонная линия и выделенный менеджер.",
    "бесплатно": "Да, мы даём 14 дней бесплатного доступа ко всем функциям без ограничений.",
    "тестовый": "Да, мы даём 14 дней бесплатного доступа ко всем функциям без ограничений.",
    "интегрировать": "CloudCRM поддерживает интеграцию через REST API и Webhook. Мы предоставляем готовые модули для WordPress, Bitrix и Tilda. Наши специалисты помогут с настройкой в течение 1-2 дней.",
    "интеграция": "CloudCRM поддерживает интеграцию через REST API и Webhook.",
    "сравнение": "Сравнение тарифов:\n• CloudCRM: Basic — 5 000 ₽/мес — до 10 пользователей, Pro — 15 000 ₽/мес — до 50 пользователей, Enterprise — индивидуально.\n• AnalyticsPro: Start — 10 000 ₽/мес — до 5 дашбордов, Business — 30 000 ₽/мес — без ограничений.\n• DevOpsStack: Base — 20 000 ₽/мес — до 20 проектов.",
    "тариф": "Сравнение тарифов:\n• CloudCRM: Basic — 5 000 ₽/мес — до 10 пользователей, Pro — 15 000 ₽/мес — до 50 пользователей, Enterprise — индивидуально.\n• AnalyticsPro: Start — 10 000 ₽/мес — до 5 дашбордов, Business — 30 000 ₽/мес — без ограничений.\n• DevOpsStack: Base — 20 000 ₽/мес — до 20 проектов.",
    "консультант": "Хорошо, я передам ваш запрос менеджеру. Чтобы менеджер мог подготовить индивидуальное предложение, скажите, как к вам обращаться? (или отправьте /cancel, чтобы отказаться)",
    "менеджер": "Хорошо, я передам ваш запрос менеджеру. Чтобы менеджер мог подготовить индивидуальное предложение, скажите, как к вам обращаться? (или отправьте /cancel, чтобы отказаться)",
    "помощь": "К сожалению, я не смог найти точный ответ на ваш вопрос. Чтобы менеджер мог подготовить индивидуальное предложение, скажите, как к вам обращаться? (или отправьте /cancel, чтобы отказаться)",
}

# ========== СОСТОЯНИЯ ДЛЯ СБОРА КОНТАКТА ==========
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
    logger.info(f"CMD /start from user={message.chat.id}")

@bot.message_handler(commands=['cancel'])
def cancel(message):
    user_data.pop(message.chat.id, None)
    bot.reply_to(message, "Диалог завершён. Если захотите продолжить — напишите /start или просто задайте вопрос.")
    logger.info(f"CMD /cancel from user={message.chat.id}")

@bot.message_handler(commands=['done'])
def done(message):
    bot.reply_to(message, "Рад был помочь! Если возникнут новые вопросы — я здесь. /start — для начала.")
    logger.info(f"CMD /done from user={message.chat.id}")

@bot.message_handler(func=lambda message: True)
def handle_all(message):
    chat_id = message.chat.id
    text = message.text.lower()
    logger.info(f"Получено сообщение от {chat_id}: {message.text[:100]}")

    # ---- 1. Проверяем, есть ли активный сбор контакта ----
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
            # Сохраняем данные (можно записать в файл или БД)
            logger.info(f"Новый клиент: {user_data[chat_id]}")
            bot.reply_to(
                message,
                "Спасибо! Ваши данные переданы менеджеру, он свяжется с вами в ближайшее время.\n\n"
                "Если появятся новые вопросы — просто напишите /start."
            )
            user_data.pop(chat_id, None)
            return

    # ---- 2. Ищем ответ в базе знаний ----
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
        return

    # ---- 3. Если не знаем ответа — начинаем сбор контакта ----
    bot.reply_to(
        message,
        "К сожалению, я не смог найти точный ответ на ваш вопрос. Чтобы менеджер мог подготовить индивидуальное предложение, скажите, как к вам обращаться? (или отправьте /cancel, чтобы отказаться)"
    )
    user_data[chat_id] = {"state": "waiting_name"}

def start_bot():
    logger.info("Бот запущен и готов к работе!")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
        except Exception as e:
            logger.error(f"Ошибка в polling: {e}. Перезапуск через 10 секунд...")
            import time
            time.sleep(10)
            # Пересоздаём бота, чтобы сбросить состояние
            bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

if __name__ == "__main__":
    start_bot()