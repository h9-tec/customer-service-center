import datetime

from celery import shared_task

from analytics_app.models import DailyKPI
from conversation_app.models import Conversation, Message
from llm_app.tool_logs import ToolCallLog
from llm_app.models import LLMInferenceLog
from commerce_app.models import PaymentIntent


@shared_task
def compute_daily_kpis(target_date: str = "") -> None:
    """Compute daily KPIs for a given date (YYYY-MM-DD). Default: yesterday."""
    if target_date:
        day = datetime.date.fromisoformat(target_date)
    else:
        day = datetime.date.today() - datetime.timedelta(days=1)

    start = datetime.datetime.combine(day, datetime.time.min).replace(tzinfo=None)
    end = datetime.datetime.combine(day, datetime.time.max).replace(tzinfo=None)

    conversations = Conversation.objects.filter(created_at__range=(start, end))
    total = conversations.count()
    if total == 0:
        DailyKPI.objects.update_or_create(
            date=day, channel="", agent_id=None, defaults={"total_conversations": 0}
        )
        return

    # Simple metrics stubs
    resolved = conversations.filter(status="resolved").count()
    resolution_rate = resolved / total
    deflected = conversations.filter(status="resolved", agent__isnull=True).count()
    deflection_rate = deflected / total
    aht_seconds = 0
    for convo in conversations:
        msgs = Message.objects.filter(conversation=convo).order_by("created_at")
        if msgs.exists():
            duration = (msgs.last().created_at - msgs.first().created_at).total_seconds()
            aht_seconds += duration
    aht_seconds = (aht_seconds / total) if total else 0

    tool_calls = ToolCallLog.objects.filter(created_at__range=(start, end))
    tool_call_counts = {}
    success_calls = 0
    for tc in tool_calls:
        tool_call_counts[tc.tool_name] = tool_call_counts.get(tc.tool_name, 0) + 1
        if tc.success:
            success_calls += 1
    total_tool_calls = tool_calls.count()
    tool_success_rate = (success_calls / total_tool_calls) if total_tool_calls else 0

    payments = PaymentIntent.objects.filter(created_at__range=(start, end))
    conversion = payments.filter(status="succeeded").count()
    payment_conversion_rate = (conversion / payments.count()) if payments.count() else 0

    llm_logs = LLMInferenceLog.objects.filter(created_at__range=(start, end))
    avg_llm_latency_ms = (
        sum([log.latency_ms or 0 for log in llm_logs]) / llm_logs.count() if llm_logs.count() else 0
    )

    DailyKPI.objects.update_or_create(
        date=day,
        channel="",
        agent_id=None,
        defaults={
            "total_conversations": total,
            "resolution_rate": resolution_rate,
            "deflection_rate": deflection_rate,
            "aht_seconds": aht_seconds,
            "tool_call_counts": tool_call_counts,
            "total_tool_calls": total_tool_calls,
            "tool_success_rate": tool_success_rate,
            "payment_conversion_rate": payment_conversion_rate,
            "avg_llm_latency_ms": avg_llm_latency_ms,
        },
    )
