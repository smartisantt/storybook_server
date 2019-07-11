#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# Create your views here.
from django.db.models import Q

from api.ssoSMS.sms import send_sms
from api.test import update_history_data
from common.common import *
from api.apiCommon import *
from common.mixFileAPI import MixAudio
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
        story = story.filter(isRecommd=False).order_by("isTop", "-updateTime")
    elif sort == "rank":
        story = story.order_by("-recordNum")
    elif sort == "recommended":  # 推荐算法
        story = story.filter(isRecommd=True).order_by("isTop", "-updateTime")
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


@check_identify
@forbbiden_say
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
        audioStoryType = True
        story = Story.objects.filter(uuid=storyUuid).first()
        if not story:
            return http_return(400, '模板信息不存在')
        # 更新录制次数
        try:
            with transaction.atomic():
                story.recordNum += 1
                story.save()
        except Exception as e:
            logging.error(str(e))
            return http_return(400, '更新录制次数失败')
    bgm = None
    if bgmUuid:
        bgm = Bgm.objects.filter(uuid=bgmUuid).first()
    if not all([audioUrl, audioVolume, storyTagUuidList, audioDuration, name, icon]):
        return http_return(400, '参数错误')
    if type not in [0, 1]:
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
    # 记录历史
    selfUuid = data['_cache']['uuid']
    selfUser = User.objects.filter(uuid=selfUuid).first()
    audio = AudioStory.objects.filter(uuid=uuid).first()
    try:
        with transaction.atomic():
            Behavior.objects.create(
                uuid=get_uuid(),
                userUuid=selfUser,
                audioUuid=audio,
                type=5,
            )
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '保存记录失败')

    # 提交音频合并请求
    mix = MixAudio()
    mix.audio_product(uuid)

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
    type = data.get('type', '')
    selfUuid = data['_cache']['uuid']
    if selfUuid == uuid:
        return http_return(400, '不能自己关注自己')
    friend = FriendShip.objects.filter(follows__uuid=uuid, followers__uuid=selfUuid).first()
    if type and int(type) == 1:
        if friend:
            try:
                with transaction.atomic():
                    friend.delete()
            except Exception as e:
                logging.error(str(e))
                return (400, '取消关注失败')
        return http_return(200, '取消关注成功')
    else:
        if not friend:
            selfUser = User.objects.filter(uuid=selfUuid).first()
            user = User.objects.filter(uuid=uuid).first()
            try:
                with transaction.atomic():
                    FriendShip.objects.create(
                        uuid=get_uuid(),
                        follows=user,
                        followers=selfUser,
                    )
            except Exception as e:
                logging.error(str(e))
                return http_return(400, '关注失败')
        return http_return(200, '关注成功')


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
        users = []
        for f in user.followers.all():
            users.append(f.follows)
    elif type == 'followers':
        users = []
        for f in user.follows.all():
            users.append(f.followers)
    else:
        return http_return(400, '参数错误')
    total, users = page_index(users, page, pageCount)
    userList = userList_format(users)
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
    audio = AudioStory.objects.filter(Q(checkStatus="check") | Q(checkStatus="exemption")).filter(isDelete=False)
    if audioStoryType:
        audio = audio.filter(audioStoryType=audioStoryType)
    audios = audio.order_by('-createTime').all()
    total, audios = page_index(audios, page, pageCount)
    audioList = audioList_format(audios, data)
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
    # 更新连续阅读天数
    readDate = selfUser.readDate
    today = datetime.date.today()
    if readDate:
        if today - readDate == datetime.timedelta(days=1):
            selfUser.readDays = today
            selfUser.readDays += 1
        elif today - readDate > datetime.timedelta(days=1):
            selfUser.readDays = today
            selfUser.readDays = 1
    else:
        selfUser.readDays = 1
    try:
        with transaction.atomic():
            selfUser.save()
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '更新阅读天数失败')
    audios = []
    audios.append(audio)
    playDict = audioList_format(audios, data)[0]
    return http_return(200, '成功', playDict)


