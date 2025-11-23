from django.db import models

from core.models import BaseModel


class AgentProfile(BaseModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    description = models.TextField(blank=True)
    system_prompt = models.TextField()
    tool_schema = models.JSONField(default=dict, blank=True)
    allowed_channels = models.JSONField(default=list, blank=True)
    routing_rules = models.JSONField(default=dict, blank=True)
    model_backend = models.CharField(max_length=32, default="vllm")
    model_name = models.CharField(max_length=255, default="qwen2.5-14b-instruct")
    temperature = models.FloatField(default=0.2)
    max_tokens = models.IntegerField(default=512)
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = (("tenant_id", "slug"),)
        indexes = [
            models.Index(fields=["tenant_id", "slug"]),
            models.Index(fields=["tenant_id", "is_active"]),
            models.Index(fields=["routing_rules"]),
        ]

    def __str__(self) -> str:
        return self.name
