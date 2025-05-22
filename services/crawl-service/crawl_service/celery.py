# myproject/celery.py
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crawl_service.settings")

app = Celery("CrawlService")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()
