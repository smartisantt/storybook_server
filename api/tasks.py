# Create your tasks here
from __future__ import absolute_import, unicode_literals

from common.MyJpush import jpush_platform_msg
from storybook_sever.celeryconfig import app

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
        result = text.work_on(behavior.remarks)
        if result == 18:
            textWorker.delay(uuid, 1)
        elif result == 0:
            behavior.checkStatus = "check"

            # 评论通过审核 推送评论信息
            title = "评论提醒"
            content = behavior.userUuid.nickName + "评论了" + behavior.audioUuid.name
            extras = {"type": 3, "unread": 1}
            alias = []
            alias.append(behavior.userUuid.uuid)
            try:
                jpush_platform_msg(title, content, extras, alias)
            except Exception as e:
                logging.error(str(e))
        elif result == 1:
            behavior.checkStatus = "checkFail"
        elif result == 2:
            behavior.checkStatus = "checkAgain"
        try:
            behavior.save()
        except Exception as e:
            logging.error(str(e))

    elif ftype == 2:
        audio = AudioStory.objects.filter(uuid=uuid).first()
        targetStr = "标题："+audio.name+",内容："+audio.remarks
        result = text.work_on(targetStr)
        if result == 18:
            textWorker.delay(uuid, 1)
        elif result == 0:
            audio.interfaceStatus = "check"
            audio.interfaceInfo = "textCheck"
        elif result == 1:
            audio.interfaceStatus = "checkFail"
            audio.interfaceInfo = "textCheck"
        elif result == 2:
            audio.checkStatus = "checkAgain"
            audio.interfaceInfo = "textCheck"
        try:
            audio.save()
        except Exception as e:
            logging.error(str(e))
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
