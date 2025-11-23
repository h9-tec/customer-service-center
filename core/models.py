from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TenantScopedModel(models.Model):
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)

    class Meta:
        abstract = True


class BaseModel(TenantScopedModel, TimeStampedModel):
    """Shared base for tenant-aware records with timestamps."""

    class Meta:
        abstract = True
