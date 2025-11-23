from django.db import models

from core.constants import Channel
from core.models import BaseModel
from customers_app.utils import encrypt_pii, decrypt_pii


class Customer(BaseModel):
    primary_email = models.EmailField(blank=True, null=True)
    primary_phone = models.CharField(max_length=32, blank=True, null=True)
    attributes = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return f"Customer {self.id}"

    def save(self, *args, **kwargs):
        # Optionally encrypt email/phone at rest if ENCRYPTION_KEY is configured.
        if self.primary_email:
            self.primary_email = encrypt_pii(self.primary_email)
        if self.primary_phone:
            self.primary_phone = encrypt_pii(self.primary_phone)
        super().save(*args, **kwargs)

    @property
    def decrypted_email(self) -> str:
        return decrypt_pii(self.primary_email or "")

    @property
    def decrypted_phone(self) -> str:
        return decrypt_pii(self.primary_phone or "")


class CustomerIdentity(BaseModel):
    customer = models.ForeignKey(
        Customer, related_name="identities", on_delete=models.CASCADE
    )
    channel = models.CharField(max_length=32, choices=Channel.choices)
    external_id = models.CharField(max_length=128)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = (("tenant_id", "channel", "external_id"),)
        indexes = [
            models.Index(fields=["tenant_id", "channel", "external_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.channel}:{self.external_id}"
