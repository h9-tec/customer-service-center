from rest_framework import serializers

from conversation_app.models import Conversation, Message


class ConversationSerializer(serializers.ModelSerializer):
    customer_id = serializers.IntegerField(source="customer.id", read_only=True)

    class Meta:
        model = Conversation
        fields = [
            "id",
            "customer_id",
            "channel",
            "agent_id",
            "status",
            "metadata",
            "created_at",
            "closed_at",
        ]


class MessageSerializer(serializers.ModelSerializer):
    conversation_id = serializers.IntegerField(source="conversation.id", read_only=True)

    class Meta:
        model = Message
        fields = [
            "id",
            "conversation_id",
            "external_message_id",
            "direction",
            "message_type",
            "text",
            "attachments",
            "llm_metadata",
            "created_at",
        ]
