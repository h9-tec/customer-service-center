from django.db import models

from core.constants import (
    Channel,
    ConversationStatus,
    FollowUpStatus,
    MessageDirection,
    MessageType,
)
from core.models import BaseModel
from customers_app.models import Customer


class Conversation(BaseModel):
    customer = models.ForeignKey(
        Customer, related_name="conversations", on_delete=models.CASCADE
    )
    channel = models.CharField(max_length=32, choices=Channel.choices)
    agent = models.ForeignKey(
        "agents_app.AgentProfile",
        related_name="conversations",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=32, choices=ConversationStatus.choices, default=ConversationStatus.OPEN
    )
    metadata = models.JSONField(default=dict, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant_id", "channel", "status"]),
            models.Index(fields=["customer", "status"]),
        ]

    def __str__(self) -> str:
        return f"Conversation {self.id} ({self.channel})"


class Message(BaseModel):
    conversation = models.ForeignKey(
        Conversation, related_name="messages", on_delete=models.CASCADE
    )
    external_message_id = models.CharField(max_length=255, blank=True, default="")
    direction = models.CharField(max_length=16, choices=MessageDirection.choices)
    message_type = models.CharField(
        max_length=32, choices=MessageType.choices, default=MessageType.TEXT
    )
    raw_payload = models.JSONField(default=dict, blank=True)
    text = models.TextField(blank=True, null=True)
    attachments = models.JSONField(default=list, blank=True)
    llm_metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["conversation", "created_at"]),
            models.Index(fields=["tenant_id", "message_type"]),
            models.Index(fields=["external_message_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.direction} message {self.id}"


class FollowUpTask(BaseModel):
    customer = models.ForeignKey(
        Customer, related_name="followups", on_delete=models.CASCADE
    )
    conversation = models.ForeignKey(
        Conversation, related_name="followups", null=True, blank=True, on_delete=models.SET_NULL
    )
    topic = models.CharField(max_length=255)
    scheduled_for = models.DateTimeField()
    status = models.CharField(
        max_length=16, choices=FollowUpStatus.choices, default=FollowUpStatus.PENDING
    )
    channel = models.CharField(
        max_length=32, choices=Channel.choices, default=Channel.WHATSAPP
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant_id", "scheduled_for"]),
            models.Index(fields=["customer", "status"]),
        ]

    def __str__(self) -> str:
        return f"Follow-up {self.topic} for customer {self.customer_id}"
