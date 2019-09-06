# coding: utf-8

from __future__ import absolute_import, unicode_literals

import logging
import time

from celery import shared_task, task

# logger = logging.getLogger(__name__)
from common.textAPI import TextAudit
from manager.models import Behavior, AudioStory


@shared_task
def audioWorker(uuid, type):
    """
    消费者处理任务
    :param uuid:
    :param type:
    :return:
    """
    print("start..........")
    text = TextAudit()
    if type == 1:
        behavior = Behavior.objects.filter(uuid=uuid).first()
        behavior.checkStatus = "check"
        if not text.work_on(behavior.content):
            behavior.checkStatus = "checkFail"
        try:
            behavior.save()
        except Exception as e:
            logging.error(str(e))

    elif type == 2:
        audio = AudioStory.objects.filter(uuid=uuid).first()
        if not text.work_on(audio.name) or not text.work_on(audio.remarks):
            audio.interfaceStatus = "checkFail"
            audio.interfaceInfo = "textCheck"
            try:
                audio.save()
            except Exception as e:
                logging.error(str(e))
    time.sleep(5)
    print("end..........")
    return True