@check_identify
def audio_other(request):
    """
    其他作品
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')
    page = data.get('page', '')
    pageCount = data.get('pageCount', '')
    audio = AudioStory.objects.filter(uuid=uuid).first()
    if not audio:
        return http_return(400, '作品信息不存在')
    otheraudio = AudioStory.objects.filter(Q(checkStatus="check") | Q(checkStatus="exemption")).filter(
        isDelete=False).exclude(uuid=uuid).filter(userUuid__uuid=audio.userUuid.uuid, isDelete=False)
    otheraudios = otheraudio.order_by("-updateTime").all()
    total, otheraudios = page_index(otheraudios, page, pageCount)
    audioList = audioList_format(otheraudios, data)
    return http_return(200, '成功', {"total": total, "list": audioList})


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
    evers = Module.objects.filter(type='MOD1', isDelete=False, audioUuid__audioStoryType=True,
                                  audioUuid__isDelete=False).order_by(
        "orderNum").all()
    if evers:
        for ever in evers:
            everList.append({
                "uuid": ever.audioUuid.uuid,
                "name": ever.audioUuid.name if ever.audioUuid.name else '',
                "content": ever.audioUuid.remarks if ever.audioUuid.remarks else '',
                "icon": ever.audioUuid.bgIcon if ever.audioUuid.bgIcon else '',
                "type": 2,
                "target": ever.audioUuid.uuid,
            })
    # 抢先听
    firstList = []
    firsts = Module.objects.filter(type='MOD2', isDelete=False, audioUuid__isDelete=False).order_by("orderNum").all()[
             :6]
    if firsts:
        for first in firsts:
            firstList.append({
                "uuid": first.audioUuid.uuid,
                "name": first.audioUuid.name if first.audioUuid.name else '',
                "icon": first.audioUuid.bgIcon if first.audioUuid.bgIcon else '',
                "content": first.audioUuid.remarks if first.audioUuid.remarks else '',
                "type": 2,
                "target": first.audioUuid.uuid,
            })
    # 热门推荐
    hotList = []
    hots = Module.objects.filter(type='MOD3', isDelete=False, audioUuid__isDelete=False).order_by("orderNum").all()[:4]
    if hots:
        for hot in hots:
            hotList.append({
                "uuid": hot.audioUuid.uuid,
                "name": hot.audioUuid.name if hot.audioUuid.name else '',
                "icon": hot.audioUuid.bgIcon if hot.audioUuid.bgIcon else '',
                "content": hot.audioUuid.remarks if hot.audioUuid.remarks else '',
                "type": 2,
                "target": hot.audioUuid.uuid,
            })
    # 猜你喜欢
    likeList = []
    audios = AudioStory.objects.filter(Q(checkStatus="check") | Q(checkStatus="exemption")).filter(
        isDelete=False).filter(
        isDelete=False).order_by("-playTimes").all()[:6]
    if audios:
        for audio in audios:
            likeList.append({
                "uuid": audio.uuid,
                "name": audio.name if audio.name else '',
                "icon": audio.bgIcon if audio.bgIcon else '',
                "content": audio.remarks if audio.remarks else '',
                "type": 2,
                "target": audio.uuid,
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
    audio = AudioStory.objects.filter(Q(checkStatus="check") | Q(checkStatus="exemption")).filter(isDelete=False)
    if type in [1, 2, 3]:
        typeDict = {1: "MOD1", 2: "MOD2", 3: "MOD3"}
        audio = audio.filter(moduleAudioUuid__type=typeDict[type], isDelete=False)
        if type == 1:
            audio = audio.filter(audioStoryType=True)
    elif type == 4:
        pass
    elif type in [5, 6, 7, 8]:
        classList = {5: "绘本", 6: "故事", 7: "英语", 8: "国学"}
        audio = audio.filter(tags__name=classList[type])
    else:
        return http_return(400, '参数错误')
    if sort == "latest":
        audio = audio.order_by('-createTime')
    elif sort == "rank":
        audio = audio.order_by('-playTimes')
    else:
        return http_return(400, '参数错误')
    audios = audio.all()
    total, audios = page_index(audios, page, pageCount)
    audioStoryList = audioList_format(audios, data)
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
    audio = AudioStory.objects.filter(Q(checkStatus="check") | Q(checkStatus="exemption")).filter(isDelete=False)
    user = User.objects.filter(roles='normalUser')
    audios = audio.filter(name__contains=keyword).order_by("-updateTime").all()[:6]
    users = user.filter(nickName__contains=keyword).order_by("-updateTime").all()[:6]
    searchAudioStory, searchUser = result_all(audios, users, data)
    return http_return(200, '成功', {"searchAudioStory": searchAudioStory, "searchUser": searchUser})


@check_identify
def search_each(request):
    """
    搜索单类
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    keyword = data.get('keyword')
    filterValue = data.get('filterValue', '')  # rank latest followersCount audioStoryCount
    type = data.get('type', '')  # audioStory publisher
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
    if type == "audioStory":
        audio = AudioStory.objects.filter(Q(checkStatus="check") | Q(checkStatus="exemption")).filter(isDelete=False)
        audio = audio.filter(Q(storyUuid__name__contains=keyword) | Q(name__contains=keyword))
        if filterValue == 'rank':
            audio = audio.order_by("-playTimes")
        else:
            audio = audio.order_by("-updateTime")
        audios = audio.all()
        total, audios = page_index(audios, page, pageCount)
        resultList = audioList_format(audios, data)
        filter = [
            {"label": "最多播放", "value": "rank"},
            {"label": "最新上传", "value": "latest"}
        ]
    elif type == "publisher":
        user = User.objects.filter(roles='normalUser')
        users = user.filter(nickName__contains=keyword).all()
        if filterValue == 'audioStoryCount':
            users = sorted(user, key=lambda x: x.useAudioUuid.filter(isDelete=False).count(), reverse=True)
        else:
            users = sorted(users, key=lambda x: FriendShip.objects.filter(follows__uuid=x.uuid).count(), reverse=True)
        total, users = page_index(users, page, pageCount)
        resultList = userList_format(users)
        filter = [
            {"label": "最多粉丝", "value": "followersCount"},
            {"label": "最多音频", "value": "audioStoyrCount"}
        ]
    else:
        return http_return(400, '参数错误')
    return http_return(200, '成功', {"list": resultList, "total": total, "filter": filter})


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
    hots = HotSearch.objects.filter(isDelete=False).order_by("-isTop", "-searchNum").values_list('keyword', flat=True)
    resStr = ','.join(list(hots)[:10])
    return http_return(200, "成功", resStr)


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
    keyword = data.get('keyword', '')
    audio = AudioStory.objects.filter(Q(checkStatus="check") | Q(checkStatus="exemption")).filter(isDelete=False)
    user = User.objects.filter(status='normal')
    if keyword:
        categoryList = keyword.split('*')
        for cate in categoryList:
            tagList = cate.split(',')
            audio = audio.filter(tags__uuid__in=tagList)
            user = user.filter(useAudioUuid__tags__uuid__in=tagList)
    audios = audio.order_by("-updateTime").all()[:6]
    users = user.order_by('-updateTime').all()[:6]
    searchAudioStory, searchUser = result_all(audios, users, data)
    return http_return(200, '成功', {"searchAudioStory": searchAudioStory, "searchUser": searchUser})


