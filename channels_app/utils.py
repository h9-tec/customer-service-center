import hmac
import hashlib
from typing import Optional

from django.conf import settings


def verify_meta_signature(body: bytes, signature_header: Optional[str]) -> bool:
    """Verify Meta (WhatsApp) webhook signature using app secret."""
    secret = settings.WHATSAPP_APP_SECRET
    if not secret or not signature_header:
        return False

    # Signature format: "sha256=..."
    try:
        algo, provided_sig = signature_header.split("=", 1)
    except ValueError:
        return False
    algo = algo.lower()
    if algo not in ("sha1", "sha256"):
        return False
    digestmod = hashlib.sha1 if algo == "sha1" else hashlib.sha256
    mac = hmac.new(secret.encode(), msg=body, digestmod=digestmod)
    expected = mac.hexdigest()
    return hmac.compare_digest(expected, provided_sig)


def is_ip_allowed(request) -> bool:
    allowlist = settings.WEBHOOK_IP_ALLOWLIST
    if not allowlist:
        return True
    ip = request.META.get("REMOTE_ADDR", "")
    return ip in allowlist
