import logging
from pathlib import Path
from typing import Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def upload_media(file_path: str) -> Optional[str]:
    """Upload media to WhatsApp Cloud API and return media id."""
    if not settings.WHATSAPP_PHONE_NUMBER_ID or not settings.WHATSAPP_TOKEN:
        logger.warning("WhatsApp credentials not set; cannot upload media.")
        return None
    url = f"{settings.WHATSAPP_API_BASE}/{settings.WHATSAPP_PHONE_NUMBER_ID}/media"
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_TOKEN}",
    }
    try:
        with open(file_path, "rb") as f:
            files = {"file": (Path(file_path).name, f, "audio/ogg")}
            data = {"messaging_product": "whatsapp"}
            resp = requests.post(url, headers=headers, files=files, data=data, timeout=30)
        if not resp.ok:
            logger.error("Failed to upload media: %s %s", resp.status_code, resp.text)
            return None
        media_id = resp.json().get("id")
        logger.info("Uploaded media %s to WhatsApp, got id %s", file_path, media_id)
        return media_id
    except Exception as exc:  # noqa: broad-except
        logger.exception("Media upload failed: %s", exc)
        return None
