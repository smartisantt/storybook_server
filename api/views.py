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
            "name": st.name if st.name else '',
            "intro": st.intro if st.intro else '',
            "icon": st.faceIcon if st.faceIcon else '',
            "content": st.content if st.content else '',
            "count": st.recordNum,
        })
    return http_return(200, '成功', {"total": total, "list": storyList})


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
            'name': banner.name if banner.name else '',
            'icon': banner.icon if banner.name else '',
            'type': banner.type,
            'target': banner.target if banner.target else '',
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
        "name": story.name if story.name else '',
        "content": story.content if story.content else '',
        "icon": story.faceIcon if story.faceIcon else '',
        "intro": story.intro if story.intro else '',
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
            "name": bg.name if bg.name else '',
            "duration": bg.duration,
            "url": bg.url if bg.url else '',
        })
    return http_return(200, '成功', {"total": total, "list": bgmList})


@forbbiden_say
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
    name = data.get('name', '')
    icon = data.get('icon', '')
    story = None
    audioStoryType = False
    if storyUuid:
        story = Story.objects.filter(uuid=storyUuid).first()
        if not story:
            return http_return(400, '模板信息不存在')
        audioStoryType = True
    bgm = None
    if bgmUuid:
        bgm = Bgm.objects.filter(uuid=bgmUuid).first()
    if not all([audioUrl, audioVolume, type, storyTagUuidList, audioDuration, name, icon]):
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
            bgm=bgm,
            bgmVolume=bgmVolume if bgmVolume else None,
            type=type,
            playTimes=0,
            audioStoryType=audioStoryType,
            storyUuid=story,
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
            "name": tag.name if tag.name else '',
        })
    return http_return(200, '成功', tagList)


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
        "name": user.nickName if user.nickName else '',
        "avatar": user.avatar if user.avatar else '',
        "id": user.id,
        "isFollower": isFollow,
        "intro": user.intro if user.intro else '',
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
            icon = audio.storyUuid.faceIcon
            name = audio.storyUuid.name
        tagList = []
        for tag in audio.tags.all():
            tagList.append({
                'uuid': tag.uuid,
                'name': tag.name if tag.name else '',
                "icon": tag.icon if tag.icon else ''
            })
        audioList.append({
            "uuid": audio.uuid,
            "duration": audio.duration,
            "icon": icon if icon else '',
            "name": name if name else '',
            "createTime": datetime_to_unix(audio.createTime),
            "tagList": tagList
        })
    return http_return(200, '成功', {"total": total, "list": audioList})


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
            "avatar": u.avatar if u.avatar else '',
            "name": u.nickName if u.nickName else ''
        })
    return http_return(200, '成功', {"total": total, "list": userList})


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
        tagList = []
        story = None
        if audio.audioStoryType:
            story = {
                "uuid": audio.storyUuid.uuid if audio.storyUuid else '',
                "name": audio.storyUuid.name if audio.storyUuid else '',
                "icon": audio.storyUuid.faceIcon if audio.storyUuid else '',
                "content": audio.storyUuid.content if audio.storyUuid else '',
                "intro": audio.storyUuid.intro if audio.storyUuid else ''
            }
        for tag in audio.tags.all():
            tagList.append({
                'uuid': tag.uuid,
                'name': tag.name if tag.name else '',
                'icon': tag.icon if tag.icon else ''
            })
        audioList.append({
            "uuid": audio.uuid,
            "duration": audio.duration,
            "icon": audio.bgIcon if audio.bgIcon else '',
            "name": audio.name if audio.name else '',
            "createTime": datetime_to_unix(audio.createTime),
            "tagList": tagList,
            "story": story
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
    story = ''
    if audio.audioStoryType:
        story = {
            "uuid": audio.storyUuid.uuid if audio.storyUuid else '',
            "name": audio.storyUuid.name if audio.storyUuid else '',
            "icon": audio.storyUuid.faceIcon if audio.storyUuid else '',
            "content": audio.storyUuid.content if audio.storyUuid else '',
            "intro": audio.storyUuid.intro if audio.storyUuid else ''
        }
    checkPraise = Behavior.objects.filter(userUuid__uuid=selfUuid, audioUuid__uuid=uuid, type=1).first()
    checkLike = Behavior.objects.filter(userUuid__uuid=selfUuid, audioUuid__uuid=uuid, type=3).first()
    playDict = {
        "uuid": audio.uuid,
        "name": audio.name if audio.name else '',
        "icon": audio.bgIcon if audio.bgIcon else '',
        "duration": audio.duration,
        "audioUrl": audio.voiceUrl,
        "audioVolume": audio.userVolume,
        "createTime": datetime_to_unix(audio.createTime),
        "playCount": audio.playTimes,
        "story": story,
        "bgm": {
            "uuid": audio.bgm.uuid if audio.bgm else '',
            "bgmUrl": audio.bgm.url if audio.bgm else '',
            "bgmVolume": audio.bgmVolume if audio.bgm else '',
        },
        "publisher": {
            "uuid": audio.userUuid.uuid if audio.userUuid else '',
            "nickname": audio.userUuid.nickName if audio.userUuid else '',
            "avatar": audio.userUuid.avatar if audio.userUuid else '',
            "createTime": datetime_to_unix(audio.userUuid.createTime) if audio.userUuid else '',
        },
        "communication": {
            "isPraise": True if checkPraise else False,
            "praiseCount": audio.bauUuid.filter(type=1, status=0).count(),
            "isLike": True if checkLike else False,
            "likeCount": audio.bauUuid.filter(type=3, status=0).count(),
            "commentsCount": '',
        }
    }
    otheraudio = AudioStory.objects.exclude(uuid=uuid, isDelete=True).filter(userUuid__uuid=audio.userUuid.uuid)
    otheraudios = otheraudio.order_by("-createTime").all()
    total, otheraudios = page_index(otheraudios, page, pageCount)
    audioList = []
    for otheraudio in otheraudios:
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
        for tag in otheraudio.tags.all():
            tagList.append({
                'uuid': tag.uuid,
                'name': tag.name if tag.name else '',
                'icon': tag.icon if tag.icon else '',
            })
        audioList.append({
            "uuid": otheraudio.uuid,
            "duration": otheraudio.duration,
            "icon": otheraudio.bgIcon if otheraudio.bgIcon else '',
            "name": otheraudio.name if otheraudio.name else '',
            "createTime": datetime_to_unix(otheraudio.createTime),
            "tagList": tagList,
            "story": story,
        })

    return http_return(200, '成功',
                       {"total": total,
                        "list": audioList,
                        "audioStory": playDict, })


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
    banner = CycleBanner.objects.filter(startTime__lte=nowDatetime, endTime__gte=nowDatetime, isUsing=True,
                                        isDelete=False)
    # 按显示序号排序
    banner = banner.filter(location=0).order_by('orderNum')
    banners = banner.all()
    banList = []
    for banner in banners:
        banList.append({
            "uuid": banner.uuid,
            'name': banner.name if banner.name else '',
            'icon': banner.icon if banner.icon else '',
            'type': banner.type,
            'target': banner.target if banner.target else '',
        })
    return http_return(200, '成功', banList)


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
    evers = Module.objects.filter(type='MOD1', isDelete=False, audioUuid__audioStoryType=True).order_by(
        "orderNum").all()
    if evers:
        for ever in evers:
            everList.append({
                "uuid": ever.audioUuid.uuid,
                "name": ever.audioUuid.name if ever.audioUuid.name else '',
                "content": ever.audioUuid.remarks if ever.audioUuid.remarks else '',
                "icon": ever.audioUuid.bgIcon if ever.audioUuid.bgIcon else '',
                "type": '',
                "target": '',
            })
    # 抢先听
    firstList = []
    firsts = Module.objects.filter(type='MOD2', isDelete=False).order_by("orderNum").all()[:4]
    if firsts:
        for first in firsts:
            firstList.append({
                "uuid": first.audioUuid.uuid,
                "name": first.audioUuid.name if first.audioUuid.name else '',
                "icon": first.audioUuid.bgIcon if first.audioUuid.bgIcon else '',
                "content": first.audioUuid.remarks if first.audioUuid.remarks else '',
                "type": '',
                "target": '',
            })
    # 热门推荐
    hotList = []
    hots = Module.objects.filter(type='MOD3', isDelete=False).order_by("orderNum").all()[:4]
    if hots:
        for hot in hots:
            hotList.append({
                "uuid": hot.audioUuid.uuid,
                "name": hot.audioUuid.name if hot.audioUuid.name else '',
                "icon": hot.audioUuid.bgIcon if hot.audioUuid.bgIcon else '',
                "content": hot.audioUuid.remarks if hot.audioUuid.remarks else '',
                "type": '',
                "target": '',
            })
    # 猜你喜欢
    likeList = []
    audios = AudioStory.objects.exclude(checkStatus="checkFail").exclude(checkStatus="unCheck").filter(
        isDelete=False).order_by("-playTimes").all()[:6]
    if audios:
        for audio in audios:
            likeList.append({
                "uuid": audio.uuid,
                "name": audio.name if audio.name else '',
                "icon": audio.bgIcon if audio.bgIcon else '',
                "content": audio.remarks if audio.remarks else '',
                "type": '',
                "target": ''
            })
    return http_return(200, '成功',
                       {"dailyReadList": everList, "listenFirstList": firstList, "hotRecommdList": hotList,
                        "mayLikeList": likeList})


@check_identify
def index_more(request):
    """
    首页更多
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    type = int(data.get('type', ''))
    page = data.get('page', '')
    pageCount = data.get('pageCount', '')
    sort = data.get('sort', '')  # rank:最热 latest:最新
    # MOD1每日一读  MOD2抢先听  MOD3热门推荐 MOD4猜你喜欢
    if type in [1, 2, 3]:
        typeDict = {1: "MOD1", 2: "MOD2", 3: "MOD3"}
        audioStoryList = []
        module = Module.objects.filter(type=typeDict[type], isDelete=False)
        if type == '1':
            module = module.filter(audioUuid__audioStoryType=True)
        if sort == "latest":
            module = module.order_by("orderNum", '-createTime')
        elif sort == "rank":
            module = module.order_by("orderNum", '-audioUuid__playTimes')
        else:
            return http_return(400, '参数错误')
        modules = module.all()
        total, modules = page_index(modules, page, pageCount)
        if modules:
            for module in modules:
                story = None
                if module.audioUuid.audioStoryType:
                    story = {
                        "uuid": module.audioUuid.storyUuid.uuid if module.audioUuid.storyUuid else '',
                        "name": module.audioUuid.storyUuid.name if module.audioUuid.storyUuid else '',
                        "icon": module.audioUuid.storyUuid.faceIcon if module.audioUuid.storyUuid else '',
                        "content": module.audioUuid.storyUuid.content if module.audioUuid.storyUuid else '',
                        "intro": module.audioUuid.storyUuid.intro if module.audioUuid.storyUuid else ''
                    }
                tagList = []
                for tag in module.audioUuid.tags.all():
                    tagList.append({
                        'uuid': tag.uuid,
                        'name': tag.name if tag.name else '',
                        'icon': tag.icon if tag.icon else '',
                    })
                audioStoryList.append({
                    "uuid": module.audioUuid.uuid,
                    "name": module.audioUuid.name if module.audioUuid.name else '',
                    "icon": module.audioUuid.bgIcon if module.audioUuid.bgIcon else '',
                    "remarks": module.audioUuid.remarks if module.audioUuid.remarks else '',
                    "playCount": module.audioUuid.playTimes,
                    "createTime": datetime_to_unix(module.audioUuid.createTime),
                    "tagList": tagList,
                    "story": story,
                })
    elif type == 4:
        audioStoryList = []
        audio = AudioStory.objects.exclude(checkStatus="checkFail").exclude(checkStatus="unCheck").filter(
            isDelete=False)
        if sort == "latest":
            audios = audio.order_by('-createTime').all()
        elif sort == "rank":
            audios = audio.order_by('-playTimes').all()
        else:
            return http_return(400, '参数错误')
        total, audios = page_index(audios, page, pageCount)
        if audios:
            for audio in audios:
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
                        'icon': tag.icon if tag.icon else '',
                    })
                audioStoryList.append({
                    "uuid": audio.uuid,
                    "name": audio.name if audio.name else '',
                    "icon": audio.bgIcon if audio.bgIcon else '',
                    "remarks": audio.remarks if audio.remarks else '',
                    "playCount": audio.playTimes,
                    "createTime": datetime_to_unix(audio.createTime),
                    "tagList": tagList,
                    "story": story,
                })
    else:
        return http_return(400, '参数错误')
    return http_return(200, '成功', {"total": total, "list": audioStoryList})


@check_identify
def search_all(request):
    """
    搜索所有
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    keyword = data.get('keyword')
    selfUuid = data['_cache']['uuid']
    selfUser = User.objects.filter(uuid=selfUuid).first()
    if not selfUser:
        return http_return(400, '未获取到用户信息')
    if not keyword:
        return http_return(400, '参数错误')
    if not save_search(data):
        return http_return(400, '存储搜索记录失败')
    audio = AudioStory.objects.filter(checkStatus='check', isDelete=False)
    user = User.objects.filter(roles='normalUser')
    audio = audio.filter(name__contains=keyword).order_by("-createTime")
    user = user.filter(nickName__contains=keyword).order_by("-createTime")
    audioList = []
    for au in audio.all()[:6]:
        story = None
        if au.audioStoryType:
            story = {
                "uuid": au.storyUuid.uuid if au.storyUuid else '',
                "name": au.storyUuid.name if au.storyUuid else '',
                "icon": au.storyUuid.faceIcon if au.storyUuid else '',
                "content": au.storyUuid.content if au.storyUuid else '',
                "intro": au.storyUuid.intro if au.storyUuid else ''
            }
        audioList.append({
            "uuid": au.uuid,
            "icon": au.bgIcon if au.bgIcon else '',
            "name": au.name if au.name else '',
            "remarks": au.remarks if au.remarks else '',
            "story": story,
        })
    userList = []
    for u in user.all()[:6]:
        audioCount = u.useAudioUuid.filter(isDelete=False).count()
        followers = len(u.get_followers())
        userList.append({
            "uuid": u.uuid,
            "avatar": u.avatar if u.avatar else '',
            "nickname": u.nickName if u.nickName else '',
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
    keyword = data.get('keyword')
    page = data.get('page', '')
    pageCount = data.get('pageCount', '')
    selfUuid = data['_cache']['uuid']
    selfUser = User.objects.filter(uuid=selfUuid).first()
    if not selfUser:
        return http_return(400, '未获取到用户信息')
    if not keyword:
        return http_return(400, '参数错误')
    if not save_search(data):
        return http_return(400, '存储搜索记录失败')
    audio = AudioStory.objects.filter(checkStatus='check', isDelete=False)
    audio = audio.filter(Q(storyUuid__name__contains=keyword) | Q(name__contains=keyword)).order_by("-createTime")
    audios = audio.all()
    total, audios = page_index(audios, page, pageCount)
    audioList = []
    for au in audios:
        story = None
        if au.audioStoryType:
            story = {
                "uuid": au.storyUuid.uuid if au.storyUuid else '',
                "name": au.storyUuid.name if au.storyUuid else '',
                "icon": au.storyUuid.faceIcon if au.storyUuid else '',
                "content": au.storyUuid.content if au.storyUuid else '',
                "intro": au.storyUuid.intro if au.storyUuid else ''
            }
        audioList.append({
            "uuid": au.uuid,
            "icon": au.bgIcon if au.bgIcon else '',
            "name": au.name if au.name else '',
            "publisher": {
                "uuid": au.userUuid.uuid if au.userUuid else '',
                "nickname": au.userUuid.nickName if au.userUuid else '',
                "avatar": au.userUuid.avatar if au.userUuid else '',
                "createTime": datetime_to_unix(au.userUuid.createTime) if au.userUuid else '',
            },
            "duration": au.duration,
            "remarks": au.remarks,
            "story": story,
        })
    return http_return(200, '成功', {"list": audioList, "total": total})


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
    keyword = data.get('keyword')
    page = data.get('page', '')
    pageCount = data.get('pageCount', '')
    selfUuid = data['_cache']['uuid']
    selfUser = User.objects.filter(uuid=selfUuid).first()
    if not selfUser:
        return http_return(400, '未获取到用户信息')
    if not keyword:
        return http_return(400, '参数错误')
    if not save_search(data):
        return http_return(400, '存储搜索记录失败')
    user = User.objects.filter(roles='normalUser')
    users = user.filter(nickName__contains=keyword).order_by("-createTime").all()
    total, users = page_index(users, page, pageCount)
    userList = []
    for u in users:
        audioCount = u.useAudioUuid.filter(isDelete=False).count()
        followers = len(u.get_followers())
        userList.append({
            "uuid": u.uuid,
            "avatar": u.avatar if u.avatar else '',
            "nickname": u.nickName if u.nickName else '',
            "audioStoryCount": audioCount,
            "followersCount": followers,
        })
    return http_return(200, '成功', {"total": total, "list": userList})


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
    hots = HotSearch.objects.filter(isDelete=False).order_by("-isTop", "-searchNum").all()[:10]
    hotSearchList = []
    for hot in hots:
        hotSearchList.append(hot.keyword)
    hotSearch = ','.join(hotSearchList)
    return http_return(200, "成功", {"hotSearch": hotSearch})


@check_identify
def audiostory_category_detail(request):
    """
    首页分类显示
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    className = data.get('className', None)
    page = data.get('page', '')
    pageCount = data.get('pageCount', '')
    if not className or className not in ['绘本', '故事', '英语', '国学']:
        return http_return(400, '参数错误')
    audio = AudioStory.objects.exclude(checkStatus="checkFail").exclude(checkStatus="unCheck").filter(isDelete=False)
    audios = audio.filter(tags__name=className).all()
    total, audios = page_index(audios, page, pageCount)
    audioStoryList = []
    for audio in audios:
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
            "duration": audio.duration,
            "icon": audio.bgIcon if audio.bgIcon else '',
            "name": audio.name if audio.name else '',
            "palyCount": audio.playTimes,
            "createTime": datetime_to_unix(audio.createTime),
            "tagList": tagList,
            "story": story,
        })
    return http_return(200, '成功', {"total": total, "list": audioStoryList})


@check_identify
def index_category_list(request):
    """
    首页分类入口
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    tag = Tag.objects.filter(isDelete=False, isUsing=True)
    tags = tag.filter(code='SEARCHSORT', parent=None).order_by('sortNum').all()
    tagList = []
    for tag in tags:
        childrenList = []
        childTags = Tag.objects.filter(isDelete=False, isUsing=True, parent=tag).order_by('sortNum').all()
        for child in childTags:
            childrenList.append({
                "uuid": child.uuid,
                "name": child.name if child.name else '',
                "icon": child.icon if child.icon else '',
            })
        tagList.append({
            "uuid": tag.uuid,
            "name": tag.name if tag.name else '',
            "icon": tag.icon if tag.icon else '',
            "tagList": childrenList,
        })
    return http_return(200, '成功', tagList)


@check_identify
def index_category_result(request):
    """
    分类筛选结果
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    categoryStr = data.get('categoryStr', '')
    audio = AudioStory.objects.exclude(checkStatus="checkFail").exclude(checkStatus="unCheck").filter(isDelete=False)
    user = User.objects.filter(status='normal')
    if categoryStr:
        categoryList = categoryStr.split('*')
        for cate in categoryList:
            tagList = cate.split(',')
            audio = audio.filter(tags__uuid__in=tagList)
            user = user.filter(useAudioUuid__tags__uuid__in=tagList)
    audios = audio.order_by("-createTime").all()[:6]
    users = user.order_by('-updateTime').all()[:6]
    audioStoryList = []
    for audio in audios:
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
            "duration": audio.duration,
            "icon": audio.bgIcon if audio.bgIcon else '',
            "name": audio.name if audio.name else '',
            "palyCount": audio.playTimes,
            "createTime": datetime_to_unix(audio.createTime),
            "tagList": tagList,
            "story": story,
        })
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
    return http_return(200, '成功', {"audioStoryList": audioStoryList, "userList": userList})


@check_identify
def index_category_audiostory(request):
    """
    作品筛选结果
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    page = data.get('page', '')
    pageCount = data.get('pageCount', '')
    categoryStr = data.get('categoryStr', '')
    audio = AudioStory.objects.exclude(checkStatus="checkFail").exclude(checkStatus="unCheck").filter(isDelete=False)
    if categoryStr:
        categoryList = categoryStr.split('*')
        for cate in categoryList:
            tagList = cate.split(',')
            audio = audio.filter(tags__uuid__in=tagList)
    audios = audio.order_by("-createTime").all()
    total, audios = page_index(audios, page, pageCount)
    audioStoryList = []
    for audio in audios:
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
            "duration": audio.duration,
            "icon": audio.bgIcon if audio.bgIcon else '',
            "name": audio.name if audio.name else '',
            "palyCount": audio.playTimes,
            "createTime": datetime_to_unix(audio.createTime),
            "tagList": tagList,
            "story": story,
        })
    return http_return(200, '成功', {"list": audioStoryList, "total": total})


@check_identify
def index_category_user(request):
    """
    分类筛选结果
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    page = data.get('page', '')
    pageCount = data.get('pageCount', '')
    categoryStr = data.get('categoryStr', '')
    user = User.objects.filter(status='normal')
    if categoryStr:
        categoryList = categoryStr.split('*')
        for cate in categoryList:
            tagList = cate.split(',')
            user = user.filter(useAudioUuid__tags__uuid__in=tagList)
    users = user.order_by('-updateTime').all()
    total, users = page_index(users, page, pageCount)
    userList = []
    for u in users:
        audioCount = u.useAudioUuid.filter(isDelete=False).count()
        followers = len(u.get_followers())
        userList.append({
            "uuid": u.uuid,
            "avatar": u.avatar if u.avatar else '',
            "nickname": u.nickName if u.nickName else '',
            "audioStoryCount": audioCount,
            "followersCount": followers,
        })
    return http_return(200, '成功', {"total": total, "list": userList})


@check_identify
def audiostory_praise(request):
    """
    点赞/取消点赞 模板音频
    :param request:
    :return:
    """
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')
    if not uuid:
        return http_return(400, '参数错误')
    selfUuid = data['_cache']['uuid']
    behav = Behavior.objects.filter(userUuid__uuid=selfUuid, audioUuid__uuid=uuid, type=1).first()
    if behav:
        try:
            with transaction.atomic():
                behav.delete()
        except Exception as e:
            logging.error(str(e))
            return http_return(400, '操作失败')
    else:
        audio = AudioStory.objects.filter(uuid=uuid).first()
        if not audio:
            return http_return(400, '信息不存在')
        user = User.objects.filter(uuid=selfUuid).first()
        if not user:
            return http_return(400, '未获取到用户信息')
        try:
            with transaction.atomic():
                Behavior.objects.create(
                    uuid=get_uuid(),
                    userUuid=user,
                    audioUuid=audio,
                    type=1,
                )
        except Exception as e:
            logging.error(str(e))
            return http_return(400, '操作失败')
    return http_return(200, '操作成功')


@check_identify
def audiostory_like(request):
    """
    喜欢/取消喜欢作品
    :param request:
    :return:
    """
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')
    if not uuid:
        return http_return(400, '参数错误')
    selfUuid = data['_cache']['uuid']
    behav = Behavior.objects.filter(userUuid__uuid=selfUuid, audioUuid__uuid=uuid, type=3).first()
    if behav:
        try:
            with transaction.atomic():
                behav.delete()
        except Exception as e:
            logging.error(str(e))
            return http_return(400, '操作失败')
    else:
        audio = AudioStory.objects.filter(uuid=uuid).first()
        if not audio:
            return http_return(400, '信息不存在')
        user = User.objects.filter(uuid=selfUuid).first()
        if not user:
            return http_return(400, '未获取到用户信息')
        try:
            with transaction.atomic():
                Behavior.objects.create(
                    uuid=get_uuid(),
                    userUuid=user,
                    audioUuid=audio,
                    type=3,
                )
        except Exception as e:
            logging.error(str(e))
            return http_return(400, '操作失败')
    return http_return(200, '操作成功')


@check_identify
def activity_detail(request):
    """
    活动详情
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')
    if not uuid:
        return http_return(400, '参数错误')
    act = Activity.objects.filter(uuid=uuid).first()
    if not act:
        return http_return(400, '活动信息不存在')
    selfUuid = data['_cache']['uuid']
    user = User.objects.filter(uuid=selfUuid).first()
    activityInfo = {
        "uuid": act.uuid,
        "name": act.name,
        "intro": act.intro,
        "icon": act.icon,
        "startTime": datetime_to_unix(act.startTime),
        "endTime": datetime_to_unix(act.endTime),
    }
    # 返回参赛状态，如果参赛再返回排名
    status = False
    rank = None
    score = None
    game = GameInfo.objects.filter(userUuid__uuid=selfUuid, activityUuid__uuid=uuid).first()
    if game:
        status = True
        config = ActivityConfig.objects.filter(status=0).first()
        if not config:
            return http_return(400, '未获取到参数配置')
        praiseNum = config.praiseNum / 100
        playTimesNum = config.playTimesNum / 100
        games = GameInfo.objects.filter(activityUuid__uuid=uuid).all()
        games = sorted(games,
                       key=lambda x: praiseNum * x.audioUuid.bauUuid.filter(
                           type=1).count() + playTimesNum * x.audioUuid.playTimes,
                       reverse=True)
        rank = games.index(game) + 1
        score = praiseNum * game.audioUuid.bauUuid.filter(type=1).count() + playTimesNum * game.audioUuid.playTimes
    userInfo = {
        "uuid": user.uuid,
        "avatar": user.avatar if user.avatar else '',
        "nickname": user.nickName if user.nickName else '',
        "status": status,
        "rank": rank,
        "score": round(score, 1),
    }
    return http_return(200, '成功', {"activityInfo": activityInfo, "userInfo": userInfo})


@check_identify
def activity_rank(request):
    """
    活动排行
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
    act = Activity.objects.filter(uuid=uuid).first()
    if not act:
        return http_return(400, '活动信息不存在')
    config = ActivityConfig.objects.filter(status=0).first()
    if not config:
        return http_return(400, '未获取到参数配置')
    praiseNum = config.praiseNum / 100
    playTimesNum = config.playTimesNum / 100
    games = GameInfo.objects.filter(activityUuid__uuid=uuid).all()
    games = sorted(games,
                   key=lambda x: praiseNum * x.audioUuid.bauUuid.filter(
                       type=1).count() + playTimesNum * x.audioUuid.playTimes,
                   reverse=True)
    total, games = page_index(games, page, pageCount)
    activityRankList = []
    for game in games:
        score = praiseNum * game.audioUuid.bauUuid.filter(type=1).count() + playTimesNum * game.audioUuid.playTimes
        activityRankList.append({
            "publisher": {
                "uuid": game.userUuid.uuid if game.userUuid else '',
                "nickname": game.userUuid.nickName if game.userUuid else '',
                "avatar": game.userUuid.avatar if game.userUuid else '',
            },
            "audio": {
                "uuid": game.audioUuid.uuid if game.audioUuid else '',
                "name": game.audioUuid.name if game.audioUuid else '',
            },
            "score": round(score, 1),
        })
    return http_return(200, '成功', {"total": total, "list": activityRankList})


@check_identify
def activity_audiostory_list(request):
    """
    用户可参赛作品列表
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
    activityUuidList = []
    games = GameInfo.objects.filter(activityUuid__uuid=uuid).all()
    for game in games:
        activityUuidList.append(game.audioUuid.uuid)
    audio = AudioStory.objects.exclude(checkStatus="checkFail").exclude(checkStatus="unCheck").filter(
        userUuid__uuid=data['_cache']['uuid'], isDelete=False)
    # 只能使用活动时间内录制的作品参赛
    activity = Activity.objects.filter(uuid=uuid).first()
    if not activity:
        return http_return(400, '活动信息不存在')
    startTime = activity.startTime
    endTime = activity.endTime
    audio = audio.filter(createTime__gte=startTime, createTime__lte=endTime)
    audios = audio.exclude(uuid__in=activityUuidList).order_by("-updateTime").all()
    total, audios = page_index(audios, page, pageCount)
    audioStoryList = []
    for audio in audios:
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
            "duration": audio.duration,
            "icon": audio.bgIcon if audio.bgIcon else '',
            "name": audio.name if audio.name else '',
            "palyCount": audio.playTimes,
            "createTime": datetime_to_unix(audio.createTime),
            "tagList": tagList,
            "story": story,
        })
    return http_return(200, '成功', {"list": audioStoryList, "total": total})


