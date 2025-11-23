from rest_framework import generics, permissions
from rest_framework.pagination import PageNumberPagination

from llm_app.serializers import ToolCallLogSerializer
from llm_app.tool_logs import ToolCallLog


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 200


class ToolCallLogListView(generics.ListAPIView):
    serializer_class = ToolCallLogSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        qs = ToolCallLog.objects.all().order_by("-created_at")
        tool = self.request.query_params.get("tool")
        success = self.request.query_params.get("success")
        if tool:
            qs = qs.filter(tool_name=tool)
        if success is not None:
            if success.lower() == "true":
                qs = qs.filter(success=True)
            elif success.lower() == "false":
                qs = qs.filter(success=False)
        return qs