@check_identify
def index_category_each(request):
    """
    作品筛选结果
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    type = data.get('type', '')  # audioStory publisher
    keyword = data.get('keyword', '')
    filterValue = data.get('filterValue', '')
    page = data.get('page', '')
    pageCount = data.get('pageCount', '')
    selfUuid = data['_cache']['uuid']
    selfUser = User.objects.filter(uuid=selfUuid).first()
    if not selfUser:
        return http_return(400, '未获取到用户信息')
    if type == "audioStory":
        audio = AudioStory.objects.filter(Q(checkStatus="check") | Q(checkStatus="exemption")).filter(isDelete=False)
        if keyword:
            categoryList = keyword.split('*')
            for cate in categoryList:
                tagList = cate.split(',')
                audio = audio.filter(tags__uuid__in=tagList)
        if filterValue == 'rank':
            audio = audio.order_by("-playTimes")
        else:
            audio = audio.order_by("-updateTime")
        audios = audio.all()
        total, audios = page_index(audios, page, pageCount)
        resultList = audioList_format(audios, data)
        filter = [
            {"label": "最多播放", "value": "rank"},
            {"label": "最新上传", "value": "latest"}
        ]
    elif type == "publisher":
        user = User.objects.filter(status='normal')
        if keyword:
            categoryList = keyword.split('*')
            for cate in categoryList:
                tagList = cate.split(',')
                user = user.filter(useAudioUuid__tags__uuid__in=tagList)
        users = user.order_by('-updateTime').all()
        if filterValue == 'audioStoryCount':
            users = sorted(user, key=lambda x: x.useAudioUuid.filter(isDelete=False).count(), reverse=True)
        else:
            users = sorted(users, key=lambda x: FriendShip.objects.filter(follows__uuid=x.uuid).count(), reverse=True)
        total, users = page_index(users, page, pageCount)
        resultList = userList_format(users)
        filter = [
            {"label": "最多粉丝", "value": "followersCount"},
            {"label": "最多音频", "value": "audioStoyrCount"}
        ]
    else:
        return http_return(400, '参数错误')
    return http_return(200, '成功', {"list": resultList, "total": total, "filter": filter})


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
    type = data.get('type', '')
    if not uuid:
        return http_return(400, '参数错误')
    selfUuid = data['_cache']['uuid']
    behav = Behavior.objects.filter(userUuid__uuid=selfUuid, audioUuid__uuid=uuid, type=1).first()
    if type and int(type) == 1:
        if behav:
            try:
                with transaction.atomic():
                    behav.delete()
            except Exception as e:
                logging.error(str(e))
                return http_return(400, '取消点赞失败')
        return http_return(200, '取消点赞成功')
    else:
        if not behav:
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
                return http_return(400, '点赞失败')
        return http_return(200, '点赞成功')


@check_identify
def audiostory_collection(request):
    """
    喜欢/取消喜欢作品
    :param request:
    :return:
    """
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')
    type = data.get('type', '')
    if not uuid:
        return http_return(400, '参数错误')
    selfUuid = data['_cache']['uuid']
    behav = Behavior.objects.filter(userUuid__uuid=selfUuid, audioUuid__uuid=uuid, type=3).first()
    if type and int(type) == 1:
        if behav:
            try:
                with transaction.atomic():
                    behav.delete()
            except Exception as e:
                logging.error(str(e))
                return http_return(400, '取消收藏失败')
        return http_return(200, '取消收藏成功')
    else:
        if not behav:
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
                return http_return(400, '收藏失败')
        return http_return(200, '收藏成功')


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
        "score": score,
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
            "score": score,
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
    audio = AudioStory.objects.filter(Q(checkStatus="check") | Q(checkStatus="exemption")).filter(
        isDelete=False).filter(
        userUuid__uuid=data['_cache']['uuid'])
    # 只能使用活动时间内录制的作品参赛
    activity = Activity.objects.filter(uuid=uuid).first()
    if not activity:
        return http_return(400, '活动信息不存在')
    startTime = activity.startTime
    endTime = activity.endTime
    audio = audio.filter(createTime__gte=startTime, createTime__lte=endTime)
    audios = audio.exclude(uuid__in=activityUuidList).order_by("-updateTime").all()
    total, audios = page_index(audios, page, pageCount)
    audioStoryList = audioList_format(audio, data)
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
    uuid = data.get('uuid', '')
    selfUuid = data['_cache'].get('uuid', '')
    if not selfUuid:
        return http_return(401, '登录过期')
    follow = False
    if uuid:
        follow = FriendShip.objects.filter(followers__uuid=selfUuid, follows__uuid=uuid).first()
        selfUuid = uuid
    user = User.objects.filter(uuid=selfUuid).first()
    userDict = {
        "uuid": user.uuid,
        "nickname": user.nickName if user.nickName else '',
        "avatar": user.avatar if user.avatar else '',
        "id": user.id,
        "city": user.city if user.city else '',
        "isFollow": True if follow else False,
        "intro": user.intro if user.intro else '',
        "createTime": datetime_to_unix(user.createTime),
        "followersCount": FriendShip.objects.filter(follows__uuid=uuid).count(),
        "followsCount": FriendShip.objects.filter(followers__uuid=uuid).count()
    }
    return http_return(200, '成功', userDict)


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
    uuid = data.get('uuid', '')
    page = data.get('page', '')
    pageCount = data.get('pageCount', '')
    selfUuid = data['_cache']['uuid']
    if uuid:
        selfUuid = uuid
    audio = AudioStory.objects.filter(Q(checkStatus="check") | Q(checkStatus="exemption")).filter(
        isDelete=False).filter(userUuid__uuid=selfUuid)
    audios = audio.order_by("-updateTime").all()
    total, audios = page_index(audios, page, pageCount)
    audioStoryList = audioList_format(audios, data)
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
    uuid = data.get('uuid', '')
    page = data.get('page', '')
    pageCount = data.get('pageCount', '')
    selfUuid = data['_cache']['uuid']
    if uuid:
        selfUuid = uuid
    behav = Behavior.objects.filter(userUuid__uuid=selfUuid, type=4)
    behavs = behav.order_by("audioUuid").distinct().order_by("-updateTime").all()
    total, behavs = page_index(behavs, page, pageCount)
    palyHistoryList = []
    for behav in behavs:
        audioStory = None
        if behav.audioUuid:
            audio = behav.audioUuid
            audios = []
            audios.append(audio)
            audioStory = audioList_format(audios, data)[0]
        palyHistoryList.append({
            "uuid": behav.uuid,
            "audioStory": audioStory,
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
    if not historyUuidList:
        return http_return(400, '参数错误')
    try:
        with transaction.atomic():
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
        if len(nickname) < 2 or len(nickname) > 10:
            return http_return(400, '用户名长度为2-10位,请重新输入')
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


@check_identify
def help_list(request):
    """
    帮助手册列表
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    helpList = []
    helpList.append({
        "title": '绘童阅读规则及APP操作流程',
        "target": 'http://123456789.html'
    })
    return http_return(200, '成功', helpList)


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