@check_identify
def activity_join(request):
    """
    参与活动
    :param request:
    :return:
    """
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    activityUuid = data.get('activityUuid', '')
    audioStoryUuid = data.get('audioStoryUuid', '')
    if not all([audioStoryUuid, activityUuid]):
        return http_return(400, '参数错误')
    activity = Activity.objects.filter(uuid=activityUuid).first()
    if not activity:
        return http_return(400, '活动信息不存在')
    # 校验作品是否可以参加比赛
    checkGame = GameInfo.objects.filter(audioUuid__uuid=audioStoryUuid).first()
    if checkGame:
        return http_return(400, '作品已参与过活动')
    audioStory = AudioStory.objects.filter(uuid=audioStoryUuid).first()
    if not audioStory:
        return http_return(400, '作品信息不存在')
    if audioStory.createTime <= activity.startTime or audioStory.createTime >= activity.endTime:
        return http_return(400, '参赛作品录制时间不在比赛时间内')
    selfUuid = data['_cache']['uuid']
    user = User.objects.filter(uuid=selfUuid).first()
    if not user:
        return http_return(400, '未获取到用户信息')
    checkUser = GameInfo.objects.filter(activityUuid__uuid=activityUuid, userUuid__uuid=selfUuid).first()
    if checkUser:
        return http_return(400, '你已参与过该活动')
    try:
        GameInfo.objects.create(
            uuid=get_uuid(),
            userUuid=user,
            activityUuid=activity,
            audioUuid=audioStory,
        )
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '参赛失败')
    return http_return(200, '参赛成功')


