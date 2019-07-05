#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import logging
import random
import re
import string

from django.core.cache import cache, caches
from django.db import transaction

from common.common import http_return, get_uuid, datetime_to_unix
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
            return http_return(400, '服务器连接redis失败')
        if not user_info:
            api = Api()
            user_info = api.check_token(token)
            if not user_info:
                return http_return(401, '登录失效')
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
                        return http_return(401, '保存失败')
                    user_data = user
                if not create_session(user_data, token, loginIP):
                    return http_return(401, '用户不存在')
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
                return http_return(401, '日志保存失败')

        selfUuid = user_info.get('uuid')
        nowDatetime = datetime.datetime.now()
        selfUser = User.objects.filter(uuid=selfUuid, startTime__lte=nowDatetime, endTime__gte=nowDatetime,
                                       settingStatus='forbbiden_login').first()
        if selfUser:
            caches['api'].delete(token)
            return http_return(403, '禁止登陆，请联系管理员')

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


def forbbiden_say(func):
    """
    验证禁言装饰器
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
        selfUuid = user_info.get('uuid')
        nowDatetime = datetime.datetime.now()
        selfUser = User.objects.filter(uuid=selfUuid, startTime__lte=nowDatetime, endTime__gte=nowDatetime,
                                       settingStatus='forbbiden_say').first()
        if selfUser:
            caches['api'].delete(token)
            return http_return(403, '禁止操作，请联系管理员')

        return func(request)

    return wrapper


def audioList_format(audios,data):
    """
    处理返回格式化
    :param audios:
    :return:
    """
    selfUuid = data['_cache']['uuid']
    audioStoryList = []
    for audio in audios:
        checkPraise = Behavior.objects.filter(userUuid__uuid=selfUuid, audioUuid__uuid=audio.uuid, type=1).first()
        checkLike = Behavior.objects.filter(userUuid__uuid=selfUuid, audioUuid__uuid=audio.uuid, type=3).first()
        story = None
        if audio.audioStoryType:
            story = {
                "uuid": audio.storyUuid.uuid if audio.storyUuid else '',
                "name": audio.storyUuid.name if audio.storyUuid else '',
                "icon": audio.storyUuid.faceIcon if audio.storyUuid else '',
                "content": audio.storyUuid.content if audio.storyUuid else '',
                "intro": audio.storyUuid.intro if audio.storyUuid else ''
            }
        tagList = []
        for tag in audio.tags.all():
            tagList.append({
                'uuid': tag.uuid,
                'name': tag.name if tag.name else '',
                "icon": tag.icon if tag.icon else '',
            })
        audioStoryList.append({
            "uuid": audio.uuid,
            "name": audio.name if audio.name else '',
            "icon": audio.bgIcon if audio.bgIcon else '',
            "audioVolume": audio.userVolume,
            "createTime": datetime_to_unix(audio.createTime),
            "playCount": audio.playTimes,
            "story": story,
            "audio": {
                "url": audio.voiceUrl,
                "duration": audio.duration,
            },
            "bgm": {
                "uuid": audio.bgm.uuid if audio.bgm else '',
                "url": audio.bgm.url if audio.bgm else '',
                "name": audio.bgm.name if audio.bgm else '',
                "duration":audio.bgm.duration if audio.bgm else '',
            },
            "publisher": {
                "uuid": audio.userUuid.uuid if audio.userUuid else '',
                "nickname": audio.userUuid.nickName if audio.userUuid else '',
                "avatar": audio.userUuid.avatar if audio.userUuid else '',
                "createTime": datetime_to_unix(audio.userUuid.createTime) if audio.userUuid else '',
                "city": audio.userUuid.city if audio.userUuid else ''
            },
            "isPraise": True if checkPraise else False,
            "praiseCount": audio.bauUuid.filter(type=1, status=0).count(),
            "isCollection": True if checkLike else False,
            "collectionCount": audio.bauUuid.filter(type=3, status=0).count(),
            "commentsCount": '',
        })
    return audioStoryList


def paginator(page,pageCount):
    """
    插件分页
    :param page:
    :param pageCount:
    :return:
    """
