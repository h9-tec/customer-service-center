from rest_framework import generics, permissions
from rest_framework.pagination import PageNumberPagination

from analytics_app.models import DailyKPI, AuditLog
from analytics_app.serializers import DailyKPISerializer, AuditLogSerializer
from django.http import HttpResponse
import csv


class KPIPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200


class DailyKPIListView(generics.ListAPIView):
    serializer_class = DailyKPISerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = KPIPagination

    def get_queryset(self):
        qs = DailyKPI.objects.all().order_by("-date")
        channel = self.request.query_params.get("channel")
        agent_id = self.request.query_params.get("agent_id")
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        if channel:
            qs = qs.filter(channel=channel)
        if agent_id:
            qs = qs.filter(agent_id=agent_id)
        if start_date:
            qs = qs.filter(date__gte=start_date)
        if end_date:
            qs = qs.filter(date__lte=end_date)
        return qs


class AuditLogListView(generics.ListAPIView):
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = KPIPagination

    def get_queryset(self):
        qs = AuditLog.objects.all().order_by("-created_at")
        event_type = self.request.query_params.get("event_type")
        if event_type:
            qs = qs.filter(event_type=event_type)
        return qs


class AuditLogExportView(generics.GenericAPIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, *args, **kwargs):
        qs = AuditLog.objects.all().order_by("-created_at")
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="audit_logs.csv"'
        writer = csv.writer(response)
        writer.writerow(["created_at", "event_type", "actor", "target", "payload"])
        for log in qs:
            writer.writerow([log.created_at, log.event_type, log.actor, log.target, log.payload])
        return response
