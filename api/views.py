#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# Create your views here.
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
    story = TemplateStory.objects.exclude(status="destroy")
    if sort == "latest":
        story = story.filter(isRecommd=False).order_by("-isTop", "-createTime")
    elif sort == "rank":
        story = story.order_by("-recordNum")
    elif sort == "recommended":  # 推荐算法
        story = story.filter(isRecommd=True).order_by("-isTop", "-createTime")
    stories = story.all()
    total, stories = page_index(stories, page, pageCount)
    storyList = []
    for st in stories:
        storyList.append({
            "uuid": st.uuid,
            "title": st.title,
            "mediaUrl": st.listUrl,
            "recordNum": st.recordNum,
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
    banner = Viewpager.objects.filter(startTime__lte=nowDatetime, endTime__gte=nowDatetime, isUsing=True)
    # 按显示序号排序
    banner = banner.filter(isUsing=True, location=1).order_by('orderNum')
    banners = banner.all()
    banList = []
    for banner in banners:
        banList.append({
            'title': banner.title,
            'mediaUrl': banner.mediaUrl,
            'jumpType': banner.jumpType,
            'targetUuid': banner.targetUuid,
        })
    total = len(banners)
    return http_return(200, '成功', {"total": total, "banList": banList})


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
    story = TemplateStory.objects.filter(uuid=uuid, status="normal").first()
    if not story:
        return http_return(400, '模板故事不存在')
    d = {
        "uuid": story.uuid,
        "title": story.title if story.title else None,
        "conten": story.content if story.content else None,
        "mediaUrl": story.faceUrl if story.faceUrl else None
    }
    return http_return(200, '成功', {"detail": d})


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
    bgm = Bgm.objects.filter(isUsing=True).order_by('sortNum')
    bgms = bgm.all()
    total, bgms = page_index(bgms, page, pageCount)
    bgmList = []
    for bg in bgms:
        bgmList.append({
            "uuid": bg.uuid,
            "name": bg.name,
            "duration": bg.bgmTime,
            "mediaUrl": bg.mediaUrl,
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
    voiceUrl = data.get('voiceUrl', '')
    voiceVolume = data.get('voiceVolume', '')
    bgmUuid = data.get('bgmUuid', '')
    bgmVolume = data.get('bgmVolume', '')
    bgUrl = data.get('bgUrl', '')
    feeling = data.get('feeling', '')
    recordType = data.get('recordType', '')
    typeUuidList = data.get('typeUuidList', '')
    worksTime = data.get('worksTime', '')
    title = None
    worksType = True
    if not storyUuid:
        title = data.get('title', '')
        worksType = False
    if bgmUuid:
        bg = Bgm.objects.filter(uuid=bgmUuid).first()
    if storyUuid:
        template = TemplateStory.objects.filter(uuid=storyUuid).first()
    if not all([voiceUrl, voiceVolume, recordType, typeUuidList, bgUrl, worksTime]):
        return http_return(400, '参数错误')
    tags = []
    for tagUuid in typeUuidList:
        tag = Tag.objects.filter(uuid=tagUuid).first()
        if tag:
            tags.append(tag)
    # 发布用户
    user = User.objects.filter(uuid=data['_cache']['uuid']).first()
    try:
        Works.objects.create(
            uuid=get_uuid(),
            userUuid=user if user else None,
            isUpload=1,
            voiceUrl=voiceUrl,
            userVolume=voiceVolume,
            bgmUuid=bg if bg else None,
            bgmVolume=bgmVolume if bgmVolume else None,
            recordType=recordType,
            playTimes=0,
            worksType=worksType,
            templateUuid=template if template else None,
            title=title,
            bgUrl=bgUrl,
            feeling=feeling,
            worksTime=worksTime,
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
            "name": tag.tagName,
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
    fans = user.get_followed()
    focus = user.get_follower()
    isFan = False
    myUuid = data['_cache']['uuid']
    for focu in focus:
        if myUuid == focu.uuid:
            isFan = True
            break
    userDict = {
        "uuid": user.uuid,
        "name": user.username,
        "icon": user.userLogo,
        "id": user.id,
        "isFan": isFan,
        "intro": user.intro,
        "fansCount": len(fans),
        "focusCount": len(focus)
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
    if not selfUser.set_follower(uuid):
        return http_return(400, '关注失败')
    return http_return(200, '关注成功')


@check_identify
def user_work_list(request):
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
    works = user.userWorkUuid.filter(isDelete=False).order_by("-createTime").all()
    total, works = page_index(works, page, pageCount)
    workList = []
    for work in works:
        title = work.title
        if work.worksType:
            title = work.templateUuid.title
        tagList = []
        for tag in work.tags.all():
            tagList.append({
                'uuid': tag.uuid,
                'name': tag.tagName
            })
        workList.append({
            "uuid": work.uuid,
            "duration": work.worksTime,
            "mediaUrl": work.bgUrl,
            "title": title,
            "createTime": datetime_to_string(work.createTime),
            "tagList": tagList
        })
    return http_return(200, '成功', {"total": total, "workList": workList})


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
    type = data.get('type', '')  # 默认返回关注的用户列表，传入fans返回粉丝用户列表
    page = data.get('page', '')
    pageCount = data.get('pageCount', '')
    if not uuid:
        return http_return(400, '参数错误')
    user = User.objects.filter(uuid=uuid).first()
    if not user:
        return http_return(400, '用户信息不存在')
    users = user.get_follower()
    if type == 'fans':
        users = user.get_followed()
    total, users = page_index(users, page, pageCount)
    userList = []
    for u in users:
        userList.append({
            "uuid": u.uuid,
            "icon": u.userLogo,
            "name": u.username
        })
    return http_return(200, '成功', {"total": total, "userList": userList})


@check_identify
def work_list(request):
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
    worksType = data.get('worksType', None)
    work = Works.objects.filter(checkStatus='check', isDelete=False)
    if worksType:
        work = work.filter(worksType=worksType)
    works = work.order_by('-createTime').all()
    total, works = page_index(works, page, pageCount)
    workList = []
    for work in works:
        title = work.title
        if work.worksType:
            title = work.templateUuid.title
        tagList = []
        for tag in work.tags.all():
            tagList.append({
                'uuid': tag.uuid,
                'name': tag.tagName
            })
        workList.append({
            "uuid": work.uuid,
            "duration": work.worksTime,
            "mediaUrl": work.bgUrl,
            "title": title,
            "createTime": datetime_to_string(work.createTime),
            "tagList": tagList
        })
    return http_return(200, '成功', {"total": total, "workList": workList})


@check_identify
def work_play(request):
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
    work = Works.objects.filter(uuid=uuid, checkStatus='check', isDelete=False).first()
    if not work:
        return http_return(400, '故事信息不存在')
    # 更新播放次数
    work.playTimes += 1
    try:
        work.save()
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '更新播放次数失败')
    content = None
    title = work.title
    if work.worksType:
        content = work.templateUuid.content
        title = work.templateUuid.title
    workDict = {
        "workUuid": work.uuid,
        "title": title,
        "content": content,
        "bgUrl": work.bgUrl,
        "duration": work.worksTime,
        "voiceUrl": work.voiceUrl,
        "userVolume": work.userVolume,
        "bgmUrl": work.bgmUuid.mediaUrl if work.bgmUuid else None,
        "bgmVolume": work.bgmVolume if work.bgmUuid else None,
        "name": work.userUuid.username,
        "icon": work.userUuid.userLogo,
        "createTIme": datetime_to_string(work.createTime),
        "playTimes": work.playTimes,
    }
    otherWork = Works.objects.exclude(uuid=uuid, isDelete=True).filter(userUuid__uuid=work.userUuid.uuid)
    otherWorks = otherWork.order_by("-createTime").all()
    total, otherWorks = page_index(otherWorks, page, pageCount)
    workList = []
    for otherWork in otherWorks:
        title = otherWork.title
        if otherWork.worksType:
            title = otherWork.templateUuid.title
        tagList = []
        for tag in otherWork.tags.all():
            tagList.append({
                'uuid': tag.uuid,
                'name': tag.tagName
            })
        workList.append({
            "uuid": otherWork.uuid,
            "duration": otherWork.worksTime,
            "mediaUrl": otherWork.bgUrl,
            "title": title,
            "createTime": datetime_to_string(otherWork.createTime),
            "tagList": tagList
        })
    return http_return(200, '成功', {"otherTotal": total, "workList": workList, "playInfo": workDict})


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
    banner = Viewpager.objects.filter(startTime__lte=nowDatetime, endTime__gte=nowDatetime, isUsing=True)
    # 按显示序号排序
    banner = banner.filter(isUsing=True, location=0).order_by('orderNum')
    banners = banner.all()
    banList = []
    for banner in banners:
        banList.append({
            'title': banner.title,
            'mediaUrl': banner.mediaUrl,
            'jumpType': banner.jumpType,
            'targetUuid': banner.targetUuid,
        })
    total = len(banners)
    return http_return(200, '成功', {"total": total, "banList": banList})

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
    modules = Module.objects.order_by("orderNum").all()
    for module in modules:
        list

