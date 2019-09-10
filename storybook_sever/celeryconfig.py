from __future__ import absolute_import, unicode_literals

import os
from celery import Celery

# set the default Django settings module for the 'celery' program.
from storybook_sever.config import version

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'storybook_sever.settings')

app = Celery('storybook_sever')
app.conf.broker_url = 'redis://127.0.0.1:6379/2'
app.conf.result_backend = 'redis://127.0.0.1:6379/3'
if version == "ali_test":
    app.conf.broker_url = 'redis://172.18.0.5:6379/2'
    app.conf.result_backend = 'redis://172.18.0.5:6379/3'



# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    pass
    # print('Request: {0!r}'.format(self.request))
