from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def healthcheck(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', healthcheck, name='healthcheck'),
    path('api/health/', healthcheck, name='api-healthcheck'),
    path('api/webhooks/', include('channels_app.urls')),
    path('api/messages/', include('conversation_app.urls')),
    path('api/agents/', include('agents_app.urls')),
    path('api/llm/', include('llm_app.urls')),
    path('api/analytics/', include('analytics_app.urls')),
    path('api/customers/', include('customers_app.urls')),
]
