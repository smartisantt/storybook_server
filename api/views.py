#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# Create your views here.
from api.ssoSMS.sms import send_sms
from common.common import *
from api.apiCommon import *
from common.fileApi import fileApi
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


# @check_identify
def index_list(request):
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
    story = TemplateStory.objects
    if sort == "latest":
        story = story.order_by("-createTime")
    elif sort == "rank":
        story = story.order_by("-recordNum")
    elif sort == "recommended":  # 推荐算法
        story = story.order_by()
    stories = story.all()
    total, stories = page_index(stories, page, pageIndex)
    storyList = []
    for st in stories:
        storyList.append({
            "uuid": st.uuid,
            "title": st.intro,
            "mediaUrl": st.listMediaUuid,
            "recordNum": st.recordNum,
        })
    pass


# @check_identify
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
    banner = banner.order_by('orderNum')
    banners = banner.all()
    mediaList = []
    for ban in banners:
        mediaList.append(ban.mediaUuid)
    #获取媒体文件地址
    mediaDict = get_media(mediaList, 'mediaUuid')
    if not mediaDict:
        return http_return(400, '获取文件失败')
    banList = []
    for banner in banners:
        banList.append({
            'title': banner.title,
            'mediaUrl': mediaDict.get(banner.mediaUuid, None),
            'jumpType': banner.jumpType,
            'targetUrl': banner.targetUuid,
        })
    total = len(banners)
    return http_return(200, '成功', {"total": total, "banList": banList})