@check_identify
def audio_other_version(request):
    """
    其他主播版本
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')
    page = data.get('page', '')
    pageCount = data.get('pageCount', '')
    audio = AudioStory.objects.filter(uuid=uuid).first()
    if not audio:
        return http_return(400, '模板音频不存在')
    if not audio.audioStoryType:
        return http_return(400, '自由录制作品没有其他主播版本')
    otheraudio = AudioStory.objects.filter(Q(checkStatus="check") | Q(checkStatus="exemption")).filter(
        isDelete=False).filter(storyUuid__uuid=audio.storyUuid.uuid)
    otheraudios = otheraudio.order_by("-updateTime").all()
    total, otheraudios = page_index(otheraudios, page, pageCount)
    audioList = audioList_format(otheraudios, data)
    return http_return(200, '成功', {"total": total, "list": audioList})


@check_identify
def recording_stroy_recent(request):
    """
    最近录制
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')
    page = data.get('page', '')
    pageCount = data.get('pageCount', '')
    selfUuid = data['_cache']['uuid']
    if uuid:
        selfUuid = uuid
    behav = Behavior.objects.filter(userUuid__uuid=selfUuid, type=5)
    behavs = behav.order_by("-updateTime").all()
    total, behavs = page_index(behavs, page, pageCount)
    audios = []
    for behav in behavs:
        audios.append(behav.audioUuid)
    audioStoryList = audioList_format(audios, data)
    return http_return(200, '成功', {"list": audioStoryList, "total": total})


