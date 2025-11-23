import base64
import hashlib
import hmac
import json
from typing import Dict

from django.conf import settings

from commerce_app.models import Order
from customers_app.models import Customer, CustomerIdentity
from core.constants import Channel, OrderSource


def validate_hmac(request_body: bytes, header_hmac: str) -> bool:
    secret = settings.SHOPIFY_SHARED_SECRET
    if not secret or not header_hmac:
        return False
    digest = hmac.new(secret.encode(), request_body, hashlib.sha256).digest()
    computed = base64.b64encode(digest).decode()
    return hmac.compare_digest(computed, header_hmac)


def upsert_customer_and_order(shop_payload: Dict) -> None:
    customer_data = shop_payload.get("customer") or {}
    email = customer_data.get("email")
    phone = customer_data.get("phone")
    customer, _ = Customer.objects.get_or_create(
        primary_email=email,
        defaults={"primary_phone": phone},
    )
    CustomerIdentity.objects.get_or_create(
        customer=customer,
        channel=Channel.SHOPIFY,
        external_id=str(customer_data.get("id") or email or phone or ""),
    )
    order_id = shop_payload.get("id")
    if order_id:
        updated_at = shop_payload.get("updated_at")
        existing = Order.objects.filter(external_order_id=str(order_id), source=OrderSource.SHOPIFY).first()
        if existing and updated_at and existing.details.get("updated_at") == updated_at:
            return
        Order.objects.update_or_create(
            external_order_id=str(order_id),
            source=OrderSource.SHOPIFY,
            defaults={
                "customer": customer,
                "status": shop_payload.get("financial_status") or "",
                "total": shop_payload.get("total_price") or 0,
                "currency": shop_payload.get("currency") or "USD",
                "details": shop_payload,
            },
        )
