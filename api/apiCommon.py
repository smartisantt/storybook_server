#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import random
import re
import string

from django.core.cache import caches
from django.core.paginator import Paginator
from django.db.models import Q

from common.common import http_return, get_uuid, datetime_to_unix, page_index
from manager.models import *
from common.api import Api
from storybook_sever.config import USER_SESSION_OVER_TIME, SHAREURL


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


def create_session(user_data, token, user_info):
    """
    用户信息保存至caches
    :param request:
    :param user_info:
    :return:
    """
    user = {
        'nickName': user_data.nickName if user_data.nickName else None,
        'uuid': user_data.uuid,
        'userId': user_data.userID,
        'tel': user_data.tel,
        'loginIp': user_info.get('loginIp', ''),
    }
    try:
        caches['api'].set(token, user, USER_SESSION_OVER_TIME)
    except Exception as e:
        logging.error(str(e))
        return False
    objKey = user_data.userID + "-" + user_info.get('platform', '')
    try:
        objToken = caches['api'].get(objKey)
    except Exception as e:
        logging.error(str(e))
        return False
    if objToken:
        if objToken != token:
            try:
                caches['api'].delete(objToken)
                caches['api'].set(objKey, token, USER_SESSION_OVER_TIME)
            except Exception as e:
                logging.error(str(e))
                return False
    else:
        try:
            caches['api'].set(objKey, token, USER_SESSION_OVER_TIME)
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


def save_login_log(user_info, user, request):
    """
    保存登陆日志
    :param user_info:
    :param user:
    :return:
    """
    try:
        log = LoginLog(
            uuid=get_uuid(),
            ipAddr=user_info.get('loginIp', ''),
            userUuid=user,
            userAgent=request.META.get('HTTP_USER_AGENT', ''),
        )
        log.save()
    except Exception as e:
        logging.error(str(e))
        return False
    return True


def create_user(user_info):
    """
    添加用户信息到user
    :param user_info:
    :return:
    """
    user_uuid = get_uuid()
    version = Version.objects.filter(status="dafault").first()
    defaultIcon = user_info.get('wxAvatarUrl', '')
    if defaultIcon == '':
        defaultIcon = 'https://hbb-ads.oss-cn-beijing.aliyuncs.com/file1111746672834.png'
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
        loginType=user_info.get('loginType', ''),
    )
    try:
        with transaction.atomic():
            user.save()
    except Exception as e:
        logging.error(str(e))
        return False
    return user


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
                user_data = User.objects.filter(userID=user_info.get('userId', '')).first()
                if not user_data:
                    user_data = create_user(user_info)
                    if not user_data:
                        return http_return(400, "用户信息保存失败")
                # 处理缓存信息，更新或者添加
                if not create_session(user_data, token, user_info):
                    return http_return(401, '缓存错误，请稍后重试')
            # 如果有登陆出现，则存登录日志
        nowDate = datetime.date.today()
        userID = user_info.get('userId', '')
        selfUser = User.objects.filter(userID=user_info.get('userId', ''), status='normal').first()
        if not selfUser:
            return http_return(400, '登录错误，请联系管理员')
        selfUuid = selfUser.uuid
        logDate = caches['api'].get(selfUuid)
        if logDate:
            if logDate != nowDate:  # 如果当天没有存日志则添加
                if not save_login_log(user_info, selfUser, request):
                    return http_return(400, '存储登陆日志失败')
                caches['api'].delete(selfUuid)
                try:
                    caches['api'].set(selfUuid, nowDate, USER_SESSION_OVER_TIME)
                except Exception as e:
                    logging.error(str(e))
                    return http_return(400, '缓存错误')
        else:  # 如果没有标志则存入标志并且保存登录日志
            try:
                caches['api'].set(selfUuid, nowDate, USER_SESSION_OVER_TIME)
            except Exception as e:
                logging.error(str(e))
                return http_return(400, '缓存错误')
            if not save_login_log(user_info, selfUser, request):
                return http_return(400, '存储登陆日志失败')

        # 禁止登陆
        forbidInfo = caches['api'].get(userID)
        if forbidInfo and forbidInfo == "forbbiden_login":
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
        userID = user_info.get('userId', '')
        forbidInfo = caches['api'].get(userID)
        if forbidInfo and forbidInfo == "forbbiden_say":
            return http_return(403, '禁止操作，请联系管理员')

        return func(request)

    return wrapper


