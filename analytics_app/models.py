from django.db import models

from core.models import BaseModel


class AnalyticsEvent(BaseModel):
    event_type = models.CharField(max_length=128)
    actor = models.CharField(max_length=128, blank=True)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant_id", "event_type"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.event_type} at {self.created_at}"


class DailyKPI(BaseModel):
    date = models.DateField()
    channel = models.CharField(max_length=64, blank=True)
    agent_id = models.IntegerField(null=True, blank=True)
    resolution_rate = models.FloatField(default=0.0)
    deflection_rate = models.FloatField(default=0.0)
    aht_seconds = models.FloatField(default=0.0)
    tool_call_counts = models.JSONField(default=dict, blank=True)
    total_tool_calls = models.IntegerField(default=0)
    tool_success_rate = models.FloatField(default=0.0)
    payment_conversion_rate = models.FloatField(default=0.0)
    model_backend = models.CharField(max_length=64, blank=True)
    model_name = models.CharField(max_length=255, blank=True)
    avg_llm_latency_ms = models.FloatField(default=0.0)
    total_conversations = models.IntegerField(default=0)

    class Meta:
        unique_together = (("tenant_id", "date", "channel", "agent_id"),)
        indexes = [
            models.Index(fields=["date"]),
            models.Index(fields=["channel"]),
            models.Index(fields=["agent_id"]),
        ]

    def __str__(self) -> str:
        return f"KPI {self.date} {self.channel or 'all'}"


class AuditLog(BaseModel):
    event_type = models.CharField(max_length=128)
    actor = models.CharField(max_length=128, blank=True)
    target = models.CharField(max_length=128, blank=True)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["event_type", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.event_type} at {self.created_at}"
