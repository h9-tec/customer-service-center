from django.db import models

from core.constants import (
    OrderSource,
    PaymentStatus,
    TicketStatus,
    TicketType,
    TransactionType,
)
from core.models import BaseModel
from customers_app.models import Customer


class Order(BaseModel):
    customer = models.ForeignKey(
        Customer, related_name="orders", on_delete=models.CASCADE
    )
    source = models.CharField(
        max_length=32, choices=OrderSource.choices, default=OrderSource.CUSTOM
    )
    external_order_id = models.CharField(max_length=128, blank=True)
    status = models.CharField(max_length=64, default="pending")
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=8, default="USD")
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant_id", "source", "external_order_id"]),
            models.Index(fields=["customer", "status"]),
        ]

    def __str__(self) -> str:
        return f"Order {self.external_order_id or self.id}"


class PaymentIntent(BaseModel):
    customer = models.ForeignKey(
        Customer, related_name="payment_intents", on_delete=models.CASCADE
    )
    order = models.ForeignKey(
        Order, related_name="payment_intents", null=True, blank=True, on_delete=models.SET_NULL
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=8, default="USD")
    status = models.CharField(
        max_length=32, choices=PaymentStatus.choices, default=PaymentStatus.INITIATED
    )
    provider_reference = models.CharField(max_length=128, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant_id", "status"]),
            models.Index(fields=["customer", "status"]),
        ]

    def __str__(self) -> str:
        return f"PaymentIntent {self.id}"


class Transaction(BaseModel):
    payment_intent = models.ForeignKey(
        PaymentIntent, related_name="transactions", on_delete=models.CASCADE
    )
    transaction_type = models.CharField(
        max_length=32, choices=TransactionType.choices, default=TransactionType.PAYMENT
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=8, default="USD")
    status = models.CharField(
        max_length=32, choices=PaymentStatus.choices, default=PaymentStatus.INITIATED
    )
    raw_response = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant_id", "transaction_type"]),
            models.Index(fields=["payment_intent", "status"]),
        ]

    def __str__(self) -> str:
        return f"Transaction {self.id}"


class Ticket(BaseModel):
    customer = models.ForeignKey(
        Customer, related_name="tickets", on_delete=models.CASCADE
    )
    conversation = models.ForeignKey(
        "conversation_app.Conversation",
        related_name="tickets",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    type = models.CharField(
        max_length=32, choices=TicketType.choices, default=TicketType.SUPPORT
    )
    status = models.CharField(
        max_length=32, choices=TicketStatus.choices, default=TicketStatus.OPEN
    )
    assigned_to = models.CharField(max_length=128, blank=True)
    summary = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant_id", "status"]),
            models.Index(fields=["customer", "status"]),
        ]

    def __str__(self) -> str:
        return f"Ticket {self.id}"
