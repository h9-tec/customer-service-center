from rest_framework import serializers

from agents_app.models import AgentProfile
from agents_app.models_prompt import AgentPromptVersion
from analytics_app.models import AuditLog
from core.utils import mask_payload


class AgentProfileSerializer(serializers.ModelSerializer):
    def validate_routing_rules(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("routing_rules must be a JSON object.")
        channels = value.get("channel") or value.get("channels") or []
        languages = value.get("language") or value.get("languages") or []
        if channels and not isinstance(channels, (list, tuple)):
            raise serializers.ValidationError("channels must be a list.")
        if languages and not isinstance(languages, (list, tuple)):
            raise serializers.ValidationError("languages must be a list.")
        return value

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        AuditLog.objects.create(
            event_type="agent_profile_updated",
            actor=str(self.context.get("request").user) if self.context.get("request") else "",
            target=str(instance.id),
            payload=mask_payload({"routing_rules": instance.routing_rules, "model": instance.model_name}),
        )
        return instance

    class Meta:
        model = AgentProfile
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "system_prompt",
            "tool_schema",
            "allowed_channels",
            "routing_rules",
            "model_backend",
            "model_name",
            "temperature",
            "max_tokens",
            "is_active",
            "metadata",
            "created_at",
            "updated_at",
        ]


class AgentPromptVersionSerializer(serializers.ModelSerializer):
    agent_id = serializers.IntegerField(source="agent.id", read_only=True)

    class Meta:
        model = AgentPromptVersion
        fields = ["id", "agent_id", "version", "system_prompt", "metadata", "created_at"]
