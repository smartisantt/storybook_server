#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import logging
import random
import re
import string

from django.core.cache import cache, caches
from django.db import transaction

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
    return ''.join(random.choice(chars) for _s in range(size))


def create_session(user_info, token, loginIP):
    """
    用户信息保存至caches
    :param request:
    :param user_info:
    :return:
    """
    user = {
        'nickName': user_info.nickName if user_info.nickName else None,
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
        start = tel[:3]
        end = tel[-4:]
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
        if not user_info:
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
                        defaultIcon = 'beijing.aliyuncs.com/5cefaceb16d3fc77d6bf8095.jpeg'
                    defaultName = user_info.get('wxNickname', '')
                    if defaultName == '':
                        defaultName = get_default_name(user_info.get('phone', ''))
                    user = User(
                        uuid=user_uuid,
                        tel=user_info.get('phone', ''),
                        userID=user_info.get('userId', ''),
                        nickName=defaultName,
                        roles="normalUser",
                        avatar=defaultIcon,
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
            # 如果有登陆出现，则存登录日志
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


def save_search(data):
    """
    存储搜索记录
    :param request:
    :return:
    """
    # 存储搜索记录
    keyword = data.get('keyword', '')
    uuid = data['_cache']['uuid']
    user = User.objects.filter(uuid=uuid).first()
    try:
        with transaction.atomic():
            SearchHistory.objects.create(
                uuid=get_uuid(),
                searchName=keyword,
                userUuid=user,
            )
    except Exception as e:
        logging.error(str(e))
        return False
    # 累加搜索次数
    hot = HotSearch.objects.filter(keyword=keyword).first()
    if hot:
        try:
            with transaction.atomic():
                hot.searchNum += 1
                hot.save()
        except Exception as e:
            logging(str(e))
            return False
    else:
        try:
            with transaction.atomic():
                HotSearch.objects.create(
                    uuid=get_uuid(),
                    keyword=keyword,
                    searchNum=1,
                )
        except Exception as e:
            logging(str(e))
            return False
    return True
