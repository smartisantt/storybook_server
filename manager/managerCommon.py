#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import re
import uuid
import datetime
import calendar
import json
import logging
import string
import time

import base64


from django.db import connection

from django.http import HttpResponse
from django.db import transaction
from django.core.cache import cache, caches

from storybook_sever.config import *


def random_string(size=6, chars=string.ascii_uppercase + string.digits):
    """
    随机字符串
    :param size:
    :param chars:
    :return:
    """
    return ''.join(random.choice(chars) for _s in xrange(size))


def get_uuid():
    """
    生成数据库uuid
    :return:
    """
    return "".join(str(uuid.uuid4()).split("-")).upper()


# def set_shop_session(request, info):
#     """
#     :param request:
#     :param info: dict={'uuid', 'tel'......}
#     :return:
#     """
#     request.session.set_expiry(SHOP_SESSION_OVER_TIME)
#     uuid = info.get('uuid', '')
#     if not uuid:
#         return False
#     request.session['shopInfo'] = info
#     request.session['uuid'] = uuid
#     return True


def datetime_to_string(mydate, rule='%Y-%m-%d %H:%M:%S'):
    """
    将datetime.datetime转为string
    :param mydate:
    :return:
    """
    if isinstance(mydate, datetime.datetime) or isinstance(mydate, datetime.date):
        return mydate.strftime(rule)
    else:
        return mydate


def string_to_datetime(mystr, rule='%Y-%m-%d %H:%M:%S'):
    """
    将string转为 datetime.datetime
    :param mydate:
    :return:
    """
    if isinstance(mystr, str) or isinstance(mystr, unicode):
        return datetime.datetime.strptime(mystr, rule)
    else:
        return mystr


def unix_time_to_str(unix_time, rule='%Y-%m-%d %H:%M:%S'):
    """
    unix时间转str
    :param unix_time:
    :param rule:
    :return:
    """
    date = unix_time_to_datetime(unix_time)
    return datetime_to_string(date, rule)


def string_to_unix_time(_str, rule='%Y-%m-%d %H:%M:%S'):
    """
    str 转unix时间戳
    :param _str:
    :param rule:
    :return:
    """
    _time = string_to_datetime(_str, rule)
    return time.mktime(_time.timetuple()) * 1000


def unix_time_to_datetime(unix_time):
    """
    unix时间戳转datetime
    :param _str:
    :param rule:
    :return:
    """
    try:
        _time = datetime.datetime.fromtimestamp(unix_time)
    except ValueError:
        try:
            _time = datetime.datetime.fromtimestamp(unix_time / 1000)
        except ValueError:
            _time = unix_time
    return _time


def datetime_to_unix(_time):
    """
    unix时间戳转datetime
    :param _str:
    :param rule:
    :return:
    """
    if isinstance(_time, datetime.datetime):
        return time.mktime(_time.timetuple())
    else:
        return _time




def get_weekday_num(start_time, end_time):
    """
    获取总天数 和 包含的周末数
    :param star_time:
    :param end_time:
    :return:
    """
    if not all([isinstance(start_time, datetime.datetime), isinstance(end_time, datetime.datetime)]):
        return 0
    weekday_num = 0
    days_time = end_time - start_time
    if days_time.seconds:
        days = days_time.days
        if days_time.seconds / (60 * 60) > 12:
            days += 1
    else:
        days = days_time.days
    while start_time <= end_time:
        if start_time.isoweekday() in [6, 7]:
            weekday_num += 1
        start_time = start_time + datetime.timedelta(days=1)
    return days, weekday_num


def get_weekday_list(start_time, end_time):
    """
    获取一段时间内的周末列表
    :param star_time:
    :param end_time:
    :return:
    """
    if not all([isinstance(start_time, datetime.datetime), isinstance(end_time, datetime.datetime)]):
        return []
    week_list = []
    while start_time <= end_time:
        if start_time.isoweekday() in [6, 7]:
            week_list.append(datetime_to_string(start_time, rule='%Y-%m-%d'))
        start_time = start_time + datetime.timedelta(days=1)
    return week_list



def count_prices(_list, price, date_list, _resource, total_devices, total_price):
    """

    :param _list: 时间列表
    :param price: 净价
    :param date_list: 需要计算的全部时间列表
    :param _resource: 资源 obj
    :param total_devices: 设备总数
    :param total_price: 累计总价
    :return: 剩余时间列表， 累计总价
    """

    com_list = list(set(date_list) & set(_list))
    date_list = list(set(date_list) ^ set(com_list))
    h_days = len(com_list)
    total_price += h_days * price * (_resource.holidayNum + 100) / 100 * total_devices
    return date_list, total_price


