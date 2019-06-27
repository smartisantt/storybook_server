#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# Create your views here.
from django.db.models import Q

from api.ssoSMS.sms import send_sms
from common.common import *
from manager.models import *
from api.apiCommon import *
from storybook_sever.config import IS_SEND, TEL_IDENTIFY_CODE


def identify_code(request):
    """
    获取验证码
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    tel = data.get('tel', '0')
    if not match_tel(tel):
        return http_return(400, '请输入正确的手机号')

    my_random = random_string(6, string.digits)
    text = "您的验证码是：{0}。请不要把验证码泄露给其他人。".format(my_random)
    if IS_SEND:
        rv = send_sms(text, tel)
        try:
            result = eval(rv)
        except Exception as e:
            logging.error(str(e))
            result = {"code": 0, "msg": "", "smsid": "0"}
    else:
        my_random = '123456'
        result = {'code': 2}
    if result.get('code', '0') == 2:
        cache.set(tel, my_random, TEL_IDENTIFY_CODE)
        return http_return(200, '短信已发送')
    else:
        return http_return(400, '短信发送失败')


def check_identify_code(request):
    """
    校验验证码
    :param request:
    :return:
    """
    data = request_body(request, "POST")
    if not data:
        return http_return(400, '参数错误')
    identify_code = data.get('identifyCode')
    tel = data.get('tel')
    code = cache.get(tel)
    if code != identify_code:
        return http_return(400, '验证码错误')
    return http_return(200, '验证码正确')


@check_identify
def recording_index_list(request):
    """
    首页信息展示
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    page = data.get('page', '')
    pageCount = data.get('pageCount', '')
    sort = data.get('sort', '')  # latest最新 rank排行 recommended推荐
    if sort not in ['latest', 'rank', 'recommended']:
        return http_return(400, '参数错误')
    story = Story.objects.exclude(status="destroy")
    if sort == "latest":
        story = story.filter(isRecommd=False).order_by("-isTop", "-updateTime")
    elif sort == "rank":
        story = story.order_by("-recordNum")
    elif sort == "recommended":  # 推荐算法
        story = story.filter(isRecommd=True).order_by("-isTop", "-updateTime")
    stories = story.all()
    total, stories = page_index(stories, page, pageCount)
    storyList = []
    for st in stories:
        storyList.append({
            "uuid": st.uuid,
            "name": st.name,
            "icon": st.listIcon,
            "count": st.recordNum,
        })
    return http_return(200, '成功', {"total": total, "storyList": storyList})


@check_identify
def recording_banner(request):
    """
    首页轮播图
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    nowDatetime = datetime.datetime.now()
    banner = CycleBanner.objects.filter(startTime__lte=nowDatetime, endTime__gte=nowDatetime, isUsing=True)
    # 按显示序号排序
    banner = banner.filter(location=1).order_by('orderNum')
    banners = banner.all()
    banList = []
    for banner in banners:
        banList.append({
            'name': banner.name,
            'icon': banner.icon,
            'type': banner.type,
            'target': banner.target,
        })
    total = len(banners)
    return http_return(200, '成功', {"total": total, "bannerList": banList})


@check_identify
def recording_stroy_detail(request):
    """
    模板详情
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')
    if not uuid:
        return http_return(400, '参数错误')
    story = Story.objects.filter(uuid=uuid, status="normal").first()
    if not story:
        return http_return(400, '模板故事不存在')
    d = {
        "uuid": story.uuid,
        "name": story.name if story.name else None,
        "content": story.content if story.content else None,
        "icon": story.faceIcon if story.faceIcon else None
    }
    return http_return(200, '成功', d)


