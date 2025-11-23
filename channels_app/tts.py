import logging
from pathlib import Path
from typing import Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def synthesize_tts(text: str) -> Optional[str]:
    """
    Call local TTS service (e.g., Piper/Coqui HTTP) to synthesize audio.
    Expects settings.TTS_SERVICE_URL to accept POST {text, voice?} and return audio bytes.
    """
    tts_url = settings.TTS_SERVICE_URL
    if not tts_url:
        logger.warning("TTS_SERVICE_URL not set; skipping TTS generation.")
        return None

    voice = settings.TTS_VOICE or None
    try:
        resp = requests.post(
            tts_url,
            json={"text": text, "voice": voice} if voice else {"text": text},
            timeout=30,
        )
        if not resp.ok:
            logger.error("TTS service error %s: %s", resp.status_code, resp.text)
            return None
        audio_bytes = resp.content
        media_dir = Path(settings.MEDIA_ROOT) / "tts"
        media_dir.mkdir(parents=True, exist_ok=True)
        file_path = media_dir / "tts_output.wav"
        with open(file_path, "wb") as f:
            f.write(audio_bytes)
        return str(file_path)
    except Exception as exc:  # noqa: broad-except
        logger.exception("TTS synthesis failed: %s", exc)
        return None
