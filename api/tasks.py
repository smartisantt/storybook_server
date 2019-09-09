# Create your tasks here
from __future__ import absolute_import, unicode_literals
from storybook_sever.celery import app
from time import sleep

import logging

from common.textAPI import TextAudit
from manager.models import Behavior, AudioStory


@app.task
def textWorker(uuid, ftype):
    """
    消费者处理任务
    :param uuid:
    :param type:
    :return:
    """
    # print("start..........")
    text = TextAudit()
    if ftype == 1:
        behavior = Behavior.objects.filter(uuid=uuid).first()
        behavior.checkStatus = "check"
        if not text.work_on(behavior.remarks):
            behavior.checkStatus = "checkFail"
        try:
            behavior.save()
        except Exception as e:
            logging.error(str(e))

    elif ftype == 2:
        audio = AudioStory.objects.filter(uuid=uuid).first()
        if not text.work_on(audio.name) or not text.work_on(audio.remarks):
            audio.interfaceStatus = "checkFail"
            audio.interfaceInfo = "textCheck"
            try:
                audio.save()
            except Exception as e:
                logging.error(str(e))
    sleep(0.2)
    # print("end..........")
    return True


def get_task_status(task_id):
    task = textWorker.AsyncResult(task_id)

    status = task.state
    progress = 0

    if status == u'SUCCESS':
        progress = 100
    elif status == u'FAILURE':
        progress = 0
    elif status == 'PROGRESS':
        progress = task.info['progress']

    return {'status': status, 'progress': progress}
