import json
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.conf import settings
from django.contrib.auth import get_user_model

from channels_app.models import WebhookEvent
from conversation_app.models import Message
from core.constants import Channel


class WhatsAppWebhookTests(TestCase):
    def setUp(self):
        self.url = reverse("whatsapp-webhook")
        self.user = get_user_model().objects.create_user(username="tester", password="pass1234")

    @patch("channels_app.views.verify_meta_signature", return_value=True)
    def test_webhook_creates_message(self, _sig):
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "contacts": [{"wa_id": "123"}],
                                "messages": [
                                    {"id": "mid-1", "from": "123", "type": "text", "text": {"body": "hi"}}
                                ],
                            }
                        }
                    ]
                }
            ]
        }
        resp = self.client.post(self.url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(resp.status_code, 202)
        self.assertEqual(Message.objects.count(), 1)
        msg = Message.objects.first()
        self.assertEqual(msg.external_message_id, "mid-1")

    @patch("channels_app.views.verify_meta_signature", return_value=True)
    def test_duplicate_message_skipped(self, _sig):
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "contacts": [{"wa_id": "123"}],
                                "messages": [
                                    {"id": "mid-dup", "from": "123", "type": "text", "text": {"body": "hi"}}
                                ],
                            }
                        }
                    ]
                }
            ]
        }
        self.client.post(self.url, data=json.dumps(payload), content_type="application/json")
        resp = self.client.post(self.url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(resp.status_code, 202)
        self.assertEqual(Message.objects.count(), 1)


class OutboundSendTests(TestCase):
    def setUp(self):
        self.url = reverse("whatsapp-send")
        self.user = get_user_model().objects.create_user(username="tester", password="pass1234")

    @patch("channels_app.views.send_whatsapp_text", return_value={"sent": True})
    def test_send_requires_auth_or_api_key(self, _send):
        resp = self.client.post(self.url, {"to": "123", "body": "hello"})
        self.assertEqual(resp.status_code, 403)

        self.client.login(username="tester", password="pass1234")
        resp2 = self.client.post(self.url, {"to": "123", "body": "hello"})
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(Message.objects.filter(direction="outbound").count(), 1)
