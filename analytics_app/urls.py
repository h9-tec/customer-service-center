from django.urls import path

from analytics_app import views

urlpatterns = [
    path('kpi/daily/', views.DailyKPIListView.as_view(), name='daily-kpi-list'),
    path('audit/', views.AuditLogListView.as_view(), name='audit-log-list'),
    path('audit/export/', views.AuditLogExportView.as_view(), name='audit-log-export'),
]
