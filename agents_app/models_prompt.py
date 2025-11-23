from django.db import models

from core.models import BaseModel
from agents_app.models import AgentProfile


class AgentPromptVersion(BaseModel):
    agent = models.ForeignKey(
        AgentProfile, related_name="prompt_versions", on_delete=models.CASCADE
    )
    version = models.IntegerField()
    system_prompt = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = (("agent", "version"),)
        ordering = ["-version"]