@check_identify
def personal_index(request):
    """
    个人中心
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    selfUuid = data['_cache']['uuid']
    user = User.objects.filter(uuid=selfUuid).first()
    userInfo = {
        "uuid": user.uuid,
        "nickname": user.nickName if user.nickName else '',
        "city": user.city if user.city else '',
        "avatar": user.avatar if user.avatar else '',
        "createTime": datetime_to_unix(user.createTime),
        "intro": user.intro,
    }
    return http_return(200, '成功', userInfo)


@check_identify
def personal_audiostory(request):
    """
    我的作品
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    page = data.get('page', '')
    pageCount = data.get('pageCount', '')
    selfUuid = data['_cache']['uuid']
    audio = AudioStory.objects.filter(isDelete=False, userUuid__uuid=selfUuid)
    audios = audio.order_by("-updateTime").all()
    total, audios = page_index(audios, page, pageCount)
    audioStoryList = []
    for audio in audios:
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
            "duration": audio.duration,
            "icon": audio.bgIcon if audio.bgIcon else '',
            "name": audio.name if audio.name else '',
            "palyCount": audio.playTimes,
            "createTime": datetime_to_unix(audio.createTime),
            "tagList": tagList,
            "story": story,
        })
    return http_return(200, '成功', {"list": audioStoryList, "total": total})