@check_identify
def recording_bgmusic_list(request):
    """
    背景音乐列表
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    page = data.get('page', '')
    pageCount = data.get('pageCount', '')
    bgm = Bgm.objects.filter(status='normal').order_by('sortNum')
    bgms = bgm.all()
    total, bgms = page_index(bgms, page, pageCount)
    bgmList = []
    for bg in bgms:
        bgmList.append({
            "uuid": bg.uuid,
            "name": bg.name,
            "duration": bg.duration,
            "url": bg.url,
        })
    return http_return(200, '成功', {"total": total, "bgmList": bgmList})


@check_identify
def recording_send(request):
    """
    发布故事
    :param request:
    :return:
    """
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    storyUuid = data.get('storyUuid', '')
    audioUrl = data.get('audioUrl', '')
    audioVolume = data.get('audioVolume', '')
    bgmUuid = data.get('bgmUuid', '')
    bgmVolume = data.get('bgmVolume', '')
    remarks = data.get('remarks', '')
    type = data.get('type', '')
    storyTagUuidList = data.get('storyTagUuidList', '')
    audioDuration = data.get('audioDuration', '')
    name = None
    icon = None
    audioStoryType = True
    if not storyUuid:
        name = data.get('name', '')
        icon = data.get('icon', '')
        audioStoryType = False
    if bgmUuid:
        bgm = Bgm.objects.filter(uuid=bgmUuid).first()
    if storyUuid:
        story = Story.objects.filter(uuid=storyUuid).first()
    if not all([audioUrl, audioVolume, type, storyTagUuidList, audioDuration]):
        return http_return(400, '参数错误')
    tags = []
    for tagUuid in storyTagUuidList:
        tag = Tag.objects.filter(uuid=tagUuid).first()
        if tag:
            tags.append(tag)
    # 发布用户
    user = User.objects.filter(uuid=data['_cache']['uuid']).first()
    try:
        uuid = get_uuid()
        AudioStory.objects.create(
            uuid=uuid,
            userUuid=user if user else None,
            isUpload=1,
            voiceUrl=audioUrl,
            userVolume=audioVolume,
            bgm=bgm if bgm else None,
            bgmVolume=bgmVolume if bgmVolume else None,
            type=type,
            playTimes=0,
            audioStoryType=audioStoryType,
            storyUuid=story if story else None,
            name=name,
            bgIcon=icon,
            remarks=remarks,
            duration=audioDuration,
            checkStatus="unCheck"
        ).tags.add(*tags)
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '发布失败')
    return http_return(200, '发布成功')


@check_identify
def recording_tag_list(request):
    """
    发布故事标签选择列表
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    tag = Tag.objects.filter(code="RECORDTYPE", isUsing=True, isDelete=False).order_by('sortNum')
    tags = tag.all()
    tagList = []
    for tag in tags:
        tagList.append({
            "uuid": tag.uuid,
            "name": tag.name,
        })
    total = len(tagList)
    return http_return(200, '成功', {"total": total, "tagList": tagList})


@check_identify
def user_center(request):
    """
    用户个人中心
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')
    user = User.objects.filter(uuid=uuid).first()
    if not user:
        return http_return(400, '用户信息不存在')
    fans = user.get_followers()
    focus = user.get_follows()
    isFollow = False
    myUuid = data['_cache']['uuid']
    for focu in focus:
        if myUuid == focu.uuid:
            isFollow = True
            break
    userDict = {
        "uuid": user.uuid,
        "name": user.nickName,
        "avatar": user.avatar,
        "id": user.id,
        "isFollower": isFollow,
        "intro": user.intro,
        "followersCount": len(fans),
        "followsCount": len(focus)
    }
    return http_return(200, '成功', {"userInfo": userDict})


@check_identify
def become_fans(request):
    """
    关注用户
    :param request:
    :return:
    """
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')
    selfUuid = data['_cache']['uuid']
    selfUser = User.objects.filter(uuid=selfUuid).first()
    if not selfUser.set_follows(uuid):
        return http_return(400, '关注失败')
    return http_return(200, '关注成功')


@check_identify
def user_audio_list(request):
    """
    用户故事列表
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')
    page = data.get('page', '')
    pageCount = data.get('pageCount', '')
    user = User.objects.filter(uuid=uuid).first()
    if not user:
        return http_return(400, '用户信息不存在')
    audios = user.useAudioUuid.filter(isDelete=False).order_by("-createTime").all()
    total, audios = page_index(audios, page, pageCount)
    audioList = []
    for audio in audios:
        icon = audio.bgIcon
        name = audio.name
        if audio.audioStoryType:
            icon = audio.storyUuid.listIcon
            name = audio.storyUuid.name
        tagList = []
        for tag in audio.tags.all():
            tagList.append({
                'uuid': tag.uuid,
                'name': tag.name
            })
        audioList.append({
            "uuid": audio.uuid,
            "duration": audio.duration,
            "icon": icon,
            "name": name,
            "createTime": datetime_to_string(audio.createTime),
            "tagList": tagList
        })
    return http_return(200, '成功', {"total": total, "audioStoryList": audioList})


