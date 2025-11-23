import base64
import logging
from typing import Optional

from django.conf import settings

logger = logging.getLogger(__name__)


def _get_key() -> Optional[bytes]:
    key = getattr(settings, "ENCRYPTION_KEY", None)
    if not key:
        return None
    try:
        return base64.urlsafe_b64decode(key)
    except Exception:
        logger.warning("Invalid ENCRYPTION_KEY format; encryption disabled.")
        return None


def encrypt_string(value: str) -> str:
    key = _get_key()
    if not key:
        return value
    try:
        from cryptography.fernet import Fernet
    except ImportError:
        logger.warning("cryptography not installed; skipping encryption.")
        return value
    f = Fernet(key)
    return f.encrypt(value.encode()).decode()


def decrypt_string(value: str) -> str:
    key = _get_key()
    if not key:
        return value
    try:
        from cryptography.fernet import Fernet
    except ImportError:
        logger.warning("cryptography not installed; skipping decryption.")
        return value
    f = Fernet(key)
    try:
        return f.decrypt(value.encode()).decode()
    except Exception:
        return value
