import json
import logging
from typing import Any, Dict, Optional

import requests
from django.conf import settings

from agents_app.models import AgentProfile
from channels_app.senders import send_whatsapp_text
from channels_app.tasks import download_media, transcribe_voice, generate_tts
from customers_app.models import Customer, CustomerIdentity
from core.constants import Channel
from commerce_app import tools as commerce_tools
from commerce_app.models import Order, Ticket
from conversation_app.models import Conversation, Message
from llm_app.tool_logs import ToolCallLog
from analytics_app.models import AuditLog
from core.utils import mask_payload
from core.metrics import LLM_REQUESTS, LLM_LATENCY, ASR_REQUESTS, ASR_LATENCY, TOOL_CALLS
from channels_app.whatsapp_media import upload_media
from core.constants import Channel

logger = logging.getLogger(__name__)


def resolve_customer(channel: str, external_id: str) -> Customer:
    """Resolve or create a customer by channel + external id."""
    identity, _ = CustomerIdentity.objects.get_or_create(
        channel=channel, external_id=external_id, defaults={"customer": Customer.objects.create()}
    )
    return identity.customer


def handle_normalized_message(normalized: Dict[str, Any]) -> None:
    """Stub orchestrator entry point; persists minimal conversation/message data."""
    channel = normalized.get("channel") or Channel.WEB
    external_id = normalized.get("external_id") or normalized.get("user_id") or "unknown"
    external_message_id = normalized.get("external_message_id") or ""
    customer = resolve_customer(channel, external_id)

    conversation, _ = Conversation.objects.get_or_create(
        customer=customer,
        channel=channel,
        status="open",
        defaults={"metadata": {"source": "webhook"}},
    )

    if external_message_id and Message.objects.filter(external_message_id=external_message_id).exists():
        logger.info("Duplicate message %s ignored.", external_message_id)
        return

    message = Message.objects.create(
        conversation=conversation,
        direction="inbound",
        message_type=normalized.get("message_type", "text"),
        external_message_id=external_message_id,
        raw_payload=normalized,
        text=normalized.get("text", ""),
        attachments=normalized.get("attachments", []),
        llm_metadata=normalized.get("llm_metadata", {}),
    )

    logger.info("Accepted normalized message on channel %s for customer %s", channel, customer.id)

    # Media/voice handling stubs
    for attachment in normalized.get("attachments", []):
        media_id = attachment.get("id")
        if media_id:
            res = download_media.delay(media_id, attachment.get("mime_type"), message.id)
            logger.info("Scheduled media download task %s for media %s", res.id, media_id)

    if channel == Channel.WHATSAPP and normalized.get("text"):
        orchestrate_reply(conversation, external_id=external_id, inbound_text=normalized["text"])


def send_outbound_message(channel: str, external_id: str, text: str):
    """Create or reuse conversation, log outbound message, and return context for sender."""
    customer = resolve_customer(channel, external_id)
    conversation, _ = Conversation.objects.get_or_create(
        customer=customer,
        channel=channel,
        status="open",
        defaults={"metadata": {"source": "outbound"}},
    )

    message = Message.objects.create(
        conversation=conversation,
        direction="outbound",
        message_type="text",
        text=text,
        raw_payload={"text": text},
    )

    logger.info(
        "Queued outbound message %s on channel %s to external_id %s", message.id, channel, external_id
    )
    ctx = {"conversation_id": conversation.id, "message_id": message.id, "customer_id": customer.id}
    return ctx, message


