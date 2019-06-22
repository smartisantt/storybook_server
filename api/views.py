#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# Create your views here.
from api.ssoSMS.sms import send_sms
from common.common import *
from manager.models import *
from api.apiCommon import check_identify
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
    pageIndex = data.get('pageIndex', '')
    sort = data.get('sort', '')  # latest最新 rank排行 recommended推荐
    if sort not in ['latest', 'rank', 'recommended']:
        return http_return(400, '参数错误')
    story = TemplateStory.objects.exclude(status="destroy")
    if sort == "latest":
        story = story.order_by("-createTime")
    elif sort == "rank":
        story = story.order_by("-recordNum")
    elif sort == "recommended":  # 推荐算法
        story = story.filter(isRecommd=True).order_by("-createTime")
    stories = story.all()
    total, stories = page_index(stories, page, pageIndex)
    mediaList = []
    for story in stories:
        mediaList.append(story.listMediaUuid)
    # 获取媒体文件地址
    if len(mediaList) > 0:
        mediaDict = get_media(mediaList, request)
        if not mediaDict:
            return http_return(400, '获取文件失败')
    storyList = []
    for st in stories:
        storyList.append({
            "uuid": st.uuid,
            "title": st.intro,
            "mediaUrl": mediaDict[st.listMediaUuid] if mediaDict else None,
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
    banner = banner.filter(isUsing=True).order_by('orderNum')
    banners = banner.all()
    mediaList = []
    for ban in banners:
        mediaList.append(ban.mediaUuid)
    # 获取媒体文件地址
    if len(mediaList) > 0:
        mediaDict = get_media(mediaList, request)
        if not mediaDict:
            return http_return(400, '获取文件失败')
    banList = []
    for banner in banners:
        banList.append({
            'title': banner.title,
            'mediaUrl': mediaDict[banner.mediaUuid] if mediaDict else None,
            'jumpType': banner.jumpType,
            'targetUrl': banner.targetUuid,
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
    mediaList = []
    mediaList.append(story.faceMediaUuid)
    # 获取媒体文件地址
    if len(mediaList) > 0:
        mediaDict = get_media(mediaList, request)
        if not mediaDict:
            return http_return(400, '获取文件失败')
    d = {
        "uuid": story.uuid,
        "title": story.intro if story.intro else None,
        "conten": story.content if story.content else None,
        "mediaUuid": mediaDict[story.faceMediaUuid] if mediaDict else None
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
    pageIndex = data.get('pageIndex', '')
    bgm = Bgm.objects.filter(isUsing=True).order_by('sortNum')
    bgms = bgm.all()
    total, bgms = page_index(bgms, page, pageIndex)
    mediaList = []
    for bgm in bgms:
        mediaList.append(bgm.mediaUuid)
    # 获取媒体文件地址
    if len(mediaList) > 0:
        mediaDict = get_media(mediaList, request)
        if not mediaDict:
            return http_return(400, '获取文件失败')
    bgmList = []
    for bg in bgms:
        bgmList.append({
            "uuid": bg.uuid,
            "name": bg.name,
            "bgmTime": bg.bgmTime,
            "mediaUrl": mediaDict[bg.mediaUuid] if mediaDict else None,
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
    viceUuid = data.get('viceUuid', '')
    viceVolume = data.get('viceVolume', '')
    bgmUuid = data.get('bgmUuid', '')
    bgmVolume = data.get('bgmVolume', '')
    photoMediaUuid = data.get('photoMediaUuid', '')
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
    if not all([viceUuid, viceVolume, recordType, typeUuidList, photoMediaUuid, worksTime]):
        return http_return(400, '参数错误')
    tags = []
    for tagUuid in typeUuidList:
        tag = Tag.objects.filter(uuid=tagUuid).first()
        if tag:
            tags.append(tag)
    try:
        Works.objects.create(
            isUpload=1,
            voiceMediaUuid=viceUuid,
            userVolume=viceVolume,
            bgmUuid=bg if bg else None,
            bgmVolume=bgmVolume if bgmVolume else None,
            recordType=recordType,
            recordDate=datetime.datetime.now(),
            playTimes=0,
            worksType=worksType,
            templateUuid=template if template else None,
            title=title,
            photoMediaUuid=photoMediaUuid,
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
    tag = Tag.objects.filter(parent__code="SEARCHSORT", parent__parent=None).order_by('sortNum')
    tags = tag.all()
    tagList = []
    for tag in tags:
        tagList.append({
            "uuid": tag.uuid,
            "name": tag.tagName,
        })
    total = len(tagList)
    return http_return(200, '成功', {"total": total, "tagList": tagList})
