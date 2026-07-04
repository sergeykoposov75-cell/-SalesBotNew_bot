import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-large-latest")
PROXY_URL = os.getenv("PROXY_URL", "")
PROXY_USER = os.getenv("PROXY_USER", "")
PROXY_PASS = os.getenv("PROXY_PASS", "")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is required in .env")
if not MISTRAL_API_KEY:
    raise ValueError("MISTRAL_API_KEY is required in .env")
if not ENCRYPTION_KEY or len(ENCRYPTION_KEY) < 64:
    raise ValueError("ENCRYPTION_KEY must be at least 64 hex characters in .env")
