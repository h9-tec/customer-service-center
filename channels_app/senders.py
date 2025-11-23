import logging
from typing import Any, Dict

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def send_whatsapp_text(to: str, body: str) -> Dict[str, Any]:
    """Send a text message via WhatsApp Cloud API."""
    if not settings.WHATSAPP_PHONE_NUMBER_ID or not settings.WHATSAPP_TOKEN:
        logger.warning("WhatsApp credentials not configured; skipping send.")
        return {"sent": False, "reason": "missing_credentials"}

    url = f"{settings.WHATSAPP_API_BASE}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"preview_url": False, "body": body},
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    ok = 200 <= resp.status_code < 300
    if not ok:
        logger.error("WhatsApp send failed: %s %s", resp.status_code, resp.text)
    return {"sent": ok, "status_code": resp.status_code, "response": resp.json() if resp.text else {}}
