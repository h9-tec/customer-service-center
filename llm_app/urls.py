from django.urls import path

from llm_app import views

urlpatterns = [
    path('tool-calls/', views.ToolCallLogListView.as_view(), name='toolcalllog-list'),
]
