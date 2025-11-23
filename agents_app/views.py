from rest_framework import generics, permissions

from agents_app.models import AgentProfile
from agents_app.models_prompt import AgentPromptVersion
from agents_app.serializers import AgentProfileSerializer, AgentPromptVersionSerializer
from analytics_app.models import AuditLog
from core.utils import mask_payload


class AgentProfileListCreateView(generics.ListCreateAPIView):
    queryset = AgentProfile.objects.all().order_by("-created_at")
    serializer_class = AgentProfileSerializer
    permission_classes = [permissions.IsAdminUser]


class AgentPromptVersionListCreateView(generics.ListCreateAPIView):
    serializer_class = AgentPromptVersionSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        agent_id = self.kwargs.get("agent_id")
        return AgentPromptVersion.objects.filter(agent_id=agent_id).order_by("-version")

    def perform_create(self, serializer):
        agent_id = self.kwargs.get("agent_id")
        latest = AgentPromptVersion.objects.filter(agent_id=agent_id).order_by("-version").first()
        next_version = (latest.version + 1) if latest else 1
        instance = serializer.save(agent_id=agent_id, version=next_version)
        AuditLog.objects.create(
            event_type="agent_prompt_version_created",
            actor=str(self.request.user),
            target=str(agent_id),
            payload=mask_payload({"version": next_version}),
        )
        return instance


class AgentPromptRollbackView(generics.GenericAPIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, *args, **kwargs):
        agent_id = kwargs.get("agent_id")
        version = request.data.get("version")
        if not version:
            return Response({"detail": "version required"}, status=400)
        try:
            pv = AgentPromptVersion.objects.get(agent_id=agent_id, version=version)
        except AgentPromptVersion.DoesNotExist:
            return Response({"detail": "version not found"}, status=404)
        AgentProfile.objects.filter(id=agent_id).update(system_prompt=pv.system_prompt)
        AuditLog.objects.create(
            event_type="agent_prompt_rollback",
            actor=str(request.user),
            target=str(agent_id),
            payload=mask_payload({"version": version}),
        )
        return Response({"status": "rolled_back", "version": version})
