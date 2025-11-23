from django.urls import path

from customers_app import views

urlpatterns = [
    path('<int:customer_id>/timeline/', views.CustomerTimelineView.as_view(), name='customer-timeline'),
    path('<int:customer_id>/timeline/export/', views.CustomerTimelineExportView.as_view(), name='customer-timeline-export'),
]
