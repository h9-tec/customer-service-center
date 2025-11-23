from typing import Dict

from commerce_app.models import Order
from customers_app.models import Customer, CustomerIdentity
from core.constants import Channel, OrderSource


def upsert_customer_and_order(magento_payload: Dict) -> None:
    customer_data = magento_payload.get("customer") or {}
    email = customer_data.get("email")
    phone = customer_data.get("telephone")
    customer, _ = Customer.objects.get_or_create(
        primary_email=email,
        defaults={"primary_phone": phone},
    )
    CustomerIdentity.objects.get_or_create(
        customer=customer,
        channel=Channel.MAGENTO,
        external_id=str(customer_data.get("id") or email or phone or ""),
    )
    order_data = magento_payload.get("order") or magento_payload
    order_id = order_data.get("entity_id") or order_data.get("increment_id")
    if order_id:
        updated_at = order_data.get("updated_at")
        existing = Order.objects.filter(external_order_id=str(order_id), source=OrderSource.MAGENTO).first()
        if existing and updated_at and existing.details.get("updated_at") == updated_at:
            return
        Order.objects.update_or_create(
            external_order_id=str(order_id),
            source=OrderSource.MAGENTO,
            defaults={
                "customer": customer,
                "status": order_data.get("status") or "",
                "total": order_data.get("grand_total") or 0,
                "currency": order_data.get("order_currency_code") or "USD",
                "details": order_data,
            },
        )
