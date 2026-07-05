import logging
import re

PHONE_MASK_RE = re.compile(r"(\+?\d)[\d\s\-\(\)]{6,}(\d)")
EMAIL_MASK_RE = re.compile(r"([\w\.\+\-])[\w\.\+\-]*@([\w\-]+\.[\w\-]+)")


def mask_phone(text: str) -> str:
    return PHONE_MASK_RE.sub(r"\1***\2", text)


def mask_email(text: str) -> str:
    return EMAIL_MASK_RE.sub(r"\1***@\2", text)


def mask_pii(text: str) -> str:
    return mask_email(mask_phone(text))


class PIISafeFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = mask_pii(record.msg)
        return True


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    for handler in logging.getLogger().handlers:
        handler.addFilter(PIISafeFilter())


def validate_phone(phone: str) -> bool:
    cleaned = re.sub(r"[\s\-\(\)]", "", phone)
    return bool(re.match(r"^(\+7|8)\d{10}$", cleaned))


def validate_email(email: str) -> bool:
    return bool(re.match(r"^[\w\.\+\-]+@[\w\-]+\.[\w\-]{2,}$", email))