def orchestrate_reply(conversation: Conversation, external_id: str, inbound_text: str) -> None:
    """Minimal orchestrator: choose agent, call LLM router, validate tools, persist + send reply."""
    agent = _select_agent(conversation)
    if not agent:
        logger.warning("No active agent configured; skipping reply.")
        return

    context_text = build_context(conversation)
    llm_response = _call_llm_router(agent, inbound_text, context_text)
    if not llm_response:
        logger.warning("LLM router returned empty response; skipping outbound send.")
        return

    tool_result_text = None
    parsed = parse_tool_call(llm_response)
    final_text = llm_response
    if parsed:
        allowed = agent.tool_schema.get("allowed_tools") if isinstance(agent.tool_schema, dict) else None
        if allowed and parsed["tool"] not in allowed:
            tool_result_text = f"Tool {parsed['tool']} is not allowed."
        else:
            tool_output = execute_tool(parsed["tool"], parsed.get("arguments", {}), conversation, agent)
            tool_result_text = f"Tool {parsed['tool']} result: {tool_output}"
            final_text = parsed.get("final_answer") or tool_result_text

    outbound = Message.objects.create(
        conversation=conversation,
        direction="outbound",
        message_type="text",
        text=final_text,
        llm_metadata={"agent_id": agent.id, "model": agent.model_name},
        raw_payload={"llm_output": llm_response, "tool_result": tool_result_text},
    )

    if conversation.channel == Channel.WHATSAPP:
        send_result = send_whatsapp_text(to=external_id, body=final_text)
        outbound.raw_payload.update({"send_result": send_result})
        outbound.save(update_fields=["raw_payload"])
        generate_tts.delay(final_text, outbound.id)
    logger.info("Sent outbound reply message %s for conversation %s", outbound.id, conversation.id)


def _get_default_agent() -> Optional[AgentProfile]:
    agent = AgentProfile.objects.filter(is_active=True).order_by("created_at").first()
    if agent:
        return agent
    return AgentProfile.objects.create(
        name="Default Support Agent",
        slug="default-support-agent",
        system_prompt="You are a helpful customer support agent. Be concise and polite.",
        tool_schema={},
        allowed_channels=[Channel.WHATSAPP],
        routing_rules={},
        model_backend="ollama",
        model_name="llama3.2:3b",
        temperature=0.2,
        max_tokens=256,
        is_active=True,
    )


def _select_agent(conversation: Conversation) -> Optional[AgentProfile]:
    # Simple routing: match channel or language in routing_rules JSON; fallback to default.
    language = detect_language(conversation)
    channel = conversation.channel
    qs = AgentProfile.objects.filter(is_active=True)
    matched = []
    for agent in qs:
        rules = agent.routing_rules or {}
        channels = rules.get("channel") or rules.get("channels") or []
        languages = rules.get("language") or rules.get("languages") or []
        if (channels and channel in channels) or (languages and language in languages):
            matched.append(agent)
    if matched:
        return matched[0]
    return _get_default_agent()


def _call_llm_router(agent: AgentProfile, user_text: str, context: str = "") -> Optional[str]:
    url = f"{settings.LLM_ROUTER_URL}/llm/infer"
    payload = {
        "backend": agent.model_backend,
        "model": agent.model_name,
        "messages": [
            {
                "role": "system",
                "content": f"{agent.system_prompt}\n\nContext:\n{context}\n\nIf you need to use a tool, respond as JSON: {{\"tool\":\"<name>\",\"arguments\":{{...}},\"final_answer\":\"<text>\"}}. Tools available: list_customer_orders, refund_order, create_payment_intent, schedule_followup.",
            },
            {"role": "user", "content": user_text},
        ],
        "temperature": agent.temperature,
        "max_tokens": agent.max_tokens,
    }
    LLM_REQUESTS.labels(backend=agent.model_backend, model=agent.model_name).inc()
    with LLM_LATENCY.labels(backend=agent.model_backend, model=agent.model_name).time():
        try:
            resp = requests.post(url, json=payload, timeout=15)
            if not resp.ok:
                logger.error("LLM router error %s: %s", resp.status_code, resp.text)
                return None
            data = resp.json()
            return data.get("output") or None
        except Exception as exc:  # noqa: broad-except
            logger.exception("Failed to call LLM router: %s", exc)
            return None


