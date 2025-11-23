from django.db import models

from core.models import BaseModel


class ToolCallLog(BaseModel):
    tool_name = models.CharField(max_length=128)
    arguments = models.JSONField(default=dict, blank=True)
    result = models.JSONField(default=dict, blank=True)
    success = models.BooleanField(default=True)
    message = models.ForeignKey(
        "conversation_app.Message", related_name="tool_calls", on_delete=models.CASCADE, null=True, blank=True
    )

    class Meta:
        indexes = [
            models.Index(fields=["tool_name", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.tool_name} @ {self.created_at}"