def share_format(icon, title, url, content):
    """
    分享模型
    :param icon:
    :param title:
    :param url:
    :param content:
    :return:
    """
    return {"icon": icon, "title": title, "content": content, "url": url}


def audioList_format(audios, data=None):
    """
    处理返回格式化
    :param audios:
    :return:
    """
    selfUuid = None
    if data:
        selfUuid = data['_cache']['uuid']
    audioStoryList = []
    for audio in audios:
        checkPraise = Behavior.objects.filter(userUuid__uuid=selfUuid, audioUuid__uuid=audio.uuid, type=1).first()
        checkLike = Behavior.objects.filter(userUuid__uuid=selfUuid, audioUuid__uuid=audio.uuid, type=3).first()
        story = None
        if audio.storyUuid:
            storyObj = audio.storyUuid
            story = {
                "uuid": storyObj.uuid if storyObj.uuid else '',
                "name": storyObj.name if storyObj.name else '',
                "icon": storyObj.faceIcon if storyObj.faceIcon else '',
                "content": storyObj.content if storyObj.content else '',
                "intro": storyObj.intro if storyObj.intro else ''
            }
        bgm = None
        if audio.bgm:
            bgmObj = audio.bgm
            bgm = {
                "uuid": bgmObj.uuid if bgmObj.uuid else '',
                "url": bgmObj.url if bgmObj.url else '',
                "name": bgmObj.name if bgmObj.name else '',
                "duration": bgmObj.duration if bgmObj.duration else 0,
            }
        tagList = []
        for tag in audio.tags.all():
            tagList.append({
                'uuid': tag.uuid,
                'name': tag.name if tag.name else '',
                "icon": tag.icon if tag.icon else '',
            })
        publisher = None
        if audio.userUuid:
            user = audio.userUuid
            publisher = {
                "uuid": user.uuid if user.uuid else '',
                "nickname": user.nickName if user.nickName else '',
                "avatar": user.avatar if user.avatar else '',
                "createTime": datetime_to_unix(user.createTime) if user.createTime else 0,
                "city": user.city if user.city else ''
            }
        content = "我在听【" + audio.name + "】，你可能也喜欢，快来听吧"
        if selfUuid and selfUuid == audio.userUuid.uuid:
            content = "我录制了【" + audio.name + "】，快来听听看"
        url = SHAREURL + "/playDetails/" + audio.uuid
        share = share_format(audio.bgIcon, audio.name, url, content)
        audioStoryList.append({
            "uuid": audio.uuid,
            "remarks": audio.remarks if audio.remarks else '',
            "name": audio.name if audio.name else '',
            "icon": audio.bgIcon if audio.bgIcon else '',
            "audioVolume": audio.userVolume if audio.userVolume else 1.0,
            "bgmVolume": audio.bgmVolume if audio.bgmVolume else 1.0,
            "createTime": datetime_to_unix(audio.createTime) if audio.createTime else 0,
            "playCount": audio.playTimes if audio.playTimes else 0,
            "story": story,
            "audio": {
                "url": audio.voiceUrl if audio.voiceUrl else '',
                "duration": audio.duration if audio.duration else 0,
                "fileSize": audio.fileSize if audio.fileSize else 0,
            },
            "bgm": bgm,
            "publisher": publisher,
            "isPraise": True if checkPraise else False,
            "praiseCount": audio.bauUuid.filter(type=1, status=0).count(),
            "isCollection": True if checkLike else False,
            "collectionCount": audio.bauUuid.filter(type=3, status=0).count(),
            "commentsCount": audio.bauUuid.filter(type=2, status=0, checkStatus="check").count(),
            "tagList": tagList,
            "share": share,
        })
    return audioStoryList