def first_last_day(now=datetime.datetime.now()):
    """
    获取某天的开始和结束时间
    :param now:
    :return:
    """
    day = now.day
    year = now.year
    month = now.month
    day_begin = '%d-%02d-%02d 00:00:00' % (year, month, day)
    day_end = '%d-%02d-%02d 23:59:59' % (year, month, day)
    day_begin = datetime.datetime.strptime(day_begin, "%Y-%m-%d %H:%M:%S")
    day_end = datetime.datetime.strptime(day_end, "%Y-%m-%d %H:%M:%S")
    return day_begin, day_end


def first_last_day_for_month(myDate=datetime.datetime.now()):
    """
    获取本月第一天与最后一天
    :return:datetime.datetime
    """

    if myDate and not isinstance(myDate, datetime.datetime):
        try:
            dates = myDate.split('-')
            year = int(dates[0])
            month = int(dates[1])
            wday, monthRange = calendar.monthrange(year, month)
            month_begin = '%d-%02d-01 00:00:00' % (year, month)
            month_end = '%d-%02d-%02d 23:59:59' % (year, month, monthRange)
            month_begin = datetime.datetime.strptime(month_begin, "%Y-%m-%d %H:%M:%S")
            month_end = datetime.datetime.strptime(month_end, "%Y-%m-%d %H:%M:%S")
        except Exception as e:
            return myDate, myDate
    else:
        if not myDate or not isinstance(myDate, datetime.datetime):
            myDate = datetime.datetime.now()
        wday, monthRange = calendar.monthrange(myDate.year, myDate.month)
        month_begin = '%d-%02d-01 00:00:00' % (myDate.year, myDate.month)
        month_end = '%d-%02d-%02d 23:59:59' % (myDate.year, myDate.month, monthRange)
        month_begin = datetime.datetime.strptime(month_begin, "%Y-%m-%d %H:%M:%S")
        month_end = datetime.datetime.strptime(month_end, "%Y-%m-%d %H:%M:%S")
    return month_begin, month_end


def page_index(myList, page=1, limit=10):
    """
    分页
    :param page: 页码  第一页为1
    :param limit: 每一页显示条数
    :return: total + list
    """
    page = page if page else 0
    limit = limit if limit else 20

    if not all([isinstance(page, int), isinstance(limit, int)]):
        try:
            page = int(page)
            limit = int(limit)
        except Exception as e:
            logging.error(str(e))
            return myList
    total = len(myList)
    if page == 0:
        startPage = 0
        endPage = limit
    else:
        startPage = (page - 1) * limit
        endPage = page * limit
    if total < startPage:
        return total, []
    if total < endPage:
        endPage = total
    return total, myList[startPage: endPage]


def http_return(code, msg='', info=None):
    """
    返回封装
    :param code: 状态码
    :param msg: 返回消息
    :param info: 返回数据
    :return:
    """
    data = {
        'code': code,
        'msg': msg
    }
    if info is not None:
        data['data'] = info
    return HttpResponse(json.dumps(data), status=code)


def datetime_to_string_object(data):
    """
    将传入的对象的数据库datetime类型转成字符串
    :param data:
    :return:
    """

    if isinstance(data, list):
        for index, _d in enumerate(data):
            if isinstance(_d, datetime.datetime):
                data[index] = datetime_to_string(_d)
            if isinstance(_d, dict):
                for k, v in _d.items():
                    if isinstance(v, datetime.datetime):
                        _d[k] = datetime_to_string(v)
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, datetime.datetime):
                data[k] = datetime_to_string(v)

    return data


# def check_shop(func):
#     """
#     身份认证装饰器
#     :param func:
#     :return:
#     """
#
#     def wrapper(request):
#         token = request.META.get('HTTP_TOKEN')
#         shop_info = cache.get(token)
#         if not shop_info:
#             shop_info = api.check_token(token)
#             if not shop_info:
#                 return http_return(299, '用户信息不存在，请重新登录')
#             else:
#                 shop_data = ShopKeeper.objects.filter(userID=shop_info.get('userId', ''), status='normal').first()
#                 if not shop_data:
#                     shop_uuid = get_uuid()
#                     shop = ShopKeeper(
#                         uuid=shop_uuid,
#                         tel=shop_info.get('phone', ''),
#                         userID=shop_info.get('userId', ''),
#                         name=shop_info.get('wxNickname', ''),
#                         updateTime=datetime.datetime.now()
#                     )
#                     try:
#                         with transaction.atomic():
#                             shop.save()
#                     except Exception as e:
#                         logging.error(str(e))
#                         return http_return(400, '保存失败')
#                     shop_data = ShopKeeper.objects.filter(userID=shop_info.get('userId', ''), status='normal').first()
#                 try:
#                     shop_data.update(loginTime=datetime.datetime.now())
#                 except Exception as e:
#                     logging.error(str(e))
#                 if not create_session(shop_data, token):
#                     return http_return(400, '用户不存在')
#
#         return func(request)
#
#     return wrapper


