import time

from django.utils.deprecation import MiddlewareMixin

from core.metrics import WEBHOOK_REQUESTS


class WebhookTimingMiddleware(MiddlewareMixin):
    """Capture webhook timing for Prometheus."""

    def process_view(self, request, view_func, view_args, view_kwargs):
        request._start_time = time.time()

    def process_response(self, request, response):
        if hasattr(request, "path") and "/api/webhooks/" in request.path:
            channel = "unknown"
            if "whatsapp" in request.path:
                channel = "whatsapp"
            elif "shopify" in request.path:
                channel = "shopify"
            elif "magento" in request.path:
                channel = "magento"
            status = response.status_code
            WEBHOOK_REQUESTS.labels(channel=channel, status=str(status)).inc()
        return response