@check_identify
def user_fans(request):
    """
    用户的粉丝列表
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')
    type = data.get('type', '')
    page = data.get('page', '')
    pageCount = data.get('pageCount', '')
    if not uuid:
        return http_return(400, '参数错误')
    user = User.objects.filter(uuid=uuid).first()
    if not user:
        return http_return(400, '用户信息不存在')
    if type == 'follows':
        users = user.get_follows()
    elif type == 'followers':
        users = user.get_followers()
    else:
        return http_return(400, '参数错误')
    total, users = page_index(users, page, pageCount)
    userList = []
    for u in users:
        userList.append({
            "uuid": u.uuid,
            "avatar": u.avatar,
            "name": u.nickName
        })
    return http_return(200, '成功', {"total": total, "userList": userList})


@check_identify
def audio_list(request):
    """
    播放列表
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    page = data.get('page', '')
    pageCount = data.get('pageCount', '')
    audioStoryType = data.get('audioStoryType', None)
    audio = AudioStory.objects.filter(checkStatus='check', isDelete=False)
    if audioStoryType:
        audio = audio.filter(audioStoryType=audioStoryType)
    audios = audio.order_by('-createTime').all()
    total, audios = page_index(audios, page, pageCount)
    audioList = []
    for audio in audios:
        bgIcon = audio.bgIcon
        name = audio.name
        if audio.audioStoryType:
            bgIcon = audio.storyUuid.listIcon
            name = audio.storyUuid.name
        tagList = []
        for tag in audio.tags.all():
            tagList.append({
                'uuid': tag.uuid,
                'name': tag.name
            })
        audioList.append({
            "uuid": audio.uuid,
            "duration": audio.duration,
            "icon": bgIcon,
            "name": name,
            "createTime": datetime_to_string(audio.createTime),
            "tagList": tagList
        })
    return http_return(200, '成功', {"total": total, "audioStoryList": audioList})


@check_identify
def audio_play(request):
    """
    播放作品
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')
    page = data.get('page', '')
    pageCount = data.get('pageCount', '')
    if not uuid:
        return http_return(400, '参数错误')
    audio = AudioStory.objects.filter(uuid=uuid, checkStatus='check', isDelete=False).first()
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
    # 记录播放历史
    selfUuid = data['_cache']['uuid']
    selfUser = User.objects.filter(uuid=selfUuid).first()
    try:
        with transaction.atomic():
            Behavior.objects.create(
                uuid=get_uuid(),
                userUuid=selfUser,
                audioUuid=audio,
                type=4,
            )
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '保存记录失败')
    content = None
    name = audio.name
    bgIcon = audio.bgIcon
    if audio.audioStoryType:
        content = audio.storyUuid.content
        name = audio.storyUuid.name
        bgIcon = audio.storyUuid.faceIcon
    playDict = {
        "audio": {
            "uuid": audio.uuid,
            "name": name,
            "content": content,
            "icon": bgIcon,
            "duration": audio.duration,
            "audioUrl": audio.voiceUrl,
            "audioVolume": audio.userVolume,
            "createTime": datetime_to_string(audio.createTime),
            "playCount": audio.playTimes,
        },
        "bgm": {
            "uuid": audio.bgm.uuid if audio.bgm else None,
            "bgmUrl": audio.bgm.url if audio.bgm else None,
            "bgmVolume": audio.bgmVolume if audio.bgm else None,
        },
        "publisher": {
            "uuid": audio.userUuid.uuid if audio.userUuid else None,
            "nickname": audio.userUuid.nickName if audio.userUuid else None,
            "avatar": audio.userUuid.avatar if audio.userUuid else None,
            "createTime": datetime_to_string(audio.userUuid.createTime) if audio.userUuid else None,
        }
    }
    otheraudio = AudioStory.objects.exclude(uuid=uuid, isDelete=True).filter(userUuid__uuid=audio.userUuid.uuid)
    otheraudios = otheraudio.order_by("-createTime").all()
    total, otheraudios = page_index(otheraudios, page, pageCount)
    audioList = []
    for otheraudio in otheraudios:
        name = otheraudio.name
        if otheraudio.audioStoryType:
            name = otheraudio.storyUuid.name
        tagList = []
        for tag in otheraudio.tags.all():
            tagList.append({
                'uuid': tag.uuid,
                'name': tag.name
            })
        audioList.append({
            "uuid": otheraudio.uuid,
            "duration": otheraudio.duration,
            "icon": otheraudio.bgIcon,
            "name": name,
            "createTime": datetime_to_string(otheraudio.createTime),
            "tagList": tagList
        })

    return http_return(200, '成功',
                       {"total": total,
                        "audioStoryList": audioList,
                        "playInfo": playDict, })


@check_identify
def audio_like(request):
    """
    点赞
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', None)
    if not uuid:
        return http_return(400, '参数错误')
    audio = AudioStory.objects.filter(uuid=uuid).first()
    selfUuid = data['_cache']['uuid']
    user = User.objects.filter(uuid=selfUuid).first()
    try:
        Behavior.objects.create(
            userUuid=user,
            audioUuid=audio,

        )
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '点赞失败')
    return http_return(200, '点赞成功')


