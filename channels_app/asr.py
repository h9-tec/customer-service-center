import logging
from functools import lru_cache
from typing import Optional

from django.conf import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_asr_pipeline():
    """Lazily load Hugging Face Whisper pipeline."""
    try:
        from transformers import pipeline  # type: ignore
    except ImportError:
        logger.warning("transformers not installed; ASR disabled.")
        return None

    model_id = settings.WHISPER_MODEL_ID or "openai/whisper-large-v3"
    device = settings.WHISPER_DEVICE or "auto"
    try:
        asr = pipeline(
            "automatic-speech-recognition",
            model=model_id,
            device=device if device != "cpu" else -1,
            chunk_length_s=30,
        )
        return asr
    except Exception as exc:  # noqa: broad-except
        logger.exception("Failed to load ASR model %s: %s", model_id, exc)
        return None


def transcribe_audio(file_path: str, language: Optional[str] = None) -> str:
    asr = _get_asr_pipeline()
    if not asr:
        return ""
    try:
        result = asr(file_path, generate_kwargs={"language": language} if language else None)
        text = result.get("text") if isinstance(result, dict) else ""
        return text or ""
    except Exception as exc:  # noqa: broad-except
        logger.exception("ASR transcription failed for %s: %s", file_path, exc)
        return ""
