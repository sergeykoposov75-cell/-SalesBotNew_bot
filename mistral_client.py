import logging
import time
import httpx
import config

logger = logging.getLogger(__name__)

_RETRIES = 3
_TIMEOUT = 30
_API_URL = "https://api.mistral.ai/v1/chat/completions"

def _get_proxy() -> str | None:
    if not config.PROXY_URL:
        return None
    proxy = config.PROXY_URL
    if config.PROXY_USER:
        proxy = proxy.replace("://", f"://{config.PROXY_USER}:{config.PROXY_PASS}@")
    return proxy

def get_response(prompt: str, context: list | None = None) -> str | None:
    messages = []
    if context:
        messages.extend(context)
    messages.append({
        "role": "user",
        "content": (
            "Ты — консультант отдела продаж IT-компании. "
            "Отвечай кратко (2–4 предложения), по-русски, дружелюбно и профессионально. "
            "Если не знаешь ответа — честно скажи, что не уверен.\n\n"
            f"Вопрос: {prompt}"
        ),
    })

    proxy = _get_proxy()
    client_kwargs = {"timeout": _TIMEOUT}
    if proxy:
        client_kwargs["proxy"] = proxy

    for attempt in range(_RETRIES):
        try:
            with httpx.Client(**client_kwargs) as client:
                resp = client.post(
                    _API_URL,
                    headers={
                        "Authorization": f"Bearer {config.MISTRAL_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": config.MISTRAL_MODEL,
                        "messages": messages,
                        "max_tokens": 500,
                        "temperature": 0.3,
                    },
                )
                if resp.status_code != 200:
                    logger.warning("Mistral HTTP %d: %s", resp.status_code, resp.text[:200])
                    continue
                content = resp.json()["choices"][0]["message"]["content"]
                logger.info("Mistral response received (len=%d)", len(content))
                return content
        except Exception as e:
            logger.warning("Mistral attempt %d/%d failed: %s", attempt + 1, _RETRIES, e)
            if attempt < _RETRIES - 1:
                time.sleep(2 ** attempt)
    return None