@check_identify
def personal_history_list(request):
    """
    播放记录
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    page = data.get('page', '')
    pageCount = data.get('pageCount', '')
    selfUuid = data['_cache']['uuid']
    behav = Behavior.objects.filter(userUuid__uuid=selfUuid, type=4)
    behavs = behav.order_by("-updateTime").all()
    total, behavs = page_index(behavs, page, pageCount)
    palyHistoryList = []
    for behav in behavs:
        audio = behav.audioUuid
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
        audio = {
            "uuid": audio.uuid,
            "duration": audio.duration,
            "icon": audio.bgIcon if audio.bgIcon else '',
            "name": audio.name if audio.name else '',
            "palyCount": audio.playTimes,
            "createTime": datetime_to_unix(audio.createTime),
            "tagList": tagList,
            "story": story,
        }
        palyHistoryList.append({
            "uuid": behav.uuid,
            "audio": audio,
        })
    return http_return(200, '成功', {"list": palyHistoryList, "total": total})


@check_identify
def personal_history_del(request):
    """
    清空聊天记录
    :param request:
    :return:
    """
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    historyUuidList = data.get('historyUuidList', '')
    try:
        Behavior.objects.filter(uuid__in=historyUuidList).delete()
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '清空失败')
    return http_return(200, '清空成功')


@check_identify
def personal_change(request):
    """
    修改个人资料
    :param request:
    :return:
    """
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    avatar = data.get('avatar', '')
    nickname = data.get('nickname', '')
    intro = data.get('intro', '')
    city = data.get('city', '')
    update_data = {}
    if avatar:
        update_data['avatar'] = avatar
    if nickname:
        update_data['nickName'] = nickname
    if intro:
        update_data['intro'] = intro
    if city:
        update_data['city'] = city
    selfUuid = data['_cache']['uuid']
    user = User.objects.filter(uuid=selfUuid)
    try:
        update_data['updateTime'] = datetime.datetime.now()
        user.update(**update_data)
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '修改失败')
    return http_return(200, '修改成功')


@check_identify
def feedback_add(request):
    """
    反馈信息
    :param request:
    :return:
    """
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    type = data.get('type', '')
    content = data.get('content', '')
    iconList = data.get('iconList', '')
    tel = data.get('tel', '')
    if not all([type, content]):
        return http_return(400, '参数错误')
    selfUuid = data['_cache']['uuid']
    user = User.objects.filter(uuid=selfUuid).first()
    if not user:
        return http_return(400, '登录已过期')
    try:
        with transaction.atomic():
            feedback = Feedback(
                uuid=get_uuid(),
                type=type,
                content=content,
                icon=','.join(iconList),
                tel=tel,
                userUuid=user
            )
            feedback.save()
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '反馈失败')
    return http_return(200, '反馈成功')


@check_identify
def feedback_reply_list(request):
    """
    反馈信息
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    selfUuid = data['_cache']['uuid']
    feed = Feedback.objects.filter(userUuid__uuid=selfUuid, status=1)
    feeds = feed.order_by("-updateTime").all()
    feedbackList = []
    for feed in feeds:
        feedbackList.append({
            "uuid": feed.uuid,
            "type": feed.type if feed.type else '',
            "content": feed.content if feed.content else '',
            "reply": feed.replyInfo if feed.replyInfo else '',
            "updateTime": datetime_to_unix(feed.updateTime),
            "isRead": feed.isRead,
        })
    return http_return(200, '成功', feedbackList)


