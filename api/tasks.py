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
    text = TextAudit()
    if ftype == 1:
        behavior = Behavior.objects.filter(uuid=uuid).first()
        checkResult, checkInfo, = text.work_on(behavior.remarks)
        if checkResult or checkInfo:
            if checkResult == 18:
                textWorker.delay(uuid, 1)
            if checkResult in [0, 1, 2]:
                if checkResult == 0:
                    checkInfo = "评论通过审核"
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
                if checkResult == 0:
                    checkInfo = "建议人工复审"
                checkDict = {
                    0: "check",
                    1: "checkFail",
                    2: "checkAgain"
                }
                behavior.checkStatus = checkDict[checkResult]
                behavior.checkInfo = checkInfo
                try:
                    behavior.save()
                except Exception as e:
                    logging.error(str(e))

    elif ftype == 2:
        audio = AudioStory.objects.filter(uuid=uuid).first()
        targetStr = "标题：" + audio.name + ",内容：" + audio.remarks
        checkResult, checkInfo = text.work_on(targetStr)
        if checkResult or checkInfo:
            if checkResult == 18:
                textWorker.delay(uuid, 1)
            if checkResult in [0, 1, 2]:
                interfaceDict = {
                    1: "check",
                    2: "checkFail",
                    3: "checkFail",
                }
                audio.interfaceStatus = interfaceDict[checkResult]
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
