import json
import os
import logging
from datetime import datetime
from crypto_utils import encrypt, decrypt
from models import ClientData
from utils import mask_pii

logger = logging.getLogger(__name__)

CLIENTS_DIR = "clients"

def _monthly_path() -> str:
    os.makedirs(CLIENTS_DIR, exist_ok=True)
    month = datetime.now().strftime("%Y-%m")
    return os.path.join(CLIENTS_DIR, f"clients_{month}.json.enc")

def save_client_data(client: ClientData) -> None:
    path = _monthly_path()
    existing = []
    try:
        with open(path, "rb") as f:
            existing = json.loads(decrypt(f.read()))
    except FileNotFoundError:
        pass
    except Exception as e:
        logger.error("Failed to read existing clients file: %s", e)

    existing.append(client.model_dump())
    raw = json.dumps(existing, ensure_ascii=False, indent=2).encode()
    with open(path, "wb") as f:
        f.write(encrypt(raw))

    logger.info(
        "Client saved: name=%s, phone=%s, email=%s",
        client.name,
        mask_pii(client.phone),
        mask_pii(client.email),
    )

def get_all_clients() -> list[ClientData]:
    all_clients = []
    if not os.path.isdir(CLIENTS_DIR):
        return all_clients
    for fname in sorted(os.listdir(CLIENTS_DIR)):
        if not fname.endswith(".json.enc"):
            continue
        path = os.path.join(CLIENTS_DIR, fname)
        try:
            with open(path, "rb") as f:
                data = json.loads(decrypt(f.read()))
            all_clients.extend(ClientData(**item) for item in data)
        except Exception as e:
            logger.error("Failed to decrypt %s: %s", fname, e)
    return all_clients
