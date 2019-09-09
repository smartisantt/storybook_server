# from celery import task
# from time import sleep
#
# import logging
#
# from common.textAPI import TextAudit
# from manager.models import Behavior, AudioStory
#
#
# @task()
# def textWorker(uuid, type):
#     """
#     消费者处理任务
#     :param uuid:
#     :param type:
#     :return:
#     """
#     print("start..........")
#     text = TextAudit()
#     if type == 1:
#         behavior = Behavior.objects.filter(uuid=uuid).first()
#         behavior.checkStatus = "check"
#         if not text.work_on(behavior.content):
#             behavior.checkStatus = "checkFail"
#         try:
#             behavior.save()
#         except Exception as e:
#             logging.error(str(e))
#
#     elif type == 2:
#         audio = AudioStory.objects.filter(uuid=uuid).first()
#         if not text.work_on(audio.name) or not text.work_on(audio.remarks):
#             audio.interfaceStatus = "checkFail"
#             audio.interfaceInfo = "textCheck"
#             try:
#                 audio.save()
#             except Exception as e:
#                 logging.error(str(e))
#     sleep(5)
#     print("end..........")
#     return True
#
#
# def get_task_status(task_id):
#     task = textWorker.AsyncResult(task_id)
#
#     status = task.state
#     progress = 0
#
#     if status == u'SUCCESS':
#         progress = 100
#     elif status == u'FAILURE':
#         progress = 0
#     elif status == 'PROGRESS':
#         progress = task.info['progress']
#
#     return {'status': status, 'progress': progress}
