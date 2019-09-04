
# 极光推送
import jpush
from datetime import datetime
from jpush import common

from storybook_sever.config import version

if version == "ali_test":
    app_key = 'b878563acc58979e1bdc1c1f'
    master_secret = '8a68fd8e94cc345f0b680dd1'
else:
    app_key = '946c0bba0a673da03bb0941f'
    master_secret = '3fa24a0e9f341da0c0c436c7'

_jpush = jpush.JPush(app_key, master_secret)
_jpush.set_logging("DEBUG")
schedule = _jpush.create_schedule()


def time2str(in_data):
    str_time = in_data.strftime('%Y-%m-%d %H:%M:%S')
    return str_time


def all(msg):
    """
    广播消息
    :param msg: 消息内容
    :return:
    """
    push = _jpush.create_push()
    push.audience = jpush.all_
    push.notification = jpush.notification(alert=msg)
    push.platform = jpush.all_
    try:
        response=push.send()
    except common.Unauthorized:
        raise common.Unauthorized("Unauthorized")
    except common.APIConnectionException:
        raise common.APIConnectionException("conn")
    except common.JPushFailure:
        print ("JPushFailure")
    except:
        print ("Exception")


def test_tag(msg):
    """
    广播消息
    :param msg: 消息内容
    :return:
    """
    tags = ['test']
    push = _jpush.create_push()
    push.audience = jpush.tag(*tags)
    push.notification = jpush.notification(alert=msg)
    push.platform = jpush.all_
    try:
        response=push.send()
    except common.Unauthorized:
        raise common.Unauthorized("Unauthorized")
    except common.APIConnectionException:
        raise common.APIConnectionException("conn")
    except common.JPushFailure:
        print ("JPushFailure")
    except:
        print ("Exception")


def test_alias(msg, alias):
    """
    :param msg: 消息内容
    :return:
    """
    push = _jpush.create_push()
    push.audience = jpush.alias(*alias)
    push.notification = jpush.notification(alert=msg)
    push.platform = jpush.all_
    try:
        response=push.send()
    except common.Unauthorized:
        raise common.Unauthorized("Unauthorized")
    except common.APIConnectionException:
        raise common.APIConnectionException("conn")
    except common.JPushFailure:
        print ("JPushFailure")
    except:
        print ("Exception")


def platfrom_msg(content, title, extras):
    """
    自定义消息
    :param content: 消息内容
    :param title: 消息标题
    :param extras: 附加消息 ，字典格式 {"title":"自定义标题","url":"http://www.baidu.com"}
    :return:
    """
    push = _jpush.create_push()
    push.audience = jpush.all_
    push.platform = jpush.all_
    push.message=jpush.message(content,title=title,content_type="text", extras=extras)
    push.send()


def platfrom_msg_alias(alias, content, title, extras):
    """
    自定义消息
    :param content: 消息内容
    :param alias: 消息听众
    :param title: 消息标题
    :param extras: 附加消息 ，字典格式 {"title":"自定义标题","url":"http://www.baidu.com"}
    :return:
    """
    push = _jpush.create_push()
    # push.audience = jpush.all_
    push.audience = jpush.alias(*alias)
    push.platform = jpush.all_
    # ios_msg = jpush.ios(alert="Hello, IOS JPush!", badge="+1", sound="a.caf", extras={'k1':'v1'})
    # android_msg = jpush.android(alert="Hello, android msg")
    # push.notification = jpush.notification(alert="Hello, JPush!", android=android_msg, ios=ios_msg)
    # push.notification = jpush.notification(alert="温馨提示：Hello, JPush!")
    push.message=jpush.message(content,title=title,content_type="text", extras=extras)
    res = push.send()
    return res


def delete_schedule(schedule_id):
    """
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


def post_schedule_message(content, title, extras, timestr, name):
    """
    定时推送 自定义消息
    :param content: 消息内容本身
    :param title: 消息标题
    :param extras: JSON 格式的可选参数
    :param timestr: 定时推送的时间字符串 ，格式为 2016-07-17 12:00:00
    :param name:  任务的名字
    :return:
    """
    push = _jpush.create_push()
    push.audience = jpush.all_
    push.platform = jpush.all_
    push.message = jpush.message(content,title=title,content_type="text", extras=extras)
    push=push.payload

    trigger=jpush.schedulepayload.trigger(timestr)   # timestr "2016-07-17 12:00:00"
    schedulepayload=jpush.schedulepayload.schedulepayload(name, True, trigger, push)
    result=schedule.post_schedule(schedulepayload)
    return result


def post_schedule_notification(msg, timestr, name):
    """
    定时推 通知
    :param msg: 消息内容本身
    :param title: 消息标题
    :param timestr: 定时推送的时间字符串 ，格式为 2016-07-17 12:00:00
    :param name:  任务的名字
    :return:
    """
    push = _jpush.create_push()
    push.audience = jpush.all_
    push.platform = jpush.all_
    push.notification = jpush.notification(alert=msg)
    push=push.payload

    trigger=jpush.schedulepayload.trigger(timestr)   # timestr "2016-07-17 12:00:00"
    schedulepayload=jpush.schedulepayload.schedulepayload(name,True,trigger,push)
    result=schedule.post_schedule(schedulepayload)
    # print (result.status_code)
    return result


def put_schedule_notification(schedule_id, msg, timestr, name):
    """
    修改定时推送
    :param schedule_id:
    :param msg:         推送消息内容
    :param timestr:   时间字符串 2016-07-17 12:00:00
    :param name:      定时推送名
    :return:
    """
    push = _jpush.create_push()
    push.audience = jpush.all_
    push.notification = jpush.notification(alert=msg)
    push.platform = jpush.all_
    push=push.payload

    trigger=jpush.schedulepayload.trigger(timestr)
    schedulepayload=jpush.schedulepayload.schedulepayload(name, True, trigger, push)
    res = schedule.put_schedule(schedulepayload, schedule_id)
    return res


def put_schedule_message(schedule_id, content, title, extras, timestr, name):
    """
    修改极光定时推送
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
    # push.notification = jpush.notification(alert=msg)
    push.message = jpush.message(content, title=title, content_type="text", extras=extras)
    push.platform = jpush.all_
    push=push.payload

    trigger=jpush.schedulepayload.trigger(timestr)
    schedulepayload=jpush.schedulepayload.schedulepayload(name, True, trigger, push)
    res = schedule.put_schedule(schedulepayload, schedule_id)
    return res


if __name__ == '__main__':
    # post_schedule("定时推送：中午好！", "2019-09-03 11:40:00")
    # get_schedule_list()
    # get_schedule("7b44ac6c-cdf1-11e9-970f-fa163e74a8d9")
    # delete_schedule("7b44ac6c-cdf1-11e9-970f-fa163e74a8d9")
    # platfrom_msg()
    # all("test")
    # test_alias("温馨提示：天冷加衣！注意保暖！", ["4F8920204ACB4500822272805CB2F5FC"])
    # post_schedule_message(content="温馨提示：天冷加衣！", title="我是标题",
    #                       extras={"title":"自定义标题","url":"http://www.baidu.com"},
    #                       timestr="2019-09-03 15:17:00", name="定时发送")
    # print(time2str(datetime.now()))
    # print(type(time2str(datetime.now())))
    platfrom_msg_alias(["4F8920204ACB4500822272805CB2F5FC"], "温馨提示", "这是标题", {"type":1, "target": "1234"})