from django.urls import path

from agents_app import views

urlpatterns = [
    path('', views.AgentProfileListCreateView.as_view(), name='agentprofile-list-create'),
    path('<int:agent_id>/prompts/', views.AgentPromptVersionListCreateView.as_view(), name='agent-prompt-versions'),
    path('<int:agent_id>/prompts/rollback/', views.AgentPromptRollbackView.as_view(), name='agent-prompt-rollback'),
]
