from django.urls import path

from conversation_app import views

urlpatterns = [
    path('normalized/', views.NormalizedMessageView.as_view(), name='normalized-message'),
    path('conversations/', views.ConversationListView.as_view(), name='conversation-list'),
    path('conversations/<int:conversation_id>/messages/', views.MessageListView.as_view(), name='conversation-messages'),
]