@check_identify
def feedback_reply_info(request):
    """
    反馈信息
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')
    feed = Feedback.objects.filter(uuid=uuid).first()
    try:
        with transaction.atomic():
            feed.isRead = True
            feed.save()
    except Exception as e:
        logging.error(str(e))
        print(str(e))
        return http_return(400, '查看失败')
    replyInfo = {
        "uuid": feed.uuid,
        "type": feed.type if feed.type else '',
        "content": feed.content if feed.content else '',
        "icon": feed.icon.split(',') if feed.icon else [],
        "reply": feed.replyInfo if feed.replyInfo else '',
        "createTime": datetime_to_unix(feed.createTime),
        "updateTime": datetime_to_unix(feed.updateTime),
    }
    return http_return(200, '成功', replyInfo)


def advertising_list(request):
    """
    进入弹屏
    :param request:
    :return:
    """
    if request.method == "POST":
        return http_return(400, '请求方式错误')
    nowDatetime = datetime.datetime.now()
    adv = Ad.objects.filter(endTime__gte=nowDatetime, startTime__lte=nowDatetime, isDelete=False)
    adv = adv.order_by("orderNum", "-createTime").first()
    advobj = {
        "uuid": adv.uuid,
        "name": adv.name,
        "icon": adv.icon,
        "type": adv.type,
        "target": adv.target,
    }
    return http_return(200, '成功', advobj)
