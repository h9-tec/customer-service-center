import re
from typing import Any, Dict


def mask_pii(value: str) -> str:
    """Mask emails/phones in a string."""
    if not value:
        return value
    masked = re.sub(r"[\w\.-]+@[\w\.-]+", "[email]", value)
    masked = re.sub(r"\+?\d[\d\s\-]{6,}", "[phone]", masked)
    return masked


def mask_payload(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {k: mask_payload(v) for k, v in payload.items()}
    if isinstance(payload, list):
        return [mask_payload(x) for x in payload]
    if isinstance(payload, str):
        return mask_pii(payload)
    return payload
