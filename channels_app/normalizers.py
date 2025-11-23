from typing import Any, Dict, List

from core.constants import Channel


def _extract_text(msg: Dict[str, Any]) -> str:
    if msg.get("type") == "text":
        return msg.get("text", {}).get("body", "")
    if msg.get("type") == "interactive":
        interactive = msg.get("interactive", {})
        return interactive.get("button", {}).get("text") or interactive.get("list_reply", {}).get("title", "")
    return ""


def _extract_attachments(msg: Dict[str, Any]) -> List[Dict[str, Any]]:
    attachments = []
    media_fields = ["image", "audio", "video", "document", "voice", "sticker"]
    for field in media_fields:
        if field in msg:
            media = msg[field]
            attachments.append(
                {
                    "type": field,
                    "id": media.get("id"),
                    "mime_type": media.get("mime_type"),
                    "sha256": media.get("sha256"),
                    "filename": media.get("filename"),
                }
            )
    return attachments


def normalize_whatsapp_payload(payload: Dict[str, Any], event_id: str = "") -> List[Dict[str, Any]]:
    """Normalize WhatsApp Cloud API webhook payload into internal message dicts."""
    normalized_messages: List[Dict[str, Any]] = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            contacts = value.get("contacts", [])
            sender_id = contacts[0].get("wa_id") if contacts else None
            for msg in value.get("messages", []) or []:
                external_message_id = msg.get("id") or ""
                external_id = msg.get("from") or sender_id or "unknown"
                message_type = msg.get("type") or "text"
                text = _extract_text(msg)
                attachments = _extract_attachments(msg)

                normalized_messages.append(
                    {
                        "channel": Channel.WHATSAPP,
                        "external_id": external_id,
                        "external_message_id": external_message_id,
                        "message_type": "voice" if message_type == "voice" else "text" if message_type == "text" else message_type,
                        "text": text,
                        "attachments": attachments,
                        "raw_payload": msg,
                        "external_event_id": event_id,
                    }
                )
    if not normalized_messages and payload:
        normalized_messages.append(
            {
                "channel": Channel.WHATSAPP,
                "external_id": "unknown",
                "message_type": "structured_event",
                "text": "",
                "attachments": [],
                "raw_payload": payload,
                "external_event_id": event_id,
            }
        )
    return normalized_messages
