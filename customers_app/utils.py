from typing import Optional

from core.crypto import decrypt_string, encrypt_string


def encrypt_pii(value: Optional[str]) -> Optional[str]:
    if not value:
        return value
    return encrypt_string(value)


def decrypt_pii(value: Optional[str]) -> Optional[str]:
    if not value:
        return value
    return decrypt_string(value)
