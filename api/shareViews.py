#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# Create your views here.

from common.common import *
from api.apiCommon import *


def h5_personal_index(request):
    """
    分享页主播主页
    :param request:
    :return:
    """
    uuid = request.GET.get('uuid', '')
    page = request.GET.get('page', '')
    pageCount = request.GET.get('pageCount', '')
    if not uuid:
        return http_return(400, '请选择要查看得主播')
    user = User.objects.filter(uuid=uuid).first()
    userDict = {
        "uuid": user.uuid,
        "nickname": user.nickName if user.nickName else '',
        "avatar": user.avatar if user.avatar else '',
        "id": user.id,
        "city": user.city if user.city else '',
        "intro": user.intro if user.intro else '',
        "createTime": datetime_to_unix(user.createTime),
        "followersCount": FriendShip.objects.filter(follows__uuid=uuid).count(),
        "followsCount": FriendShip.objects.filter(followers__uuid=uuid).count()
    }
    audios = user.useAudioUuid.all()
    total, audios = page_index(audios, page, pageCount)
    audioList = []
    for audio in audios:
        audioList.append({
            "uuid": audio.uuid,
            "remarks": audio.remarks if audio.remarks else '',
            "name": audio.name if audio.name else '',
            "icon": audio.bgIcon if audio.bgIcon else '',
            "duration": audio.duration if audio.duration else 0,
            "createTime": datetime_to_unix(audio.createTime) if audio.createTime else 0,
        })
    return http_return(200, '成功', {"userInfo": userDict, "total": total, "audioStoryList": audioList})


def h5_listen_detail(request):
    """
    分享听单详情页
    :param request:
    :return:
    """
    uuid = request.GET.get('uuid', '')
    if not uuid:
        return http_return(400, '请选择需要修改的听单')
    listen = Listen.objects.filter(uuid=uuid).first()
    user = listen.userUuid
    users = []
    users.append(user)
    userInfo = userList_format(users)[0]
    if not listen:
        return http_return(400, '听单信息不存在')
    listenInfo = {
        "uuid": listen.uuid,
        "name": listen.name,
        "icon": listen.icon,
        "intro": listen.intro if listen.intro else '',
    }
    listenAudio = ListenAudio.objects.filter(listenUuid=uuid, status=0).order_by("-updateTime").all()
    audioList = []
    for la in listenAudio:
        audio = la.audioUuid
        audioList.append({
            "uuid": audio.uuid,
            "remarks": audio.remarks if audio.remarks else '',
            "name": audio.name if audio.name else '',
            "icon": audio.bgIcon if audio.bgIcon else '',
            "duration": audio.duration if audio.duration else 0,
        })
    return http_return(200, '成功', {"listenInfo": listenInfo, "userInfo": userInfo, "list": audioList, "type": 1})
