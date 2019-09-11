# Create your tasks here
from __future__ import absolute_import, unicode_literals

from common.MyJpush import jpush_platform_msg
from common.exceptions import QPSError
from storybook_sever.celeryconfig import app

import logging

from common.textAPI import TextAudit
from manager.models import Behavior, AudioStory


@app.task(autoretry_for=(QPSError,), retry_kwargs={'max_retries': 5})
def textWorker(uuid):
    """
    消费者处理任务
    :param uuid:
    :return:
    """
    text = TextAudit()
    behavior = Behavior.objects.filter(uuid=uuid).first()
    if behavior:
        checkResult, checkInfo, = text.work_on(behavior.remarks)
        if checkResult:
            if checkResult == 18:
                raise QPSError
            if checkResult in ["check", "checkFail", "checkAgain"]:
                if checkResult == "checkAgain":
                    checkInfo = "建议人工复审"
                if checkResult == "check":
                    checkInfo = "评论通过审核"
                behavior.checkStatus = checkResult
                behavior.checkInfo = checkInfo
                try:
                    behavior.save()
                except Exception as e:
                    logging.error(str(e))
                if checkResult == "check":
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
        return True

    audio = AudioStory.objects.filter(uuid=uuid)
    if audio:
        targetStr = "标题：" + audio.name + ",内容：" + audio.remarks
        checkResult, checkInfo = text.work_on(targetStr)
        if checkResult:
            if checkResult == 18:
                raise QPSError
            interfaceData = {}
            if checkResult in ["checkAgain", "checkFail"]:
                interfaceData["interfaceStatus"] = "checkFail"
            interfaceData["interfaceInfo"] = "textCheck"
            try:
                audio.update(**interfaceData)
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
