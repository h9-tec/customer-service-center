import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

celery_app = Celery("core")
celery_app.config_from_object("django.conf:settings", namespace="CELERY")
celery_app.autodiscover_tasks()

# Celery beat schedule for daily KPIs at 01:00
celery_app.conf.beat_schedule = {
    "compute-daily-kpis": {
        "task": "analytics_app.tasks.compute_daily_kpis",
        "schedule": 60 * 60 * 24,  # daily
        "options": {"expires": 60 * 60 * 2},
    },
}
