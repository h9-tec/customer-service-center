from rest_framework import serializers

from analytics_app.models import DailyKPI
from analytics_app.models import AuditLog


class DailyKPISerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyKPI
        fields = [
            "id",
            "date",
            "channel",
            "agent_id",
            "resolution_rate",
            "deflection_rate",
            "aht_seconds",
            "tool_call_counts",
            "payment_conversion_rate",
            "model_backend",
            "model_name",
            "avg_llm_latency_ms",
            "total_conversations",
        ]


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ["id", "event_type", "actor", "target", "payload", "created_at"]