@check_identify
def search_word_like(request):
    """
    模糊匹配参数
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    keyword = data.get('keyword', '')
    user = User.objects.filter(nickName__contains=keyword).values_list('nickName', flat=True).distinct()
    audio = AudioStory.objects.filter(name__contains=keyword).values_list('name', flat=True).distinct()
    resStr = ','.join(list(user)[:5] + list(audio)[:5])
    return http_return(200, '成功', resStr)


@check_identify
def logout(request):
    """
    退出登录
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    selfUser = User.objects.filter(uuid=data['_cache']['uuid']).first()
    if selfUser:
        token = request.META.get('HTTP_TOKEN')
        caches['api'].delete(token)
        return http_return(200, '退出登录成功')
    return http_return(400, '退出登录失败')


@check_identify
def book_list(request):
    """
    书架列表
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    selfUuid = data['_cache']['uuid']
    selfUser = User.objects.filter(uuid=selfUuid).first()
    if not selfUser:
        return http_return(400, '未获取到用户信息')
    playCount = Behavior.objects.filter(userUuid__uuid=selfUuid, type=4).values('userUuid').distinct().count()
    collectionBehav = Behavior.objects.filter(userUuid__uuid=selfUuid, type=3).order_by("-updateTime")
    collAudios = []
    for coll in collectionBehav.all()[:6]:
        collAudios.append(coll.audioUuid)
    collectionList = audioList_format(collAudios, data)

    historyBehav = Behavior.objects.filter(userUuid__uuid=selfUuid, type=4).order_by(
        "audioUuid").distinct()
    historyAudios = []
    for his in historyBehav.order_by("updateTime").all()[:6]:
        historyAudios.append(his.audioUuid)
    historyList = audioList_format(historyAudios, data)
    infoData = {
        "readDays": selfUser.readDays,
        "readCount": playCount,
        "collectionList": collectionList,
        "historyList": historyList,
    }
    return http_return(200, '成功', infoData)


@check_identify
def collection_more(request):
    """
    更多收藏
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    page = data.get('page', '')
    pageCount = data.get('pageCount', '')
    selfUuid = data['_cache']['uuid']
    collectionBehav = Behavior.objects.filter(userUuid__uuid=selfUuid, type=3).order_by("-updateTime")
    collAudios = []
    for coll in collectionBehav.all()[:6]:
        collAudios.append(coll.audioUuid)
    total, audios = page_index(collAudios, page, pageCount)
    audioStoryList = audioList_format(audios, data)
    return http_return(200, '成功', {"total": total, "list": audioStoryList})
