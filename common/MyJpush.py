
# 极光推送

import jpush

from storybook_sever.config import version

if version == "ali_test":
    # 阿里测试----->  ios release
    app_key = 'b878563acc58979e1bdc1c1f'
    master_secret = '8a68fd8e94cc345f0b680dd1'
else:
    #  235测试------> ios debug
    app_key = '946c0bba0a673da03bb0941f'
    master_secret = '3fa24a0e9f341da0c0c436c7'

_jpush = jpush.JPush(app_key, master_secret)
_jpush.set_logging("DEBUG")
schedule = _jpush.create_schedule()


def time2str(in_date):
    """
    日期转字符串，方便定时推送使用
    :param in_date:
    :return:
    """
    str_time = in_date.strftime('%Y-%m-%d %H:%M:%S')
    return str_time


# 横幅使用 notification 通知 （广播，别名(使用用户uuid））
# APP内使用  message 自定义消息 （别名（使用用户uuid））

# 定时通知 活动邀请
# 非定时 审核通过，关注，点赞

def jpush_notification(title, msg, extras, alias=None):
    """

    :param title:
    :param msg:
    :param extras:
    :param alias:
    :return:
    """
    push = _jpush.create_push()
    if not alias:
        push.audience = jpush.all_
    else:
        push.audience = jpush.alias(*alias)
    push.notification = jpush.notification(alert=msg)
    ios = jpush.ios(alert=msg, sound="default", extras=extras)
    android = jpush.android(alert=msg, title=title, extras=extras)
    push.notification = jpush.notification(alert=msg, android=android, ios=ios)
    if version != "ali_test":
        push.options = {"apns_production":False}
    push.platform = jpush.all_
    response = push.send()
    return response


def jpush_platform_msg(title, content, extras, alias=None):
    """
    自定义消息   app内 非定时
    :param content: 消息内容
    :param title: 消息标题
    :param extras: 附加消息 ，字典格式 {"type":3,"target":"uuid"}
    :return:
    """
    push = _jpush.create_push()
    if not alias:
        push.audience = jpush.all_
    else:
        push.audience = jpush.alias(*alias)
    if version != "ali_test":
        push.options = {"apns_production":False}
    push.platform = jpush.all_
    push.message = jpush.message(content,title=title,content_type="text", extras=extras)
    res = push.send()
    return res


def delete_schedule(schedule_id):
    """
    删除定时推送
    :param schedule_id: string类型 推送唯一标识符
    :return:
    """
    res = schedule.delete_schedule(schedule_id)
    return res


def get_schedule(schedule_id):
    schedule.get_schedule_by_id(schedule_id)


def get_schedule_list(page=1):
    """
    获取定时任务的信息列表
    获取当前有效（endtime 未过期）的 schedule 列表
    每页最多返回 50 个 task，如请求页实际的 task 的个数小于 50，则返回实际数量的 task。
    :return:
    """
    schedule.get_schedule_list(page)


def post_schedule_message(title, content, extras, timestr, name, alias=None):
    """
    定时推送 自定义消息  app内  定时
    :param content: 消息内容本身
    :param title: 消息标题
    :param extras: JSON 格式的可选参数
    :param timestr: 定时推送的时间字符串 ，格式为 2016-07-17 12:00:00
    :param name:  任务的名字
    :return:
    """
    push = _jpush.create_push()
    if not alias:
        push.audience = jpush.all_
    else:
        push.audience = jpush.alias(*alias)
    push.platform = jpush.all_
    push.message = jpush.message(content, title=title, content_type="text", extras=extras)
    if version != "ali_test":
        push.options = {"apns_production":False}
    push=push.payload

    trigger=jpush.schedulepayload.trigger(timestr)   # timestr "2016-07-17 12:00:00"
    schedulepayload=jpush.schedulepayload.schedulepayload(name, True, trigger, push)
    result=schedule.post_schedule(schedulepayload)
    return result


def post_schedule_notification(title, msg, extras, timestr, name, alias=None):
    """
    定时推 通知  --  横幅  定时  活动
    :param msg: 消息内容本身
    :param title: 消息标题
    :param timestr: 定时推送的时间字符串 ，格式为 2016-07-17 12:00:00
    :param name:  任务的名字
    :return:
    """
    push = _jpush.create_push()
    if not alias:
        push.audience = jpush.all_
    else:
        push.audience = jpush.alias(*alias)
    push.platform = jpush.all_
    ios = jpush.ios(alert=msg, sound="default", extras=extras)
    android = jpush.android(alert=msg, title=title, extras=extras)
    push.notification = jpush.notification(alert=msg, android=android, ios=ios)
    if version != "ali_test":
        push.options = {"apns_production":False}
    push=push.payload

    trigger=jpush.schedulepayload.trigger(timestr)   # timestr "2016-07-17 12:00:00"
    schedulepayload=jpush.schedulepayload.schedulepayload(name,True,trigger,push)
    result=schedule.post_schedule(schedulepayload)
    return result


def put_schedule_notification(schedule_id, title, msg, extras, timestr, name):
    """
    修改定时推送 -- 广播
    :param schedule_id:
    :param msg:         推送消息内容
    :param timestr:   时间字符串 2016-07-17 12:00:00
    :param name:      定时推送名
    :return:
    """
    push = _jpush.create_push()
    push.audience = jpush.all_
    # push.notification = jpush.notification(alert=msg)
    ios = jpush.ios(alert=msg, sound="default", extras=extras)
    android = jpush.android(alert=msg, title=title, extras=extras)
    push.notification = jpush.notification(alert=msg, android=android, ios=ios)
    push.platform = jpush.all_
    push = push.payload
    trigger = jpush.schedulepayload.trigger(timestr)
    schedulepayload = jpush.schedulepayload.schedulepayload(name, True, trigger, push)
    res = schedule.put_schedule(schedulepayload, schedule_id)
    return res


def put_schedule_message(schedule_id, title, content, extras, timestr, name):
    """
    修改极光定时推送 -- 广播
    :param schedule_id:
    :param content:  自定义消息内容
    :param title:
    :param extras:
    :param timestr:  定时时间， 格式是时间字符串 2016-07-17 12:00:00
    :param name: 定时推送名
    :return:
    """
    push = _jpush.create_push()
    push.audience = jpush.all_
    push.message = jpush.message(content, title=title, content_type="text", extras=extras)
    push.platform = jpush.all_
    push=push.payload

    trigger = jpush.schedulepayload.trigger(timestr)
    schedulepayload = jpush.schedulepayload.schedulepayload(name, True, trigger, push)
    res = schedule.put_schedule(schedulepayload, schedule_id)
    return res


if __name__ == '__main__':
    extras = {"type": 0, "target": "http://www.baidu.com"}
    # jpush_notification("温馨提示", "中秋快到了, 快来吧！", extras, alias=["2EFDC3A8B982416B9180226552B2F450"])
    jpush_platform_msg("温馨提示", "中秋快到了, 快来吧！", extras, alias=["4F8920204ACB4500822272805CB2F5FC"])
    # put_schedule_message('76ad4986-cfaf-11e9-8106-fa163e93210b', "温馨提示",
    #                      "下午好，中秋快到了", extras, "2019-09-05 15:50:30", "name")
    # res = post_schedule_message("温馨提示", "下午好，中秋快到了", extras, "2019-09-05 15:50:30", "title", ["09AA7CA6B2F34185B6B568720C32FD27"])
    # get_schedule_list()
    # try:
    #     delete_schedule("f9a6680a-cfb5-11e9-b74b-fa163e52e4931")
    # except:
    #     print("aa")