def check_admin_rule(func):
    """
    权限校验
    :param func:
    :return:
    """

    def wrapper(request):
        if version in ['test', 'debug']:
            pass
        else:
            token = request.META.get('HTTP_TOKEN')
            user_rule = request.path
            user_info = cache.get(token)
            if not user_info:
                return http_return(400, '登录已过期')
            user_uuid = user_info.get('uuid')
            if cache.get(user_uuid):
                return http_return(299, '您的权限发生改变，请重新登录')
            rule_list = user_info.get('user_rule', [])
            if user_rule not in rule_list:
                return http_return(400, '用户无此权限')
            cache.set(token, user_info, USER_CACHE_OVER_TIME)
        return func(request)

    return wrapper


def create_session(user_info, token):
    """
    用户信息保存至cache
    :param request:
    :param user_info:
    :return:
    """
    shop_keeper = {
        'name': user_info.name,
        'uuid': user_info.uuid,
        'userID': user_info.userID,
        'tel': user_info.tel,
    }
    try:
        cache.set(token, shop_keeper, USER_SESSION_OVER_TIME)
    except Exception as e:
        logging.error(str(e))
        return False
    return True


def create_cache(user_info, loginIp, token):
    """
    用户信息保存至cache
    :param request:
    :param user_info:
    :return:
    """
    user_data = {
        'name': user_info.username,
        'uuid': user_info.uuid,
        'userID': user_info.userID,
        'logo': user_info.userLogo,
        'tel': user_info.tel,
        'role': user_info.roles,
        'status': user_info.status,
        'loginIp': loginIp
    }
    # request.session.set_expiry(SHOP_SESSION_OVER_TIME)
    # request.session[token] = shop_keeper
    # request.session['uuid'] = user_info.uuid
    try:
        caches['default'].set(token, user_data, USER_CACHE_OVER_TIME)
    except Exception as e:
        logging.error(str(e))
        return False
    return True


def request_body(request):
    """
    转换request.body
    :param request:
    :return:
    """
    if not request:
        return request
    try:
        token = request.META.get('HTTP_TOKEN')
        if not token:
            return http_return(400, '非法请求')
        data = {
            '_cache': cache.get(token)
        }
        if request.method == 'POST':
            if request.body:
                try:
                    for key, value in json.loads(request.body).items():
                        data[key] = value
                except Exception as e:
                    logging.error(str(e))
                    pass
            if request.POST:
                for key, value in request.POST.items():
                    data[key] = value
        elif request.method == 'GET':
            for key, value in request.GET.items():
                data[key] = value
        else:
            pass

    except Exception as e:
        logging.error(str(e))
        return False
    return data


def request_body_not_token(request):
    """
    转换request.body
    :param request:
    :return:
    """
    if not request:
        return request
    try:
        token = request.META.get('HTTP_TOKEN')

        data = {
            '_cache': cache.get(token)
        }
        if request.method == 'POST':
            if request.body:
                try:
                    for key, value in json.loads(request.body).items():
                        data[key] = value
                except Exception as e:
                    logging.error(str(e))
                    pass
            if request.POST:
                for key, value in request.POST.items():
                    data[key] = value
        elif request.method == 'GET':
            for key, value in request.GET.items():
                data[key] = value
        else:
            pass

    except Exception as e:
        logging.error(str(e))
        return False
    return data



def match_tel(tel):
    """
    正则校验手机号
    :param tel:
    :return:
    """
    if re.match(r'1[3,4,5,7,8,9]\d{9}', tel):
        return True
    return False


def get_ip_address(request):
    """获取请求的IP地址"""
    ip = request.META.get('HTTP_X_FORWARDED_FOR', None)
    return ip or request.META['REMOTE_ADDR']

if __name__ == '__main__':
    print(match_tel('13811111111'))