def build_context(conversation: Conversation) -> str:
    customer = conversation.customer
    language = detect_language(conversation)
    recent_msgs = (
        Message.objects.filter(conversation=conversation).order_by("-created_at")[:5][::-1]
    )
    orders = (
        Order.objects.filter(customer=customer)
        .order_by("-created_at")
        .values("external_order_id", "status", "total", "currency")[:5]
    )
    tickets = (
        Ticket.objects.filter(customer=customer)
        .order_by("-created_at")
        .values("id", "status", "summary")[:5]
    )
    ctx_parts = [
        f"Customer ID: {customer.id}",
        f"Attributes: {customer.attributes}",
        f"Language: {language}",
        "Recent messages:",
    ]
    for m in recent_msgs:
        ctx_parts.append(f"- {m.direction}: {m.text}")
    if orders:
        ctx_parts.append("Recent orders:")
        for o in orders:
            ctx_parts.append(f"- {o['external_order_id']} {o['status']} {o['total']} {o['currency']}")
    if tickets:
        ctx_parts.append("Tickets:")
        for t in tickets:
            ctx_parts.append(f"- {t['id']} {t['status']} {t['summary']}")
    return "\n".join(ctx_parts)


def detect_language(conversation: Conversation) -> str:
    last_msg = (
        Message.objects.filter(conversation=conversation, direction="inbound")
        .order_by("-created_at")
        .first()
    )
    text = last_msg.text if last_msg else ""
    # Simple heuristic: presence of Arabic characters
    for ch in text or "":
        if "\u0600" <= ch <= "\u06FF":
            return "ar"
    return "en"


def parse_tool_call(raw: str) -> Optional[Dict[str, Any]]:
    try:
        data = json.loads(raw)
        if isinstance(data, dict) and "tool" in data:
            return data
    except Exception:
        return None
    return None


def execute_tool(tool_name: str, args: Dict[str, Any], conversation: Optional[Conversation] = None, agent: Optional[AgentProfile] = None) -> Any:
    registry = {
        "list_customer_orders": lambda: commerce_tools.list_customer_orders(args.get("customer_id")),
        "refund_order": lambda: commerce_tools.refund_order(args.get("order_id"), args.get("amount")),
        "create_payment_intent": lambda: commerce_tools.create_payment_intent(
            args.get("customer_id"), args.get("amount"), args.get("currency", "USD"), args.get("order_id")
        ),
        "schedule_followup": lambda: commerce_tools.schedule_followup(
            args.get("conversation_id"), args.get("topic", "")
        ),
        "update_order_status": lambda: commerce_tools.update_order_status(args.get("order_id"), args.get("status")),
        "capture_payment_intent": lambda: commerce_tools.capture_payment_intent(args.get("payment_intent_id")),
    }
    if tool_name not in registry:
        TOOL_CALLS.labels(tool=tool_name, success=False).inc()
        return {"error": "unknown_tool"}
    if tool_name in ("refund_order", "create_payment_intent"):
        required = ["customer_id"]
        missing = [r for r in required if not args.get(r)]
        if missing:
            TOOL_CALLS.labels(tool=tool_name, success=False).inc()
            return {"error": "missing_args", "missing": missing}
        if not args.get("confirmed"):
            TOOL_CALLS.labels(tool=tool_name, success=False).inc()
            return {"error": "confirmation_required"}
    if tool_name in ("update_order_status", "capture_payment_intent") and not args.get("confirmed"):
        TOOL_CALLS.labels(tool=tool_name, success=False).inc()
        return {"error": "confirmation_required"}
    try:
        result = registry[tool_name]()
        if tool_name in ("refund_order", "create_payment_intent"):
            AuditLog.objects.create(
                event_type=tool_name,
                actor="llm_orchestrator",
                target=str(args.get("order_id") or args.get("customer_id") or ""),
                payload=mask_payload({"args": args, "result": result}),
            )
            ToolCallLog.objects.create(
                tool_name=tool_name,
                arguments=args,
                result=result if isinstance(result, dict) else {"result": result},
                success="error" not in (result or {}),
            )
        TOOL_CALLS.labels(tool=tool_name, success="error" not in (result or {})).inc()
        return result
    except Exception as exc:  # noqa: broad-except
        logger.exception("Tool %s failed: %s", tool_name, exc)
        ToolCallLog.objects.create(
            tool_name=tool_name,
            arguments=args,
            result={"error": str(exc)},
            success=False,
        )
        TOOL_CALLS.labels(tool=tool_name, success=False).inc()
        return {"error": "tool_failed", "message": str(exc)}
