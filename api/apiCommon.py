#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import logging
import random
import re
import string

from django.core.cache import cache, caches
from django.db import transaction
from pip._vendor.msgpack.fallback import xrange

from common.common import http_return, get_uuid
from manager.models import *
from storybook_sever import api
from storybook_sever.api import Api
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


def create_session(user_info, token, loginIP):
    """
    用户信息保存至caches
    :param request:
    :param user_info:
    :return:
    """
    user = {
        'username': user_info.username if user_info.username else None,
        'uuid': user_info.uuid,
        'userId': user_info.userID,
        'tel': user_info.tel,
        'loginIp': loginIP
    }
    try:
        caches['api'].set(token, user, USER_SESSION_OVER_TIME)
    except Exception as e:
        logging.error(str(e))
        return False
    return True


def get_default_name(tel):
    """
    获取默认用户名
    :return:
    """
    if tel == '':
        result = ''
    else:
        start = tel[:2]
        end = tel[6:]
        result = start + "****" + end
    return result


def check_identify(func):
    """
    身份认证装饰器
    :param func:
    :return:
    """

    def wrapper(request):
        token = request.META.get('HTTP_TOKEN')
        try:
            user_info = caches['api'].get(token)
        except Exception as e:
            logging.error(str(e))
            return http_return(400, '连接redis失败')
        if user_info:
            user_data = User.objects.filter(userID=user_info.get('userId', ''), status='normal').first()
        else:
            api = Api()
            user_info = api.check_token(token)
            if not user_info:
                return http_return(400, '未获取到用户信息')
            else:
                # 记录登录ip,存入缓存
                loginIP = user_info.get('loginIp', '')
                user_data = User.objects.filter(userID=user_info.get('userId', ''), status='normal').first()
                if not user_data:
                    user_uuid = get_uuid()
                    version = Version.objects.filter(status="dafault").first()
                    defaultIcon = user_info.get('wxAvatarUrl', '')
                    if defaultIcon == '':
                        defaultIcon = '42686029A3E740D78CD20E118D615DD3'
                    defaultName = user_info.get('wxNickname', '')
                    if defaultName == '':
                        defaultName = get_default_name(user_info.get('phone', ''))
                    user = User(
                        uuid=user_uuid,
                        tel=user_info.get('phone', ''),
                        userID=user_info.get('userId', ''),
                        username=defaultName,
                        roles="normalUser",
                        userLogo=defaultIcon,
                        gender=user_info.get('wxSex', None),
                        versionUuid=version if version else None,
                        status="normal",
                    )
                    try:
                        with transaction.atomic():
                            user.save()
                    except Exception as e:
                        logging.error(str(e))
                        return http_return(400, '保存失败')
                    user_data = user
                if not create_session(user_data, token, loginIP):
                    return http_return(400, '用户不存在')

        try:
            log = LoginLog(
                uuid=get_uuid(),
                ipAddr=user_info.get('loginIp', ''),
                userUuid=user_data,
            )
            log.save()
        except Exception as e:
            logging.error(str(e))
            return http_return(400, '日志保存失败')

        return func(request)

    return wrapper
