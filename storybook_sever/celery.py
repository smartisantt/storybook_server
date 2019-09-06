from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.utils import timezone

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'storybook_sever.settings')

app = Celery('storybook_sever')

app.config_from_object('django.conf:settings')
app.now = timezone.now

# Load task modules from all registered Django app configs.

app.autodiscover_tasks()