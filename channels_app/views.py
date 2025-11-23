import os
from html import escape

from django.http import HttpResponse
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from channels_app.models import WebhookEvent
from channels_app.normalizers import normalize_whatsapp_payload
from channels_app.senders import send_whatsapp_text
from channels_app.shopify import upsert_customer_and_order as shopify_upsert, validate_hmac
from channels_app.magento import upsert_customer_and_order as magento_upsert
from channels_app.utils import verify_meta_signature, is_ip_allowed
from core.auth import APIKeyPermission
from core.constants import Channel
from core.metrics import WEBHOOK_REQUESTS
from conversation_app.models import Conversation, Message
from conversation_app.services import handle_normalized_message, send_outbound_message


class WhatsAppWebhookView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        """Verification endpoint for Meta webhook setup."""
        mode = request.query_params.get("hub.mode")
        token = request.query_params.get("hub.verify_token")
        challenge = request.query_params.get("hub.challenge")
        verify_token = os.environ.get("WHATSAPP_VERIFY_TOKEN")
        if mode == "subscribe" and verify_token and token == verify_token:
            return Response(challenge, status=status.HTTP_200_OK)
        return Response({"detail": "verification failed"}, status=status.HTTP_403_FORBIDDEN)

    def post(self, request, *args, **kwargs):
        if not is_ip_allowed(request):
            return Response({"detail": "ip_not_allowed"}, status=status.HTTP_403_FORBIDDEN)
        signature = request.headers.get("X-Hub-Signature-256") or request.headers.get("X-Hub-Signature")
        if not verify_meta_signature(request.body, signature):
            return Response({"detail": "invalid signature"}, status=status.HTTP_401_UNAUTHORIZED)
        payload = request.data
        event_id = str(payload.get("id") or payload.get("entry", [{}])[0].get("id", ""))
        # Deduplicate on external_event_id if provided
        if event_id and WebhookEvent.objects.filter(
            channel=Channel.WHATSAPP, external_event_id=event_id
        ).exists():
            WEBHOOK_REQUESTS.labels(channel=Channel.WHATSAPP, status="duplicate").inc()
            return Response({"status": "duplicate_skipped"}, status=status.HTTP_202_ACCEPTED)

        event = WebhookEvent.objects.create(
            channel=Channel.WHATSAPP, payload=payload, external_event_id=event_id
        )
        normalized_messages = normalize_whatsapp_payload(payload, event_id=event.external_event_id)
        for message in normalized_messages:
            handle_normalized_message(message)
        WEBHOOK_REQUESTS.labels(channel=Channel.WHATSAPP, status="accepted").inc()
        return Response({"status": "accepted"}, status=status.HTTP_202_ACCEPTED)


class OutboundWhatsAppMessageView(APIView):
    permission_classes = [IsAuthenticated | APIKeyPermission]

    def post(self, request, *args, **kwargs):
        to = request.data.get("to")
        body = request.data.get("body")
        if not to or not body:
            return Response({"detail": "to and body are required"}, status=status.HTTP_400_BAD_REQUEST)
        ctx, message = send_outbound_message(channel=Channel.WHATSAPP, external_id=to, text=body)
        result = send_whatsapp_text(to=to, body=body)
        message.raw_payload.update({"send_result": result})
        message.save(update_fields=["raw_payload"])
        result.update(ctx)
        return Response(
            result,
            status=status.HTTP_200_OK if result.get("sent") else status.HTTP_502_BAD_GATEWAY,
        )


def whatsapp_messages_html(request):
    """Chat-style HTML showing WhatsApp conversation (user vs AI) from DB."""
    conversation_id = request.GET.get("conversation_id")
    conversation = None
    if conversation_id:
        conversation = Conversation.objects.filter(
            id=conversation_id, channel=Channel.WHATSAPP
        ).first()
    if not conversation:
        conversation = (
            Conversation.objects.filter(channel=Channel.WHATSAPP)
            .order_by("-created_at")
            .first()
        )
    if not conversation:
        return HttpResponse("<p>No WhatsApp conversations found.</p>")

    messages = (
        Message.objects.filter(conversation=conversation)
        .order_by("created_at")
        .select_related("conversation", "conversation__customer")
    )

    bubbles = []
    for msg in messages:
        role = "User" if msg.direction == "inbound" else "AI"
        alignment = "left" if msg.direction == "inbound" else "right"
        color = "#e1ffc7" if msg.direction == "inbound" else "#d9e9ff"
        bubbles.append(
            f"""
            <div class="bubble {alignment}" style="background:{color}">
                <div class="meta">{escape(role)} · {msg.created_at:%Y-%m-%d %H:%M:%S}</div>
                <div class="text">{escape(msg.text or '')}</div>
            </div>
            """
        )

    html = f"""
    <html>
      <head>
        <title>WhatsApp Chat</title>
        <style>
          body {{ font-family: Arial, sans-serif; background: #f5f5f5; }}
          .container {{ max-width: 800px; margin: 20px auto; background: #fff; padding: 16px; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); }}
          .header {{ margin-bottom: 12px; }}
          .bubble {{ max-width: 70%; padding: 10px 12px; margin: 8px 0; border-radius: 12px; position: relative; }}
          .left {{ margin-right: auto; }}
          .right {{ margin-left: auto; }}
          .meta {{ font-size: 12px; color: #555; margin-bottom: 4px; }}
          .text {{ white-space: pre-wrap; font-size: 14px; }}
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h2>WhatsApp Conversation</h2>
            <div>Conversation ID: {conversation.id} · Customer: {conversation.customer_id}</div>
            <div style="font-size:12px;color:#666;">Pass ?conversation_id= to focus on a specific thread.</div>
          </div>
          {''.join(bubbles)}
        </div>
      </body>
    </html>
    """
    return HttpResponse(html)


class ShopifyWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        if not is_ip_allowed(request):
            return Response({"detail": "ip_not_allowed"}, status=status.HTTP_403_FORBIDDEN)
        header_hmac = request.headers.get("X-Shopify-Hmac-Sha256")
        if not validate_hmac(request.body, header_hmac):
            WEBHOOK_REQUESTS.labels(channel=Channel.SHOPIFY, status="unauthorized").inc()
            return Response({"detail": "invalid hmac"}, status=status.HTTP_401_UNAUTHORIZED)

        shopify_upsert(request.data)
        WEBHOOK_REQUESTS.labels(channel=Channel.SHOPIFY, status="accepted").inc()
        return Response({"status": "accepted"}, status=status.HTTP_202_ACCEPTED)


class MagentoWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        if not is_ip_allowed(request):
            return Response({"detail": "ip_not_allowed"}, status=status.HTTP_403_FORBIDDEN)
        shared_secret = os.environ.get("MAGENTO_WEBHOOK_SECRET")
        provided = request.headers.get("X-Magento-Signature")
        if shared_secret and provided != shared_secret:
            WEBHOOK_REQUESTS.labels(channel=Channel.MAGENTO, status="unauthorized").inc()
            return Response({"detail": "invalid signature"}, status=status.HTTP_401_UNAUTHORIZED)
        magento_upsert(request.data)
        WEBHOOK_REQUESTS.labels(channel=Channel.MAGENTO, status="accepted").inc()
        return Response({"status": "accepted"}, status=status.HTTP_202_ACCEPTED)
