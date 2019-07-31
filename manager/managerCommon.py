#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import re
import uuid
import datetime
import json
import logging
import string
import time

from django.core.paginator import Paginator
from django.http import HttpResponse
from django.core.cache import cache, caches
from django.utils import timezone

from manager.models import User, LoginLog
from common.api import Api
from storybook_sever.config import *
from utils.errors import ParamsException



def get_uuid():
    """
    生成数据库uuid
    :return:
    """
    return "".join(str(uuid.uuid4()).split("-")).upper()



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



def unix_time_to_str(unix_time, rule='%Y-%m-%d %H:%M:%S'):
    """
    unix时间转str
    :param unix_time:
    :param rule:
    :return:
    """
    date = unix_time_to_datetime(unix_time)
    return datetime_to_string(date, rule)



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


def timestamp2datetime(startTimestamp, endTimestamp, convert=True):
    """
    毫秒级时间戳转为datetime格式
    :param startTimestamp: 开始时间戳
    :param endTimestamp: 结束时间戳
    :param convert: 是否处理时间的时分秒，默认转换
    :return: 返回的datetime元祖
    """
    if not all([startTimestamp, endTimestamp]):
        raise ParamsException('时间不能为空')

    # 如果是字符串
    if isinstance(startTimestamp, str):
        if startTimestamp.isdigit():
            try:
                startTimestamp = int(startTimestamp)
            except Exception as e:
                logging.error(str(e))
                raise ParamsException('开始时间格式错误')
        else:
            raise ParamsException('开始时间格式错误')
    if isinstance(endTimestamp, str):
        if endTimestamp.isdigit():
            try:
                endTimestamp = int(endTimestamp)
            except Exception as e:
                logging.error(str(e))
                raise ParamsException('结束时间格式错误')
        else:
            raise ParamsException('结束时间格式错误')

    if not all([isinstance(startTimestamp, int), isinstance(endTimestamp, int)]):
        raise ParamsException('时间格式错误')

    if endTimestamp < startTimestamp:
        raise ParamsException('结束时间小于开始时间')

    startTimestamp = startTimestamp / 1000
    endTimestamp = endTimestamp / 1000


    try:
        startTime = datetime.datetime.fromtimestamp(startTimestamp)
        endTime = datetime.datetime.fromtimestamp(endTimestamp)
        # startTime = timezone.make_aware(startTime, timezone.get_current_timezone())
        # endTime = timezone.make_aware(endTime, timezone.get_current_timezone())
    except Exception as e:
        logging.error(str(e))
        raise ParamsException('时间格式错误')
    if convert:
        startTime = datetime.datetime(startTime.year, startTime.month, startTime.day)
        endTime = datetime.datetime(endTime.year, endTime.month, endTime.day, 23, 59, 59, 999999)
    return startTime, endTime

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



def create_cache(user_info, token):
    """
    用户信息保存至cache
    :param request:
    :param user_info:
    :return:
    """
    user_data = {
        'nickName': user_info.nickName,
        'uuid': user_info.uuid,
        'userID': user_info.userID,
        'avatar': user_info.avatar,
        'tel': user_info.tel,
        'role': user_info.roles,
        'status': user_info.status,
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


# def request_body(request):
#     """
#     转换request.body
#     :param request:
#     :return:
#     """
#     if not request:
#         return request
#     try:
#         token = request.META.get('HTTP_TOKEN')
#         if not token:
#             return http_return(400, '非法请求')
#         data = {
#             '_cache': cache.get(token)
#         }
#         if request.method == 'POST':
#             if request.body:
#                 try:
#                     for key, value in json.loads(request.body).items():
#                         data[key] = value
#                 except Exception as e:
#                     logging.error(str(e))
#                     pass
#             if request.POST:
#                 for key, value in request.POST.items():
#                     data[key] = value
#         elif request.method == 'GET':
#             for key, value in request.GET.items():
#                 data[key] = value
#         else:
#             pass
#
#     except Exception as e:
#         logging.error(str(e))
#         return False
#     return data


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
    if re.match("^1[3456789]\d{9}$", tel):
        return True
    return False


def get_ip_address(request):
    """获取请求的IP地址"""
    # HTTP_X_FORWARDED_FOR也就是HTTP的请求端真实的IP，
    # 只有在通过了HTTP 代理或者负载均衡服务器时才会添加该项。
    ip = request.META.get('HTTP_X_FORWARDED_FOR', None)
    return ip or request.META['REMOTE_ADDR']


def request_body(request, method='GET'):
    """
    转换request.body
    :param request:
    :return:
    """
    if not request:
        return request
    if request.method != method:
        return False
    try:
        token = request.META.get('HTTP_TOKEN')
        if not token:
            return False
        data = {
            '_cache': caches['default'].get(token)
        }
        if request.method == 'POST':
            if request.body:
                try:
                    for key, value in json.loads(request.body.decode('utf-8')).items():
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



def check_identify(func):
    """身份认证装饰器"""
    def wrapper(request):
        token = request.META.get('HTTP_TOKEN')
        if not token:
            return http_return(400, '提供有效的身份认证标识')
        try:
            user_info = caches['default'].get(token)
        except Exception as e:
            logging.error(str(e))
            return http_return(400, '连接redis失败')
        if not user_info:
            api = Api()
            user_info = api.check_token(token)
            if not user_info:
                return http_return(403, '禁止登录')

            # 记录登录ip,存入缓存
            user = User.objects.filter(userID=user_info.get('userId', ''), roles='adminUser'). \
                exclude(status="destroy").only('userID').first()
            if not user:
                return http_return(403, '没有管理员权限')

            loginIp = get_ip_address(request)

            if not create_session(user, token, loginIp):
                return http_return(400, '写缓存失败')
            # 如果有登陆出现，则存登录日志
            try:
                LoginLog.objects.create(
                    uuid=get_uuid(),
                    ipAddr=user_info.get('loginIp', ''),
                    userUuid=user,
                    userAgent=request.META.get('HTTP_USER_AGENT', ''),
                    isManager=True
                )
            except Exception as e:
                logging.error(str(e))
                return http_return(400, '日志保存失败')
        return func(request)

    return wrapper



# def request_body(request, method='GET'):
#     """
#     转换request.body
#     :param request:
#     :return:
#     """
#     if not request:
#         return request
#     if request.method != method:
#         return False
#     try:
#         token = request.META.get('HTTP_TOKEN')
#         if not token:
#             return False
#         data = {
#             '_cache': caches['default'].get(token)
#         }
#         if request.method == 'POST':
#             if request.body:
#                 try:
#                     for key, value in json.loads(request.body.decode('utf-8')).items():
#                         data[key] = value
#                 except Exception as e:
#                     logging.error(str(e))
#                     pass
#             if request.POST:
#                 for key, value in request.POST.items():
#                     data[key] = value
#         elif request.method == 'GET':
#             for key, value in request.GET.items():
#                 data[key] = value
#         else:
#             pass
#
#     except Exception as e:
#         logging.error(str(e))
#         return False
#     return data


def create_session(user, token, loginIP):
    """用户信息保存至caches"""
    user = {
        'nickName': user.nickName or '',
        'uuid': user.uuid,
        'userId': user.userID,
        'tel': user.tel,
        'loginIp': loginIP
    }
    try:
        caches['default'].set(token, user, timeout=USER_CACHE_OVER_TIME)
    except Exception as e:
        logging.error(str(e))
        return False
    return True




if __name__ == '__main__':
    print(match_tel('13811111111'))