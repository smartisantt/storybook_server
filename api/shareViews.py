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
    audioList = h5_audioList_format(audios)
    return http_return(200, '成功', {"userInfo": userDict, "total": total, "audioStoryList": audioList})


def h5_listen_detail(request):
    """
    分享听单详情页
    :param request:
    :return:
    """
    uuid = request.GET.get('uuid', '')
    if not uuid:
        return http_return(400, '请选择需要查看的听单')
    listen = Listen.objects.filter(uuid=uuid, status=0).first()
    if not listen:
        return http_return(400, '该听单已被删除')
    user = listen.userUuid
    users = []
    users.append(user)
    userInfo = userList_format(users)[0]
    listenInfo = {
        "uuid": listen.uuid,
        "name": listen.name,
        "icon": listen.icon,
        "intro": listen.intro if listen.intro else '',
    }
    listenAudio = ListenAudio.objects.filter(listenUuid=uuid, status=0).order_by("-updateTime").all()
    audios = []
    for la in listenAudio:
        audio = la.audioUuid
        audios.append(audio)
    audioList = h5_audioList_format(audios)
    return http_return(200, '成功', {"info": listenInfo, "userInfo": userInfo, "list": audioList, "type": 1})


def h5_album_detail(request):
    """
    分享听单详情页
    :param request:
    :return:
    """
    uuid = request.GET.get('uuid', '')
    if not uuid:
        return http_return(400, '请选择需要查看的专辑')
    album = Album.objects.filter(uuid=uuid, isDelete=False).first()
    if not album:
        return http_return(400, '该专辑已被删除')
    user = album.author
    users = []
    users.append(user)
    userInfo = userList_format(users)[0]
    albumInfo = {
        "uuid": album.uuid,
        "name": album.title,
        "icon": album.faceIcon,
        "intro": album.intro if album.intro else '',
    }
    albumAudio = AlbumAudioStory.objects.filter(album__uuid=uuid, isUsing=True).order_by("-updateTime").all()
    audios = []
    for aa in albumAudio:
        audio = aa.audioStory
        audios.append(audio)
    audioList = h5_audioList_format(audios)
    return http_return(200, '成功', {"info": albumInfo, "userInfo": userInfo, "list": audioList, "type": 2})


def h5_audio_play(request):
    """
    播放作品
    :param request:
    :return:
    """
    uuid = request.GET.get('uuid', '')
    if not uuid:
        return http_return(400, '参数错误')
    audio = AudioStory.objects.filter(uuid=uuid).first()
    if not audio:
        return http_return(400, '故事信息不存在')
    # 更新播放次数
    audio.playTimes += 1
    try:
        with transaction.atomic():
            audio.save()
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '更新播放次数失败')
    audios = []
    audios.append(audio)
    playDict = audioList_format(audios)[0]
    return http_return(200, '成功', playDict)