def activity_audioList_format(audios):
    """
    活动处理返回格式化
    :param audios:
    :return:
    """
    audioStoryList = []
    for audio in audios:
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
            "createTime": datetime_to_unix(audio.createTime) if audio.createTime else 0,
            "tagList": tagList,
        })
    return audioStoryList


def userList_format(users):
    """
    格式返回用户列表
    :param users:
    :return:
    """
    resultList = []
    for u in users:
        audioCount = u.useAudioUuid.filter(isDelete=False).filter(
            Q(checkStatus__in=["check", "exemption"]) | Q(interfaceStatus="check")).exclude(
            Q(checkStatus="checkFail") | Q(interfaceStatus="checkFail")).count()
        followers = FriendShip.objects.filter(follows__uuid=u.uuid).count()
        resultList.append({
            "uuid": u.uuid,
            "avatar": u.avatar if u.avatar else '',
            "nickname": u.nickName if u.nickName else '',
            "city": u.city if u.city else '',
            "audioStoryCount": audioCount,
            "followersCount": followers,
        })
    return resultList


def result_all(audios, users, data):
    """
    返回搜索和分类筛选结果
    :param audios:
    :param users:
    :param data:
    :return:
    """
    audioList = audioList_format(audios, data)
    userList = userList_format(users)
    searchAudioStory = {
        "filter": [
            {"label": "最多播放", "value": "rank"},
            {"label": "最新上传", "value": "latest"}
        ],
        "list": audioList,
    }
    searchUser = {
        "filter": [
            {"label": "最多粉丝", "value": "followersCount"},
            {"label": "最多音频", "value": "audioStoryCount"}
        ],
        "list": userList,
    }
    return searchAudioStory, searchUser


def paginator(myList, page, pageCount=10):
    """
    插件分页
    :param page:
    :param pageCount:
    :return:
    """
    try:
        pageObj = Paginator(myList, pageCount)
        total = pageObj.count
        res_data = pageObj.page(page)
    except Exception as e:
        logging.error(str(e))
        return False
    return total, res_data


def h5_audioList_format(audios):
    """
    分享返回模型
    :param audios:
    :return:
    """
    audioList = []
    for audio in audios:
        bgm = None
        if audio.bgm:
            bgmObj = audio.bgm
            bgm = {
                "uuid": bgmObj.uuid if bgmObj.uuid else '',
                "url": bgmObj.url if bgmObj.url else '',
                "name": bgmObj.name if bgmObj.name else '',
                "duration": bgmObj.duration if bgmObj.duration else 0,
            }
        audioList.append({
            "uuid": audio.uuid,
            "remarks": audio.remarks if audio.remarks else '',
            "name": audio.name if audio.name else '',
            "icon": audio.bgIcon if audio.bgIcon else '',
            "createTime": datetime_to_unix(audio.createTime) if audio.createTime else 0,
            "audio": {
                "url": audio.voiceUrl if audio.voiceUrl else '',
                "duration": audio.duration if audio.duration else 0,
            },
            "bgm": bgm,
            "audioVolume": audio.userVolume if audio.userVolume else 1.0,
            "bgmVolume": audio.bgmVolume if audio.bgmVolume else 1.0,
        })
    return audioList


def albumList_format(albums):
    """
    统一返回听单和转接模型
    :param objList:
    :return:
    """
    albumList = []
    for albu in albums:
        albumList.append({
            "uuid": albu.uuid,
            "name": albu.title,
            "icon": albu.faceIcon,
            "intro": albu.intro if albu.intro else '',
            "audioStoryCount": albu.audioStory.count() if albu.audioStory else 0,
        })
    return albumList


