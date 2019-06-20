#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import logging
import random
import re
import string

from django.core.cache import cache
from django.db import transaction
from pip._vendor.msgpack.fallback import xrange

from common.common import http_return, get_uuid
from manager.models import *
from storybook_sever import api
from storybook_sever.config import USER_SESSION_OVER_TIME


def match_tel(tel):
    """
    正则校验手机号
    :param tel:
    :return:
    """
    if re.match(r'1[3,4,5,7,8,9]\d{9}', tel):
        return True
    return False


def random_string(size=6, chars=string.ascii_uppercase + string.digits):
    """
    随机字符串
    :param size:
    :param chars:
    :return:
    """
    return ''.join(random.choice(chars) for _s in xrange(size))


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


def check_identify(func):
    """
    身份认证装饰器
    :param func:
    :return:
    """

    def wrapper(request):
        token = request.META.get('HTTP_TOKEN')
        user_info = cache.get(token)
        if not user_info:
            user_info = api.check_token(token)
            if not user_info:
                return http_return(400, '未获取到用户信息')
            else:
                user_data = User.objects.filter(userID=user_info.get('userId', ''), status='normal').first()
                if not user_data:
                    user_uuid = get_uuid()
                    user = User(
                        uuid=user_uuid,
                        tel=user_info.get('phone', ''),
                        userID=user_info.get('userId', ''),
                        username=user_info.get('wxNickname', ''),
                        roles="normalUser",
                        gender=user_info.get('wxSex', None),
                        updateTime=datetime.datetime.now()
                    )
                    try:
                        with transaction.atomic():
                            user.save()
                    except Exception as e:
                        logging.error(str(e))
                        return http_return(400, '保存失败')
                    user_data = User.objects.filter(userID=user_info.get('userId', ''), status='normal').first()
                try:
                    user_data.update(loginTime=datetime.datetime.now())
                except Exception as e:
                    logging.error(str(e))
                if not create_session(user_data, token):
                    return http_return(400, '用户不存在')

        return func(request)

    return wrapper
