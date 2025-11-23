from django.db import models

from core.models import BaseModel


class LLMInferenceLog(BaseModel):
    agent = models.ForeignKey(
        "agents_app.AgentProfile",
        related_name="llm_calls",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    model_backend = models.CharField(max_length=32)
    model_name = models.CharField(max_length=255)
    request_payload = models.JSONField(default=dict, blank=True)
    response_payload = models.JSONField(default=dict, blank=True)
    latency_ms = models.IntegerField(null=True, blank=True)
    success = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant_id", "model_backend"]),
            models.Index(fields=["agent", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"LLM call {self.id} ({self.model_backend})"