@check_identify
def index_banner(request):
    """
    首页轮播图
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    nowDatetime = datetime.datetime.now()
    banner = CycleBanner.objects.filter(startTime__lte=nowDatetime, endTime__gte=nowDatetime, isUsing=True)
    # 按显示序号排序
    banner = banner.filter(location=0).order_by('orderNum')
    banners = banner.all()
    banList = []
    for banner in banners:
        banList.append({
            'name': banner.name,
            'icon': banner.icon,
            'type': banner.type,
            'target': banner.target,
        })
    total = len(banners)
    return http_return(200, '成功', {"total": total, "bannerList": banList})


@check_identify
def index_list(request):
    """
    首页列表
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    # 每日一读
    everList = []
    ever = Module.objects.filter(type='MOD1').order_by("orderNum").first()
    if ever:
        name = ever.audioUuid.name
        intro = None
        bgIcon = ever.audioUuid.bgIcon
        if ever.audioUuid.audioStoryType:
            name = ever.audioUuid.audioUuid.name
            intro = ever.audioUuid.audioUuid.intro
            bgIcon = ever.audioUuid.audioUuid.listIcon
        everList.append({
            "uuid": ever.audioUuid.uuid,
            "name": name,
            "intro": intro,
            "icon": bgIcon,
        })
    # 抢先听
    firstList = []
    firsts = Module.objects.filter(type='MOD2').order_by("orderNum").all()[:4]
    if firsts:
        for first in firsts:
            name = first.audioUuid.name
            bgIcon = first.audioUuid.bgIcon
            if first.audioUuid.audioStoryType:
                name = first.audioUuid.storyUuid.name
                bgIcon = first.audioUuid.storyUuid.listIcon
            firstList.append({
                "uuid": first.audioUuid.uuid,
                "name": name,
                "icon": bgIcon,
            })
    # 热门推荐
    hotList = []
    hots = Module.objects.filter(type='MOD3').order_by("orderNum").all()[:4]
    if hots:
        for hot in hots:
            name = hot.audioUuid.name
            bgIcon = hot.audioUuid.bgIcon
            if hot.audioUuid.audioStoryType:
                name = hot.audioUuid.storyUuid.name
                bgIcon = hot.audioUuid.storyUuid.listIcon
            hotList.append({
                "uuid": hot.audioUuid.uuid,
                "name": name,
                "icon": bgIcon,
            })
    # 猜你喜欢
    likeList = []
    audios = AudioStory.objects.filter(isDelete=False, checkStatus="check").order_by("-playTimes").all()[:6]
    if audios:
        for audio in audios:
            name = audio.name
            bgIcon = audio.bgIcon
            if audio.audioStoryType:
                name = audio.storyUuid.name
                bgIcon = audio.storyUuid.listIcon
            likeList.append({
                "uuid": audio.uuid,
                "name": name,
                "icon": bgIcon
            })
    return http_return(200, '成功',
                       {"daliyReadList": everList, "listenFirstList": firstList, "hotRecommdList": hotList,
                        "mayLikeList": likeList})


