import csv
from django.http import HttpResponse
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from customers_app.models import Customer
from customers_app.serializers import CustomerSerializer, TimelineEventSerializer
from commerce_app.models import Order, Ticket
from conversation_app.models import Conversation


class CustomerTimelineView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, customer_id):
        customer = Customer.objects.filter(id=customer_id).first()
        if not customer:
            return Response({"detail": "not found"}, status=404)

        events = []
        for convo in Conversation.objects.filter(customer=customer).order_by("-created_at"):
            events.append(
                {"type": "conversation", "id": convo.id, "created_at": convo.created_at, "payload": {"status": convo.status}}
            )
        for order in Order.objects.filter(customer=customer).order_by("-created_at"):
            events.append(
                {
                    "type": "order",
                    "id": order.id,
                    "created_at": order.created_at,
                    "payload": {
                        "external_order_id": order.external_order_id,
                        "status": order.status,
                        "total": float(order.total),
                        "currency": order.currency,
                    },
                }
            )
        for ticket in Ticket.objects.filter(customer=customer).order_by("-created_at"):
            events.append(
                {"type": "ticket", "id": ticket.id, "created_at": ticket.created_at, "payload": {"status": ticket.status, "summary": ticket.summary}}
            )
        events = sorted(events, key=lambda e: e["created_at"], reverse=True)
        serializer = TimelineEventSerializer(events, many=True)
        return Response({"customer": CustomerSerializer(customer).data, "events": serializer.data})


class CustomerTimelineExportView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, customer_id):
        customer = Customer.objects.filter(id=customer_id).first()
        if not customer:
            return Response({"detail": "not found"}, status=404)
        # reuse timeline assembly
        events_resp = CustomerTimelineView().get(request, customer_id)
        if events_resp.status_code != 200:
            return events_resp
        events = events_resp.data["events"]
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="customer_{customer_id}_timeline.csv"'
        writer = csv.writer(response)
        writer.writerow(["type", "id", "created_at", "payload"])
        for ev in events:
            writer.writerow([ev["type"], ev["id"], ev["created_at"], ev["payload"]])
        return response
