from django.db import models

from core.constants import KnowledgeSource, SummaryType
from core.models import BaseModel
from customers_app.models import Customer


class KnowledgeDocument(BaseModel):
    title = models.CharField(max_length=255)
    source = models.CharField(
        max_length=64, choices=KnowledgeSource.choices, default=KnowledgeSource.MANUAL
    )
    metadata = models.JSONField(default=dict, blank=True)
    storage_uri = models.CharField(max_length=512, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant_id", "source"]),
        ]

    def __str__(self) -> str:
        return self.title


class UserMemorySummary(BaseModel):
    customer = models.ForeignKey(
        Customer, related_name="memory_summaries", on_delete=models.CASCADE
    )
    summary_type = models.CharField(
        max_length=32, choices=SummaryType.choices, default=SummaryType.LIFETIME
    )
    content = models.TextField()
    structured_metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = (("tenant_id", "customer", "summary_type"),)
        indexes = [
            models.Index(fields=["customer", "summary_type"]),
        ]

    def __str__(self) -> str:
        return f"Memory {self.summary_type} for customer {self.customer_id}"
