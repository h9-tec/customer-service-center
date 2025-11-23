from django.db import models

from core.constants import Channel
from core.models import BaseModel


class WebhookEvent(BaseModel):
    channel = models.CharField(max_length=32, choices=Channel.choices)
    external_event_id = models.CharField(max_length=255, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    processed = models.BooleanField(default=False)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant_id", "channel", "external_event_id"]),
            models.Index(fields=["processed"]),
        ]
        unique_together = (("tenant_id", "channel", "external_event_id"),)

    def __str__(self) -> str:
        return f"Webhook {self.channel} {self.external_event_id}"
