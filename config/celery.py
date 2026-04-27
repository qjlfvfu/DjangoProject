from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Устанавливаем настройки Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")

# Используем строку, а не объект settings
app.config_from_object("django.conf:settings", namespace="CELERY")

# Автоматически находим задачи
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
