from typing import Any, Dict, List, Optional

from commerce_app.models import Order, PaymentIntent, Ticket
from conversation_app.models import Conversation


def list_customer_orders(customer_id: int) -> List[Dict[str, Any]]:
    orders = (
        Order.objects.filter(customer_id=customer_id)
        .order_by("-created_at")[:10]
        .values("id", "external_order_id", "status", "total", "currency", "source", "details")
    )
    return list(orders)


def refund_order(order_id: int, amount: Optional[float] = None) -> Dict[str, Any]:
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return {"error": "order_not_found"}
    # Stub refund logic with audit readiness
    return {"status": "queued", "order_id": order.id, "amount": float(amount) if amount else None}


def create_payment_intent(customer_id: int, amount: float, currency: str = "USD", order_id: Optional[int] = None) -> Dict[str, Any]:
    intent = PaymentIntent.objects.create(
        customer_id=customer_id,
        order_id=order_id,
        amount=amount,
        currency=currency,
        status="initiated",
    )
    return {"payment_intent_id": intent.id, "status": intent.status}


def schedule_followup(conversation_id: int, topic: str) -> Dict[str, Any]:
    try:
        Conversation.objects.get(id=conversation_id)
    except Conversation.DoesNotExist:
        return {"error": "conversation_not_found"}
    # Stub follow-up scheduling
    return {"status": "scheduled", "conversation_id": conversation_id, "topic": topic}


def update_order_status(order_id: int, status: str) -> Dict[str, Any]:
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return {"error": "order_not_found"}
    order.status = status
    order.save(update_fields=["status"])
    return {"order_id": order.id, "status": order.status}


def capture_payment_intent(payment_intent_id: int) -> Dict[str, Any]:
    try:
        intent = PaymentIntent.objects.get(id=payment_intent_id)
    except PaymentIntent.DoesNotExist:
        return {"error": "payment_intent_not_found"}
    intent.status = "succeeded"
    intent.save(update_fields=["status"])
    return {"payment_intent_id": intent.id, "status": intent.status}