def listenList_format(listens):
    """
    听单列表返回模型
    :param listens:
    :return:
    """
    listenList = []
    for lis in listens:
        listenList.append({
            "uuid": lis.uuid,
            "name": lis.name,
            "icon": lis.icon,
            "intro": lis.intro if lis.intro else '',
            "audioStoryCount": lis.listListenUuid.filter(status=0).count() if lis.listListenUuid else 0,
        })
    return listenList


def indexList_format(objList):
    """
    定义首页返回列表模型
    :param objList:
    :return:
    """
    resultList = []
    for obj in objList:
        if obj.albumUuid:
            album = obj.albumUuid
            resultList.append({
                "uuid": album.uuid,
                "name": album.title,
                "icon": album.faceIcon,
                "intro": album.intro if album.intro else '',
                "audioStoryCount": album.audioStory.count() if album.audioStory else 0,
                "type": 1,
                "target": album.uuid,
            })
        if obj.audioUuid:
            audio = obj.audioUuid
            resultList.append({
                "uuid": audio.uuid,
                "name": audio.name if audio.name else '',
                "icon": audio.bgIcon if audio.bgIcon else '',
                "content": audio.remarks if audio.remarks else '',
                "type": 2,
                "target": audio.uuid,
            })
    return resultList


def activityRankList_format(games):
    """
    活动排行返回模型
    :param objList:
    :return:
    """
    resultList = []
    for game in games:
        resultList.append({
            "uuid": game.uuid,
            "publisher": {
                "uuid": game.userUuid.uuid if game.userUuid else '',
                "nickname": game.userUuid.nickName if game.userUuid else '',
                "avatar": game.userUuid.avatar if game.userUuid else '',
            },
            "audio": {
                "uuid": game.audioUuid.uuid if game.audioUuid else '',
                "name": game.audioUuid.name if game.audioUuid else '',
                "icon": game.audioUuid.bgIcon if game.audioUuid else '',
            },
            "score": game.votes,
        })
    return resultList


def prizeList_format(prizes):
    """
    奖品列表模型
    :param prizes:
    :return:
    """
    prizeList = []
    for prize in prizes:
        prizeList.append({
            "uuid": prize.uuid,
            "name": prize.name if prize.name else "",
            "icon": prize.icon if prize.icon else "",
            "type": prize.type if prize.type else "",
        })
    return prizeList


def commentList_format(comments):
    """
    评论返回模型
    :param comments:
    :return:
    """
    commentList = []
    for comment in comments:
        user = comment.userUuid
        if user:
            users = []
            users.append(user)
            userInfo = userList_format(users)[0]
        commentList.append({
            "uuid": comment.uuid,
            "createTime": datetime_to_unix(comment.createTime),
            "replyUuid": "",
            "replyType": 0,
            "content": comment.remarks,
            "user": userInfo,
        })
    return commentList


def message_format(mylist, pageCount, ftype, uuid=None, way=None):
    """
    消息刷新返回
    :param mylist:
    :param pageCount:
    :param uuid:
    :param way:
    :param ftype:
    :return:
    """
    mylist = list(mylist)
    if isinstance(pageCount, str) and pageCount == "":
        pageCount = 10
    else:
        pageCount = int(pageCount)
    resultList = mylist[:pageCount]
    total = len(mylist)
    if uuid and way:
        targetObj = None
        if ftype == 1:
            targetObj = SystemNotification.objects.filter(uuid=uuid).first()
        elif ftype == 2:
            targetObj = FriendShip.objects.filter(uuid=uuid).first()
        elif ftype == 3:
            targetObj = Behavior.objects.filter(uuid=uuid, type=1).first()
        elif ftype == 4:
            targetObj = Behavior.objects.filter(uuid=uuid, type=2).first()
        if not targetObj:
            return False
        targetIndex = mylist.index(targetObj)
        if way == "up":
            end = targetIndex + pageCount + 1
            resultList = mylist[targetIndex + 1:end]
        elif way == "down":
            start = targetIndex - pageCount
            if start < 0:
                start = 0
            resultList = mylist[start:targetIndex]
        else:
            return False
    return total, resultList
