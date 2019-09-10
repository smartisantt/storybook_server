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
    targetDict = {
        1: "暴恐违禁",
        2: "文本色情",
        3: "政治敏感",
        4: "恶意推广",
        5: "低俗辱骂",
        6: "低质灌水",
    }
    if ftype == 1:
        behavior = Behavior.objects.filter(uuid=uuid).first()
        checkResult, checkInfo, = text.work_on(behavior.remarks)
        if checkResult or checkInfo:
            if checkResult == 18:
                textWorker.delay(uuid, 1)
                return True
            if checkResult in [0, 1, 2]:
                checkList = []
                for info in checkInfo:
                    checkList.append(targetDict[info["label"]])
                if checkResult == 0:
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
                checkDict = {
                    0: "check",
                    1: "checkFail",
                    2: "checkAgain"
                }
                behavior.checkStatus = checkDict[checkResult]
                behavior.checkInfo = ",".join(checkList)
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
                return True
            if checkResult in [0, 1, 2]:
                interfaceDict = {
                    1: "check",
                    2: "checkFail",
                    3: "checkFail",
                }
                checkList = []
                for info in checkInfo:
                    checkList.append(targetDict[info["label"]])
                audio.interfaceStatus = interfaceDict[checkResult]
                audio.interfaceInfo = ",".join(checkList)
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
