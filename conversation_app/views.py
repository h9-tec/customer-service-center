from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from conversation_app.services import handle_normalized_message
from conversation_app import serializers
from conversation_app.models import Conversation, Message
from rest_framework import generics, permissions


class NormalizedMessageView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        handle_normalized_message(request.data)
        return Response({"status": "accepted"}, status=status.HTTP_202_ACCEPTED)


class ConversationListView(generics.ListAPIView):
    serializer_class = serializers.ConversationSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        qs = Conversation.objects.all().order_by("-created_at")
        channel = self.request.query_params.get("channel")
        status_filter = self.request.query_params.get("status")
        created_after = self.request.query_params.get("created_after")
        created_before = self.request.query_params.get("created_before")
        if channel:
            qs = qs.filter(channel=channel)
        if status_filter:
            qs = qs.filter(status=status_filter)
        if created_after:
            qs = qs.filter(created_at__gte=created_after)
        if created_before:
            qs = qs.filter(created_at__lte=created_before)
        return qs


class MessageListView(generics.ListAPIView):
    serializer_class = serializers.MessageSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        conversation_id = self.kwargs.get("conversation_id")
        return Message.objects.filter(conversation_id=conversation_id).order_by("created_at")
