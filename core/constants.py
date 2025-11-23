from django.db import models


class Channel(models.TextChoices):
    WHATSAPP = "whatsapp", "WhatsApp"
    FB_MESSENGER = "fb_messenger", "Facebook Messenger"
    SHOPIFY = "shopify", "Shopify"
    MAGENTO = "magento", "Magento"
    WEB = "web", "Web"


class ConversationStatus(models.TextChoices):
    OPEN = "open", "Open"
    PENDING = "pending", "Pending"
    RESOLVED = "resolved", "Resolved"
    ESCALATED = "escalated", "Escalated"


class MessageDirection(models.TextChoices):
    INBOUND = "inbound", "Inbound"
    OUTBOUND = "outbound", "Outbound"


class MessageType(models.TextChoices):
    TEXT = "text", "Text"
    IMAGE = "image", "Image"
    VOICE = "voice", "Voice"
    STRUCTURED = "structured_event", "Structured Event"


class TicketStatus(models.TextChoices):
    OPEN = "open", "Open"
    PENDING = "pending", "Pending"
    RESOLVED = "resolved", "Resolved"
    ESCALATED = "escalated", "Escalated"


class TicketType(models.TextChoices):
    COMPLAINT = "complaint", "Complaint"
    INQUIRY = "inquiry", "Inquiry"
    SUPPORT = "support_case", "Support Case"


class OrderSource(models.TextChoices):
    SHOPIFY = "shopify", "Shopify"
    MAGENTO = "magento", "Magento"
    CUSTOM = "custom", "Custom"


class PaymentStatus(models.TextChoices):
    INITIATED = "initiated", "Initiated"
    REQUIRES_ACTION = "requires_action", "Requires Action"
    SUCCEEDED = "succeeded", "Succeeded"
    FAILED = "failed", "Failed"
    CANCELED = "canceled", "Canceled"


class TransactionType(models.TextChoices):
    PAYMENT = "payment", "Payment"
    REFUND = "refund", "Refund"
    PARTIAL_REFUND = "partial_refund", "Partial Refund"


class SummaryType(models.TextChoices):
    LIFETIME = "lifetime", "Lifetime"
    LAST_90_DAYS = "last_90_days", "Last 90 Days"
    LAST_CASE = "last_case", "Last Case"


class KnowledgeSource(models.TextChoices):
    FAQ = "faq", "FAQ"
    POLICY = "policy", "Policy"
    PRODUCT = "product", "Product"
    HISTORICAL = "historical_conversation", "Historical Conversation"
    MANUAL = "manual", "Manual"


class FollowUpStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SENT = "sent", "Sent"
    CANCELED = "canceled", "Canceled"
    FAILED = "failed", "Failed"
