import logging
from telegram import Update
from telegram.ext import ContextTypes

from knowledge_base import search_knowledge_base, classify_intent, INTENT_NAMES, KB
from mistral_client import get_response
from storage import save_client_data
from models import ClientData
from utils import validate_phone, validate_email, mask_pii
from stats import stats

logger = logging.getLogger(__name__)

WAITING_NAME = "waiting_name"
WAITING_PHONE = "waiting_phone"
WAITING_EMAIL = "waiting_email"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("CMD /start from user=%s", update.effective_user.id)
    context.user_data.clear()
    await update.message.reply_text(KB["intro"])

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("CMD /cancel from user=%s", update.effective_user.id)
    context.user_data.clear()
    await update.message.reply_text(
        "Диалог завершён. Если захотите продолжить — напишите /start "
        "или просто задайте вопрос."
    )

async def handle_non_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    logger.info(
        "MSG from user=%s type=non-text attachment=%s state=%s",
        update.effective_user.id,
        type(update.message.effective_attachment).__name__,
        context.user_data.get("state"),
    )
    await update.message.reply_text(
        "Пожалуйста, отправьте ваш вопрос текстом. "
        "Я пока не умею обрабатывать изображения, стикеры и другие файлы."
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Unhandled error: %s", context.error, exc_info=context.error)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        await update.message.reply_text("Пожалуйста, напишите ваш вопрос текстом.")
        return

    logger.info(
        "MSG from user=%s text=%s state=%s",
        update.effective_user.id,
        mask_pii(update.message.text),
        context.user_data.get("state"),
    )

    state = context.user_data.get("state")

    if state == WAITING_NAME:
        await _handle_name(update, context)
    elif state == WAITING_PHONE:
        await _handle_phone(update, context)
    elif state == WAITING_EMAIL:
        await _handle_email(update, context)
    else:
        await _process_question(update, context)

async def _process_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.strip()
    if not text:
        await update.message.reply_text("Пожалуйста, напишите ваш вопрос текстом.")
        return

    stats["requests_processed"] += 1
    intent = classify_intent(text)
    logger.info(
        "User=%s intent=%s text=%s",
        update.effective_user.id,
        INTENT_NAMES.get(intent, intent),
        mask_pii(text),
    )

    if intent == "contact":
        context.user_data["state"] = WAITING_NAME
        context.user_data["last_question"] = text
        await update.message.reply_text(
            "Хорошо, я передам ваш запрос менеджеру. "
            "Чтобы менеджер мог подготовить индивидуальное предложение, "
            "скажите, как к вам обращаться?"
        )
        return

    kb_answer = search_knowledge_base(text)
    if kb_answer:
        logger.info("KB hit for intent=%s", intent)
        await update.message.reply_text(kb_answer)
        await update.message.reply_text(
            "Есть ли ещё вопросы? Если хотите связаться с менеджером — "
            "просто напишите об этом."
        )
        return

    logger.info("KB miss for intent=%s, calling Mistral...", intent)
    try:
        mistral_answer = get_response(text)
    except Exception as e:
        logger.error("Mistral exception: %s", e)
        mistral_answer = None

    if mistral_answer and len(mistral_answer) > 10:
        uncertain = ["не знаю", "не могу", "не уверен", "недостаточно", "уточните"]
        if not any(w in mistral_answer.lower() for w in uncertain):
            logger.info("Mistral answer accepted (len=%d)", len(mistral_answer))
            await update.message.reply_text(mistral_answer)
            await update.message.reply_text(
                "Есть ли ещё вопросы? Если хотите связаться с менеджером — "
                "напишите об этом."
            )
            return

    logger.info("Fallback to manager for intent=%s", intent)
    context.user_data["state"] = WAITING_NAME
    context.user_data["last_question"] = text
    await update.message.reply_text(
        "К сожалению, я не смог найти точный ответ на ваш вопрос. "
        "Чтобы менеджер мог подготовить индивидуальное предложение, "
        "скажите, как к вам обращаться? (или отправьте /cancel, чтобы отказаться)"
    )

async def _handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.strip()
    if not text:
        await update.message.reply_text("Пожалуйста, напишите ваше имя.")
        return
    if text.lower() in ("/skip", "пропустить", "отказ", "нет"):
        await update.message.reply_text(
            "Хорошо. Вы можете позвонить нам по телефону +7 800 000-00-00 "
            "в рабочее время."
        )
        context.user_data.clear()
        return
    context.user_data["contact_name"] = text
    context.user_data["state"] = WAITING_PHONE
    await update.message.reply_text(
        "Спасибо! Укажите ваш номер телефона, чтобы менеджер мог с вами связаться "
        "(например, +7 999 123-45-67):"
    )

async def _handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    phone = update.message.text.strip()
    if phone.lower() in ("нет", "не хочу", "отказ", "пропустить", "/skip"):
        context.user_data["contact_phone"] = "не указан"
        context.user_data["state"] = WAITING_EMAIL
        await update.message.reply_text(
            "Хорошо. Вы можете позвонить нам по телефону +7 800 000-00-00 "
            "в рабочее время. А пока укажите ваш email для отправки "
            "коммерческого предложения: (или отправьте /cancel)"
        )
        return
    if not validate_phone(phone):
        await update.message.reply_text(
            "Пожалуйста, укажите корректный номер телефона в формате +7 XXX XXX-XX-XX "
            "или отправьте /cancel, если не хотите указывать."
        )
        return
    context.user_data["contact_phone"] = phone
    context.user_data["state"] = WAITING_EMAIL
    await update.message.reply_text(
        "Отлично! Укажите ваш email для отправки коммерческого предложения:"
    )

async def _handle_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    email = update.message.text.strip()
    if email.lower() in ("нет", "не хочу", "отказ", "пропустить", "/skip"):
        context.user_data["contact_email"] = "не указан"
        await _finish_collection(update, context)
        return
    if not validate_email(email):
        await update.message.reply_text(
            "Пожалуйста, укажите корректный email (например, name@domain.ru) "
            "или отправьте /cancel, если не хотите указывать."
        )
        return
    context.user_data["contact_email"] = email
    await _finish_collection(update, context)

async def _finish_collection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    client = ClientData(
        name=context.user_data.get("contact_name", "не указано"),
        phone=context.user_data.get("contact_phone", "не указан"),
        email=context.user_data.get("contact_email", "не указан"),
        preferences=context.user_data.get("last_question", ""),
    )
    try:
        save_client_data(client)
        stats["contacts_collected"] += 1
        logger.info("Contact collected: name=%s", client.name)
    except Exception as e:
        logger.error("Failed to save client data: %s", e)

    context.user_data.clear()
    await update.message.reply_text(
        "Спасибо! Ваши данные переданы менеджеру, он свяжется с вами "
        "в ближайшее время.\n\n"
        "Если появятся новые вопросы — просто напишите /start."
    )
