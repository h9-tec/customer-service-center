from rest_framework import serializers

from customers_app.models import Customer
from commerce_app.models import Order, Ticket
from conversation_app.models import Conversation, Message


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "decrypted_email", "decrypted_phone", "attributes", "created_at", "updated_at"]


class TimelineEventSerializer(serializers.Serializer):
    type = serializers.CharField()
    id = serializers.CharField()
    created_at = serializers.DateTimeField()
    payload = serializers.JSONField()
