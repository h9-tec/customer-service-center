import logging
import os
from pathlib import Path
from typing import Optional

import requests
from celery import shared_task
from django.conf import settings

from channels_app.tts import synthesize_tts
from core.metrics import ASR_REQUESTS, ASR_LATENCY, TTS_REQUESTS, TTS_LATENCY
from channels_app.whatsapp_media import upload_media
from channels_app.asr import transcribe_audio
from conversation_app.models import Message

logger = logging.getLogger(__name__)


def _media_headers() -> dict:
    return {"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"} if settings.WHATSAPP_TOKEN else {}


@shared_task
def download_media(media_id: str, mime_type: Optional[str], message_id: int) -> Optional[str]:
    """Download WhatsApp media to local storage and trigger transcription for voice."""
    if not settings.WHATSAPP_TOKEN:
        logger.warning("WHATSAPP_TOKEN not set; skipping media download")
        return None

    info_url = f"{settings.WHATSAPP_API_BASE}/{media_id}"
    info_resp = requests.get(info_url, headers=_media_headers(), timeout=10)
    if not info_resp.ok:
        logger.error("Failed to fetch media info %s: %s", media_id, info_resp.text)
        return None
    media_url = info_resp.json().get("url")
    if not media_url:
        logger.error("No media URL returned for %s", media_id)
        return None

    media_resp = requests.get(media_url, headers=_media_headers(), timeout=30)
    if not media_resp.ok:
        logger.error("Failed to download media %s: %s", media_id, media_resp.text)
        return None

    ext = mime_type.split("/")[-1] if mime_type else "bin"
    media_dir = Path(settings.MEDIA_ROOT) / "whatsapp"
    media_dir.mkdir(parents=True, exist_ok=True)
    file_path = media_dir / f"{media_id}.{ext}"
    with open(file_path, "wb") as f:
        f.write(media_resp.content)

    logger.info("Saved media %s to %s", media_id, file_path)

    if mime_type and "audio" in mime_type or "voice" in mime_type:
        transcribe_voice.delay(str(file_path), message_id)
    return str(file_path)


@shared_task
def transcribe_voice(file_path: str, message_id: int) -> Optional[str]:
    """Transcribe audio using local Whisper (Hugging Face) if available."""
    ASR_REQUESTS.labels(model=settings.WHISPER_MODEL_ID).inc()
    with ASR_LATENCY.labels(model=settings.WHISPER_MODEL_ID).time():
        transcript = transcribe_audio(file_path)
    try:
        msg = Message.objects.get(id=message_id)
    except Message.DoesNotExist:
        logger.warning("Message %s not found for transcription.", message_id)
        return None

    if transcript:
        msg.text = transcript
        msg.save(update_fields=["text"])
    logger.info("Transcription stub completed for %s (file %s)", message_id, file_path)
    return transcript


@shared_task
def generate_tts(text: str, message_id: int) -> Optional[str]:
    """Generate TTS audio locally and attach to message."""
    TTS_REQUESTS.labels(voice=settings.TTS_VOICE or "default").inc()
    with TTS_LATENCY.labels(voice=settings.TTS_VOICE or "default").time():
        audio_path = synthesize_tts(text)
    if not audio_path:
        return None
    try:
        msg = Message.objects.get(id=message_id)
    except Message.DoesNotExist:
        logger.warning("Message %s not found for TTS attach.", message_id)
        return None
    attachments = msg.attachments or []
    attachments.append({"type": "audio", "path": audio_path})
    # Optionally upload to WhatsApp and store media id
    media_id = upload_media(audio_path) if audio_path else None
    if media_id:
        attachments[-1]["whatsapp_media_id"] = media_id
    msg.attachments = attachments
    msg.save(update_fields=["attachments"])
    logger.info("Attached TTS audio to message %s at %s", message_id, audio_path)
    return audio_path