@check_identify
def search_all(request):
    """
    搜索历史
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    keyWord = data.get('keyword')
    selfUuid = data['_cache']['uuid']
    selfUser = User.objects.filter(uuid=selfUuid).first()
    if not selfUser:
        return http_return(400, '未获取到用户信息')
    if not keyWord:
        return http_return(400, '参数错误')
    if not save_search(data):
        return http_return(400, '存储搜索记录失败')
    audio = AudioStory.objects.filter(checkStatus='check', isDelete=False)
    user = User.objects.filter(roles='normalUser')
    audio = audio.filter(Q(storyUuid__name__contains=keyWord) | Q(name__contains=keyWord)).order_by("-isTop",
                                                                                                    "-createTime")
    user = user.filter(nickName__contains=keyWord).order_by("-createTime")
    audioList = []
    for au in audio.all()[:6]:
        icon = au.bgIcon
        name = au.name
        if au.audioStoryType:
            icon = au.storyUuid.listIcon
            name = au.storyUuid.name
        audioList.append({
            "uuid": au.uuid,
            "icon": icon,
            "name": name,
        })
    userList = []
    for u in user.all()[:6]:
        audioCount = u.useAudioUuid.filter(isDelete=False).count()
        followers = len(u.get_followers())
        userList.append({
            "uuid": u.uuid,
            "avatar": u.avatar,
            "nickname": u.nickName,
            "audioCount": audioCount,
            "followersCount": followers,
        })
    return http_return(200, '成功', {"audioStoryList": audioList, "userList": userList})


@check_identify
def search_audio(request):
    """
    搜索音频
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    keyWord = data.get('keyword')
    page = data.get('page', '')
    pageCount = data.get('pageCount', '')
    selfUuid = data['_cache']['uuid']
    selfUser = User.objects.filter(uuid=selfUuid).first()
    if not selfUser:
        return http_return(400, '未获取到用户信息')
    if not keyWord:
        return http_return(400, '参数错误')
    if not save_search(data):
        return http_return(400, '存储搜索记录失败')
    audio = AudioStory.objects.filter(checkStatus='check', isDelete=False)
    audio = audio.filter(Q(storyUuid__name__contains=keyWord) | Q(name__contains=keyWord)).order_by("-createTime")
    audios = audio.all()
    total, audios = page_index(audios, page, pageCount)
    audioList = []
    for au in audios:
        icon = au.bgIcon
        name = au.name
        if au.audioStoryType:
            icon = au.storyUuid.listIcon
            name = au.storyUuid.name
        audioList.append({
            "uuid": au.uuid,
            "icon": icon,
            "name": name,
            "publisher": au.userUuid.nickName,
            "duration": au.duration,
        })
    return http_return(200, '成功', {"audioStoryList": audioList, "total": total})


@check_identify
def search_user(request):
    """
    搜索历史
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    keyWord = data.get('keyword')
    page = data.get('page', '')
    pageCount = data.get('pageCount', '')
    selfUuid = data['_cache']['uuid']
    selfUser = User.objects.filter(uuid=selfUuid).first()
    if not selfUser:
        return http_return(400, '未获取到用户信息')
    if not keyWord:
        return http_return(400, '参数错误')
    if not save_search(data):
        return http_return(400, '存储搜索记录失败')
    user = User.objects.filter(roles='normalUser')
    users = user.filter(nickName__contains=keyWord).order_by("-createTime").all()
    total, users = page_index(users, page, pageCount)
    userList = []
    for u in users:
        audioCount = u.useAudioUuid.filter(isDelete=False).count()
        followers = len(u.get_followers())
        userList.append({
            "uuid": u.uuid,
            "avatar": u.avatar,
            "nickname": u.nickName,
            "audioStoryCount": audioCount,
            "followersCount": followers,
        })
    return http_return(200, '成功', {"total": total, "userList": userList})


@check_identify
def search_hot(request):
    """
    热搜关键字
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    hots = HotSearch.objects.filter(isDelete=False).order_by("-orderNum", "-searchNum").all()[:10]
    hotSearchList = []
    for hot in hots:
        hotSearchList.append(hot.keyword)
    hotSearch = ','.join(hotSearchList)
    return http_return(200, "成功", {"hotSearch": hotSearch})


@check_identify
def index_class_show(request):
    """
    首页绘本
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    className = data.get('className', None)
    page = data.get('page', '')
    pageCount = data.get('pageCount', '')
    if not className:
        return http_return(400, '参数错误')
    audio = AudioStory.objects.filter(isDelete=False, checkStatus="check")
    audios = audio.filter(tags__name=className).all()
    total, audios = page_index(audios, page, pageCount)
    audioStoryList = []
    for audio in audios:
        icon = audio.bgIcon
        name = audio.name
        content = None
        if audio.audioStoryType:
            icon = audio.storyUuid.listIcon if audio.storyUuid else None
            name = audio.storyUuid.name if audio.storyUuid else None
            content = audio.storyUuid.content if audio.storyUuid else None
        tagList = []
        for tag in audio.tags.all():
            tagList.append({
                'uuid': tag.uuid,
                'name': tag.name
            })
        audioStoryList.append({
            "uuid": audio.uuid,
            "duration": audio.duration,
            "icon": icon,
            "name": name,
            "content": content,
            "palyCount": audio.playTimes,
            "createTime": datetime_to_string(audio.createTime),
            "tagList": tagList
        })
    return http_return(200, '成功', {"total": total, "audioStoryList": audioStoryList})
