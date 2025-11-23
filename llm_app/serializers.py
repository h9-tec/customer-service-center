from rest_framework import serializers

from llm_app.tool_logs import ToolCallLog


class ToolCallLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ToolCallLog
        fields = ["id", "tool_name", "arguments", "result", "success", "created_at", "updated_at"]
