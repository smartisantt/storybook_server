#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from urllib.parse import urljoin

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import authentication_classes, api_view, action
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from api.apiCommon import get_default_name
from common.MyJpush import post_schedule_message, time2str, delete_schedule, put_schedule_message, \
    post_schedule_notification, put_schedule_notification, jpush_notification, jpush_platform_msg
from common.common import limit_of_text
from common.textAPI import TextAudit
from manager.auths import CustomAuthentication
from manager.filters import StoryFilter, FreedomAudioStoryInfoFilter, CheckAudioStoryInfoFilter, AudioStoryInfoFilter, \
    UserSearchFilter, BgmFilter, HotSearchFilter, UserFilter, CycleBannerFilter, \
    AdFilter, FeedbackFilter, QualifiedAudioStoryInfoFilter, AlbumFilter, AuthorAudioStoryFilter, NotificationFilter, \
    CommentFilter
from manager.models import *
from manager.managerCommon import *
from manager.paginations import MyPagination
from manager.serializers import StorySerializer, FreedomAudioStoryInfoSerializer, CheckAudioStoryInfoSerializer, \
    AudioStoryInfoSerializer, TagsSimpleSerialzer, StorySimpleSerializer, UserSearchSerializer, BgmSerializer, \
    HotSearchSerializer, AdSerializer, ModuleSerializer, UserDetailSerializer, \
    AudioStorySimpleSerializer, CycleBannerSerializer, FeedbackSerializer, \
    TagsSerialzer, QualifiedAudioStoryInfoSerializer, AlbumSerializer, CheckAlbumSerializer, \
    AuthorAudioStorySerializer, AlbumDetailSerializer, NotificationSerializer, CommentSerializer
from common.api import Api
from django.db.models import Count, Q, Max, Min
from datetime import datetime, timedelta
from utils.errors import ParamsException

import jpush

q = (Q(isDelete=False) & Q(isUpload=1) & (
            Q(checkStatus='check') | Q(interfaceStatus="check") | Q(checkStatus='exemption')))


def admin(request):
    """
    后台路由测试
    :param request:
    :return:
    """
    return http_return(200, 'normal')


"""
登录接口
"""


def login(request):
    """登录模块"""
    # 前端传入token ， 先在缓存查找， 如果没有（调用接口查询），
    token = request.META.get('HTTP_TOKEN')
    try:
        user_data = caches['default'].get(token)
    except Exception as e:
        logging.error(str(e))
        return http_return(500, '服务器连接redis失败')

    # 登录前更新用户状态
    currentTime = datetime.now()
    # 过了结束时间，恢复用户成正常状态，缓存的信息userid自动删除
    User.objects.filter(endTime__lt=currentTime).exclude(status__in=["destroy", "normal"]). \
        update(status="normal", updateTime=currentTime, startTime=None, endTime=None, settingStatus=None)

    if user_data:
        # 获取缓存用户信息
        user_info = caches['default'].get(token)
        user = User.objects.filter(userID=user_info.get('userId', ''), roles='adminUser'). \
            exclude(status="destroy").only('userID').first()
        role = user.roles
        status = user.status
        if status == 'forbbiden_login':
            return http_return(403, '此用户被禁止登录')
        try:
            # 获取登录ip
            loginIp = get_ip_address(request)
            # 登录成功生成登录日志，缓存存入信息
            loginLog = LoginLog(
                uuid=get_uuid(),
                ipAddr=loginIp,
                userUuid=user,
                userAgent=request.META.get('HTTP_USER_AGENT', ''),
                isManager=True
            )
            loginLog.save()

        except Exception as e:
            logging.error(str(e))
            return http_return(401, '登陆失败')
        nickName = user.nickName or get_default_name(user.tel, '')
        return http_return(200, '登录成功', {'nickName': nickName, 'roles': role})
    # 缓存中没有数据
    if not user_data:
        api = Api()
        # 校验前端传过来的token值
        user_info = api.check_token(token)

        if not user_info:
            return http_return(401, '无效token')
        else:
            # 用户表中是否有该用户
            userID = user_info.get('userId', '')
            if not userID:
                return http_return(401, '无效token')
            user = User.objects.filter(userID=user_info.get('userId', ''), roles='adminUser'). \
                exclude(status="destroy").first()

            if not user:
                return http_return(403, '没有权限')

            # 当前表中没有此用户信息则不在数据库中创建，你又不是管理员
            # if not user:
            #     user = User(
            #         uuid=get_uuid(),
            #         tel=user_info.get('phone', ''),
            #         userID=userID,
            #         nickName=user_info.get('wxNickname', ''),
            #         roles="normalUser",
            #         avatar=user_info.get('wxAvatarUrl', ''),
            #         gender=user_info.get('wxSex', 0),
            #         status='normal'
            #     )
            #     try:
            #         with transaction.atomic():
            #             user.save()
            #     except Exception as e:
            #         logging.error(str(e))
            #         return http_return(400, '保存失败')
            # user = User.objects.filter(userID=userID).exclude(status__in=['destroy','forbbiden_login']).first()
            # print(user.uuid)
            # role = user.roles

            # 写入缓存
            loginIp = get_ip_address(request)
            if not create_session(user, token, loginIp):
                return http_return(500, '创建缓存失败')
            try:
                with transaction.atomic():
                    LoginLog.objects.create(
                        uuid=get_uuid(),
                        ipAddr=user_info.get('loginIp', ''),
                        userUuid=user,
                        userAgent=request.META.get('HTTP_USER_AGENT', ''),
                        isManager=True
                    )
                    role = user.roles or ''
                    nickName = user.nickName or get_default_name(user.tel, '')
                    return http_return(200, '登录成功', {'nickName': nickName, 'roles': role})
            except Exception as e:
                logging.error(str(e))
                return http_return(400, '保存日志失败')


"""
首页数据
"""


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def total_data(request):
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    # 前端传入毫秒为单位的时间戳
    startTimestamp = data.get('startTime', '')
    endTimestamp = data.get('endTime', '')

    if not all([startTimestamp, endTimestamp]):  # 最近7天数据，不包含今天的数据
        currentTime = datetime.now()
        t1 = currentTime + timedelta(days=-8)
        t2 = currentTime + timedelta(days=-1)
        t1 = datetime(t1.year, t1.month, t1.day)
        t2 = datetime(t2.year, t2.month, t2.day, 23, 59, 59, 999999)
    else:
        try:
            t1, t2 = timestamp2datetime(startTimestamp, endTimestamp)
        except Exception as e:
            logging.error(str(e))
            return http_return(e.status_code, e.detail)

        # 结束小于2019-05-30 00:00:00的时间不合法
        if t2 < datetime(2019, 5, 30):
            return http_return(200, '此时间没有数据', {'status': 1})

        if (t2 - t1).days > 31:
            return http_return(400, '超出时间范围')

    # 用户总人数
    totalUsers = User.objects.exclude(status='destroy').count()
    # 音频总数
    totalAudioStory = AudioStory.objects.filter(q).exclude(checkStatus="checkFail").count()
    # 专辑总数
    totalAlbums = Album.objects.filter(isDelete=False).count()
    # 新增用户人数
    newUsers = User.objects.filter(createTime__range=(t1, t2)).exclude(status='destroy').count()
    # 活跃用户人数
    activityUsers = LoginLog.objects.filter(createTime__range=(t1, t2), isManager=False).values('userUuid_id'). \
        annotate(Count('userUuid_id')).count()
    # 新增音频数
    newAudioStory = AudioStory.objects.filter(createTime__range=(t1, t2), isUpload=1).count()

    # 男性
    male = User.objects.filter(gender=1).exclude(status='destroy').count()

    # 女性
    female = User.objects.filter(gender=2).exclude(status='destroy').count()

    # 未知
    unkonwGender = User.objects.filter(gender=0).exclude(status='destroy').count()

    # 模板音频
    aduioStoryCount = AudioStory.objects.filter(Q(createTime__range=(t1, t2)) & Q(audioStoryType=1) & q). \
        exclude(checkStatus="checkFail").count()

    # 自由录制
    freedomStoryCount = AudioStory.objects.filter(Q(createTime__range=(t1, t2)) & Q(audioStoryType=0) & q). \
        exclude(checkStatus="checkFail").count()

    tagNameList = []
    tagsNumList = []
    userNumList = []
    tags = Tag.objects.filter(code="SEARCHSORT", parent__name='类型').order_by('sortNum')[:6]  #
    for tag in tags:
        tagNameList.append(tag.name)
        tagCount = tag.tagsAudioStory.filter(isDelete=False, createTime__range=(t1, t2)).count()
        tagsNumList.append(tagCount)
        userCount = tag.tagsAudioStory.filter(isDelete=False, createTime__range=(t1, t2)). \
            values('userUuid_id').annotate(Count('userUuid_id')).count()
        userNumList.append(userCount)

    recordTypePercentage = [{'name': name, 'tagsNum': tagsNum, 'userNum': userNum}
                            for name, tagsNum, userNum in zip(tagNameList, tagsNumList, userNumList)
                            ]

    # 活跃用户排行
    data1_list = []
    # result = AudioStory.objects.filter(isDelete=False, createTime__range=(t1, t2)).values('userUuid_id').annotate(Count('userUuid_id'))[:1]
    res = User.objects.annotate(audioStory_count_by_user=Count("useAudioUuid")).order_by('-audioStory_count_by_user')[
          :5]
    for index, item in enumerate(res.values()):
        data = {
            'orderNum': index + 1,
            'name': item['nickName'],
            'recordCount': item['audioStory_count_by_user']
        }
        data1_list.append(data)
    # 热门录制排行 模板在选定的时间范围内的录制次数排行
    data2_list = []
    # res = Story.objects.filter(status="normal", createTime__range=(t1, t2)).order_by('-recordNum')[:5]
    res = AudioStory.objects.filter(isDelete=False, createTime__range=(t1, t2), isUpload=1, audioStoryType=1). \
              values('storyUuid').annotate(storycount=Count('storyUuid')).order_by('-storycount')[:5]
    for index, item in enumerate(res):
        data = {
            'orderNum': index + 1 or -1,
            'name': Story.objects.filter(uuid=item['storyUuid']).first().name if item['storyUuid'] else '',
            'recordNum': item['storycount'] or 0
        }
        data2_list.append(data)

    # 热门播放排行
    data3_list = []
    audioStory = AudioStory.objects.filter(isDelete=False, createTime__range=(t1, t2), isUpload=1).order_by(
        '-playTimes')[:5]
    for index, item in enumerate(audioStory):
        data = {
            'orderNum': index + 1,
            'name': item.storyUuid.name if item.audioStoryType else item.name,
            'playTimes': item.playTimes
        }
        data3_list.append(data)

    begin = t1
    end = t2
    d = begin
    graphList = []
    delta = timedelta(days=1)
    while d <= end:
        graphList.append({'time': d.strftime("%m-%d"), 'userNum': 0})
        d += delta

    # 图表数据--新增用户
    graph1 = User.objects.filter(createTime__range=(t1, t2)). \
        only('createTime', 'id'). \
        extra(select={"time": "DATE_FORMAT(createTime,'%%m-%%d')"}). \
        order_by('time').values('time') \
        .annotate(userNum=Count('createTime')).values('time', 'userNum')
    # if graph1:
    #     graph1 = list(graph1)
    # else:
    #     graph1 = []
    if graph1:
        graph1 = list(graph1)
        res1 = graphList[:]
        for item in graph1:
            res1.remove({'time': item['time'], 'userNum': 0})
        res1.extend(graph1)
        res1 = sorted(res1, key=lambda s: s['time'], reverse=False)
    else:
        res1 = graphList

    # 活跃用户
    graph2 = LoginLog.objects.filter(createTime__range=(t1, t2), isManager=False). \
        only('time', 'userUuid_id'). \
        extra(select={"time": "DATE_FORMAT(createTime,'%%m-%%d')"}). \
        values('time').annotate(userNum=Count('userUuid_id', distinct=True)). \
        values('time', 'userNum').order_by('time')
    # if graph2:
    #     graph2 = list(graph2)
    # else:
    #     graph2 = []
    if graph2:
        graph2 = list(graph2)
        res2 = graphList[:]
        for item in graph2:
            res2.remove({'time': item['time'], 'userNum': 0})
        res2.extend(graph2)
        res2 = sorted(res2, key=lambda s: s['time'], reverse=False)
    else:
        res2 = graphList

    return http_return(200, '查询成功',
                       {
                           'totalUsers': totalUsers,  # 总用户人数
                           'totalAudioStory': totalAudioStory,  # 音频总数
                           'totalAlbums': totalAlbums,  # 总的专辑数
                           'newUsers': newUsers,  # 新增用户人数
                           'activityUsers': activityUsers,  # 活跃用户人数
                           'newAudioStory': newAudioStory,  # 新增音频数
                           'activityUsersRank': data1_list,  # 活跃用户排行
                           'male': male,  # 男性
                           'female': female,  # 女性
                           'unkonwGender': unkonwGender,  # 未知性别
                           'aduioStoryCount': aduioStoryCount,  # 模板音频数量
                           'freedomStoryCount': freedomStoryCount,  # 自由录制音频数量
                           'recordTypePercentage': recordTypePercentage,
                           'hotRecordRank': data2_list,  # 热门录制排行
                           'hotPlayAudioStoryRank': data3_list,  # 热门播放排行
                           'newUserGraph': res1,  # 新增用户折线图
                           'activityUserGraph': res2,  # 活跃用户折线图
                       })


class AllTagView(ListAPIView):
    queryset = Tag.objects.filter(code="SEARCHSORT", parent_id__isnull=True, isDelete=False)
    serializer_class = TagsSerialzer

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        res = {
            "total": len(serializer.data),
            "tagList": serializer.data
        }
        return Response(res)


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def add_tags(request):
    """添加分类（一级标签）"""
    data = request_body(request, "POST")
    if not data:
        return http_return(400, '参数错误')
    icon = data.get('icon', '')
    name = data.get('name', '')
    sortNum = data.get('sortNum', '')

    # all 都为True 才返回True
    if not all([name, sortNum, icon]):
        return http_return(400, '参数有误')
    if not isinstance(sortNum, int):
        return http_return(400, '序号错误')
    if sortNum <= 0:
        return http_return(400, '序号错误')
    # 一级标签中没有重复序号
    tag = Tag.objects.filter(sortNum=sortNum, parent_id__isnull=True, code='SEARCHSORT', isDelete=False).first()
    if tag:
        return http_return(400, '重复序号')
    # 查询是否有重复tagName
    tag = Tag.objects.filter(name=name, parent_id__isnull=True, code='SEARCHSORT', isDelete=False).first()
    if tag:
        return http_return(400, '重复分类名')
    try:
        with transaction.atomic():
            uuid = get_uuid()
            tag = Tag(
                uuid=uuid,
                code='SEARCHSORT',
                name=name,
                icon=icon,
                sortNum=sortNum
            )
            tag.save()
            return http_return(200, '添加分类成功')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '添加分类失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def modify_tags(request):
    """修改一级标签"""
    data = request_body(request, "POST")
    if not data:
        return http_return(400, '参数错误')
    icon = data.get('icon', '')
    name = data.get('name', '')
    sortNum = data.get('sortNum', '')
    uuid = data.get('uuid', '')
    if not all([name, sortNum, uuid, icon]):
        return http_return(400, '参数错误')
    if not isinstance(sortNum, int):
        return http_return(400, '序号错误')
    if sortNum <= 0:
        return http_return(400, '序号错误')
    tag = Tag.objects.filter(uuid=uuid).first()
    if not tag:
        return http_return(400, '没有对象')
    mySortNum = tag.sortNum
    myName = tag.name
    if sortNum != mySortNum:
        tag = Tag.objects.filter(sortNum=sortNum, code='SEARCHSORT', isDelete=False, parent_id__isnull=True).first()
        if tag:
            return http_return(400, '重复序号')

    if name != myName:
        tag = Tag.objects.filter(name=name, code='SEARCHSORT', isDelete=False, parent_id__isnull=True).first()
        if tag:
            return http_return(400, '重复标签')
    tag = Tag.objects.filter(uuid=uuid).first()
    try:
        with transaction.atomic():
            tag.sortNum = sortNum
            tag.icon = icon
            tag.name = myName  # 保存的还是老标签，一级标签不能修改
            tag.save()
            return http_return(200, '修改分类成功', {
                'name': myName,
                'icon': icon,
                'sortNum': sortNum,
            })

    except Exception as e:
        logging.error(str(e))
        return http_return(400, '修改分类失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def stop_tags(request):
    """停用/恢复一级标签"""
    data = request_body(request, "POST")
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')
    if not uuid:
        return http_return(400, '参数有误')
    tag = Tag.objects.filter(uuid=uuid, isDelete=False, parent_id__isnull=True).first()
    if not tag:
        return http_return(400, '没有对象')
    try:
        with transaction.atomic():
            tag.isUsing = not tag.isUsing
            tag.save()
            # 标签状态停用0 还是使用1
            return http_return(200, '保存分类成功', {"status": tag.isUsing})
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '保存分类失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def del_tags(request):
    """删除一级标签 或者 二级标签"""
    data = request_body(request, "POST")
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')
    if not uuid:
        return http_return(400, '参数有误')
    tag = Tag.objects.filter(uuid=uuid, code='SEARCHSORT', isDelete=False).first()
    if not tag:
        return http_return(400, '没有对象')

    try:
        # 如果删除的是一级标签则所有字标签一起删除
        if tag.parent is None:
            Tag.objects.filter(parent=tag).update(isDelete=True)
        with transaction.atomic():
            tag.isDelete = True
            tag.save()
            return http_return(200, '删除分类成功')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '删除分类失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def add_child_tags(request):
    """添加子标签"""
    data = request_body(request, "POST")
    if not data:
        return http_return(400, '参数错误')
    parentUuid = data.get('parentUuid', '')
    name = data.get('name', '')
    sortNum = data.get('sortNum', '')
    if not all([parentUuid, name, sortNum]):
        return http_return(400, '参数错误')
    if not isinstance(sortNum, int):
        return http_return(400, '序号错误')
    if sortNum <= 0:
        return http_return(400, '序号错误')

    parentTag = Tag.objects.filter(uuid=parentUuid, code='SEARCHSORT', isDelete=False, parent_id__isnull=True).first()
    if not parentTag:
        return http_return(400, '参数有误')
    # 查询是否有重复name
    tag = Tag.objects.filter(name=name, code='SEARCHSORT', isDelete=False, parent_id=parentUuid).first()
    if tag:
        return http_return(400, '重复标签')
    # 查询是否有重复sortNum
    tag = Tag.objects.filter(sortNum=sortNum, code='SEARCHSORT', isDelete=False, parent_id=parentUuid).first()
    if tag:
        return http_return(400, '重复序号')
    # 创建新标签
    try:
        with transaction.atomic():
            uuid = get_uuid()
            tag = Tag(
                uuid=uuid,
                code='SEARCHSORT',
                name=name,
                sortNum=sortNum,
                parent=parentTag
            )
            tag.save()
            return http_return(200, '创建子标签成功', {
                'uuid': uuid,
                'name': name,
                'sortNum': sortNum,
                'parentUuid': parentUuid
            })
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '保存失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def modify_child_tags(request):
    """修改子标签"""
    data = request_body(request, "POST")
    if not data:
        return http_return(400, '参数错误')
    parentUuid = data.get('parentUuid', '')
    name = data.get('name', '')
    sortNum = data.get('sortNum', '')
    uuid = data.get('uuid', '')
    if not all([parentUuid, name, sortNum, uuid]):
        return http_return(400, '参数错误')
    if not isinstance(sortNum, int):
        return http_return(400, '序号错误')
    if sortNum <= 0:
        return http_return(400, '序号错误')
    tag = Tag.objects.filter(uuid=uuid).first()
    if not tag:
        return http_return(400, '没有对象')
    mySortNum = tag.sortNum
    myName = tag.name

    parentTag = Tag.objects.filter(uuid=parentUuid, code='SEARCHSORT', isDelete=False, parent_id__isnull=True).first()
    if not parentTag:
        return http_return(400, '参数有误')

    if sortNum != mySortNum:
        tag = Tag.objects.filter(sortNum=sortNum, code='SEARCHSORT', isDelete=False, parent_id=parentUuid).first()
        if tag:
            return http_return(400, '重复序号')

    if name != myName:
        tag = Tag.objects.filter(name=name, code='SEARCHSORT', isDelete=False, parent_id=parentUuid).first()
        if tag:
            return http_return(400, '重复标签')
    tag = Tag.objects.filter(uuid=uuid).first()
    try:
        with transaction.atomic():
            tag.sortNum = sortNum
            tag.name = name
            tag.save()
            return http_return(200, '修改标签成功', {
                'uuid': uuid,
                'name': name,
                'sortNum': sortNum,
                'parentUuid': parentUuid
            })

    except Exception as e:
        logging.error(str(e))
        return http_return(400, '修改分类失败')


# 获取类型标签下的所有字标签
class TypeTagView(ListAPIView):
    queryset = Tag.objects.filter(code='SEARCHSORT', parent__name='类型', isDelete=False). \
        only('id', 'name', 'sortNum', 'uuid').all()
    serializer_class = TagsSimpleSerialzer
    pagination_class = MyPagination


# 获取所有子标签
class ChildTagView(ListAPIView):
    queryset = Tag.objects.filter(code='SEARCHSORT', parent_id__isnull=False, isDelete=False). \
        only('id', 'name', 'sortNum', 'uuid').all()
    serializer_class = TagsSimpleSerialzer
    pagination_class = MyPagination


"""
模板管理
"""


class StoryView(ListAPIView):
    """GET 显示所有模板列表"""
    queryset = Story.objects.exclude(status='destroy').defer('tags').order_by('-createTime')
    serializer_class = StorySerializer
    filter_class = StoryFilter
    pagination_class = MyPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('-createTime',)
    ordering_fields = ('id', 'createTime', 'recordNum')

    def get_queryset(self):
        startTimestamp = self.request.query_params.get('starttime', '')
        endTimestamp = self.request.query_params.get('endtime', '')

        if (startTimestamp and not endTimestamp) or (not startTimestamp and endTimestamp):
            raise ParamsException('时间错误')
        if startTimestamp and endTimestamp:
            try:
                starttime, endtime = timestamp2datetime(startTimestamp, endTimestamp)
                return self.queryset.filter(createTime__range=(starttime, endtime))
            except Exception as e:
                logging.error(str(e))
                raise ParamsException(e.detail)

        return self.queryset


class StorySimpleView(ListAPIView):
    """所有模板的模板名"""
    queryset = Story.objects.filter(status="normal")
    serializer_class = StorySimpleSerializer
    filter_class = StoryFilter
    pagination_class = MyPagination


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def add_story(request):
    """添加模板"""
    data = request_body(request, "POST")
    if not data:
        return http_return(400, '参数错误')
    faceIcon = data.get('faceIcon', '')
    listIcon = data.get('listIcon', '')  # 非必填
    name = data.get('name', '')
    intro = data.get('intro', '')
    content = data.get('content', '')
    isRecommd = data.get('isRecommd', '')
    isTop = data.get('isTop', '')

    # all 都为True 才返回True
    if not all([name, faceIcon, content, intro, isRecommd, isTop]):
        return http_return(400, '参数有误')

    story = Story.objects.filter(name=name).exclude(status='destroy').first()
    if story:
        return http_return(400, '重复模板名')

    if not limit_of_text(content, 16000):
        return http_return("故事内容字符超出16000")

    if not limit_of_text(name, 14):
        return http_return("模板故事名大于14个字符")

    if not limit_of_text(intro, 512):
        return http_return("模板故事介绍512个字符")

    try:
        with transaction.atomic():
            uuid = get_uuid()
            story = Story(
                uuid=uuid,
                faceIcon=faceIcon,
                listIcon=listIcon,
                name=name,
                intro=intro,
                content=content,
                isRecommd=isRecommd,
                isTop=isTop,
                recordNum=0
            )
            story.save()
            return http_return(200, '添加模板成功')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '添加模板失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def modify_story(request):
    """修改模板"""
    data = request_body(request, "POST")
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')
    faceIcon = data.get('faceIcon', '')
    listIcon = data.get('listIcon', '')  # 非必填
    name = data.get('name', '')
    intro = data.get('intro', '')
    content = data.get('content', '')
    isRecommd = data.get('isRecommd', '')
    isTop = data.get('isTop', '')

    # all 都为True 才返回True
    if not all([faceIcon, name, content, intro, isRecommd, isTop]):
        return http_return(400, '参数有误')

    story = Story.objects.filter(uuid=uuid).exclude(status='destroy').first()
    if not story:
        return http_return(400, '没有对象')

    if not limit_of_text(content, 16000):
        return http_return("故事内容字符超出16000")

    if not limit_of_text(name, 14):
        return http_return("模板故事名大于14个字符")

    if not limit_of_text(intro, 512):
        return http_return("模板故事介绍512个字符")

    myName = story.name
    # 如果修改标题
    if myName != name:
        story = Story.objects.filter(name=name).exclude(status='destroy').first()
        if story:
            return http_return(400, '重复标题')

    story = Story.objects.filter(uuid=uuid).exclude(status='destroy').first()
    try:
        with transaction.atomic():
            story.faceIcon = faceIcon
            story.listIcon = listIcon
            story.name = name
            story.intro = intro
            story.content = content
            story.isRecommd = isRecommd
            story.isTop = isTop
            story.save()
            return http_return(200, '添加模板成功')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '添加模板失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def change_story_status(request):
    """停用模板 恢复模板"""
    data = request_body(request, "POST")
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')

    if not uuid:
        return http_return(400, '参数有误')

    story = Story.objects.filter(uuid=uuid).exclude(status='destroy').first()
    if not story:
        return http_return(400, '没有对象')

    story = Story.objects.filter(uuid=uuid).exclude(status='destroy').first()
    try:
        with transaction.atomic():
            # normal启用 forbid禁用 destroy删除
            if story.status == 'normal':
                story.status = 'forbid'
            elif story.status == 'forbid':
                story.status = 'normal'
            story.save()
            return http_return(200, '改变模板状态成功', {"status": story.status})
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '改变模板状态失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def del_story(request):
    """删除模板"""
    data = request_body(request, "POST")
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')

    if not uuid:
        return http_return(400, '参数有误')

    story = Story.objects.filter(uuid=uuid).exclude(status='destroy').first()
    if not story:
        return http_return(400, '没有对象')

    # 用这个模板创造的作品则提示不能删除
    story = Story.objects.filter(uuid=uuid).exclude(status='destroy').first()
    audioStory = AudioStory.objects.filter(storyUuid=story, isDelete=False).first()
    if audioStory:
        return http_return(400, '该模板已关联音频')
    try:
        with transaction.atomic():
            story.status = 'destroy'
            story.save()
            return http_return(200, '删除模板成功')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '删除模板失败')


class AudioStoryInfoView(ListAPIView):
    """模板音频"""
    queryset = AudioStory.objects.filter(q & Q(audioStoryType=1)) \
        .exclude(checkStatus="checkFail") \
        .select_related('bgm', 'userUuid') \
        .prefetch_related('tags')

    serializer_class = AudioStoryInfoSerializer
    filter_class = AudioStoryInfoFilter
    pagination_class = MyPagination

    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('-createTime',)
    ordering_fields = ('id', 'createTime')

    def get_queryset(self):
        startTimestamp = self.request.query_params.get('starttime', '')
        endTimestamp = self.request.query_params.get('endtime', '')
        nickName = self.request.query_params.get('nickName', '')  # 用户名
        tag = self.request.query_params.get('tag', '')  # 类型标签

        if (startTimestamp and not endTimestamp) or (not startTimestamp and endTimestamp):
            raise ParamsException('时间错误')
        if startTimestamp and endTimestamp:
            try:
                starttime, endtime = timestamp2datetime(startTimestamp, endTimestamp)
                self.queryset = self.queryset.filter(createTime__range=(starttime, endtime))
            except Exception as e:
                logging.error(str(e))
                raise ParamsException(e.detail)

        if nickName:
            self.queryset = self.queryset.filter(userUuid__in=User.objects.filter(nickName__icontains=nickName).all())

        if tag:
            tag_info = Tag.objects.filter(uuid=tag, isDelete=False).first()
            if tag_info:
                self.queryset = self.queryset.filter(tags__id=tag_info.id)
            else:
                self.queryset = self.queryset.filter(tags__id=0)

        return self.queryset


class UserSearchView(ListAPIView):
    queryset = User.objects.only('uuid', 'nickName').exclude(status="destroy").order_by("nickName")
    serializer_class = UserSearchSerializer
    filter_class = UserSearchFilter
    pagination_class = None


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def add_audio_story(request):
    """添加音频"""
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    storyUuid = data.get('storyuuid', '')
    userUuid = data.get('useruuid', '')
    remarks = data.get('remarks', '')
    duration = data.get('duration', '')
    url = data.get('url', '')
    type = data.get('type', '')  # 录制形式 0宝宝录制 1爸妈录制
    tagsUuidList = data.get('tagsuuidlist', '')
    fileSize = data.get('filesize', '')  # 文件大小

    if not all([storyUuid, userUuid, remarks, url, duration, tagsUuidList, type in [0, 1]]):
        return http_return(400, '参数不能为空')

    if not (isinstance(fileSize, int) and fileSize > 0):
        return http_return(400, '文件大小参数有误')

    story = Story.objects.filter(uuid=storyUuid).first()
    if not story:
        return http_return(400, '模板错误')

    user = User.objects.filter(uuid=userUuid).exclude(status="destroy").first()
    if not user:
        return http_return(400, '找不到用户')

    tags = []
    for tagUuid in tagsUuidList:
        tag = Tag.objects.filter(uuid=tagUuid).first()
        if not tag:
            return http_return(400, '无效标签')
        tags.append(tag)
    # 相同用户，相同模板，相同音频，则是重复上传
    audioStory = AudioStory.objects.filter(userUuid=user, storyUuid=story, voiceUrl=url, isDelete=False).first()
    if audioStory:
        return http_return(400, '重复添加')
    try:
        uuid = get_uuid()
        AudioStory.objects.create(
            uuid=uuid,
            userUuid=user,
            isUpload=1,
            voiceUrl=url,
            playTimes=0,
            audioStoryType=1,  # 1模板录制 0 自由音频
            type=type,
            name=story.name,
            bgIcon=story.faceIcon,
            storyUuid=story,
            remarks=remarks,
            duration=duration,
            fileSize=fileSize,
            checkStatus="exemption"
        ).tags.add(*tags)
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '添加失败')
    return http_return(200, '添加成功')


class FreedomAudioStoryInfoView(ListAPIView):
    """自由音频"""
    queryset = AudioStory.objects.filter(q & Q(audioStoryType=0)) \
        .exclude(checkStatus='checkFail') \
        .select_related('bgm', 'userUuid') \
        .prefetch_related('tags').order_by('-createTime')

    serializer_class = FreedomAudioStoryInfoSerializer
    filter_class = FreedomAudioStoryInfoFilter
    pagination_class = MyPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('-createTime',)
    ordering_fields = ('id', 'createTime')

    def get_queryset(self):
        startTimestamp = self.request.query_params.get('startTime', '')
        endTimestamp = self.request.query_params.get('endTime', '')
        nickName = self.request.query_params.get('nickName', '')  # 用户名
        tag = self.request.query_params.get('tag', '')  # 类型标签

        if (startTimestamp and not endTimestamp) or (not startTimestamp and endTimestamp):
            raise ParamsException('时间错误')
        if startTimestamp and endTimestamp:
            try:
                starttime, endtime = timestamp2datetime(startTimestamp, endTimestamp)
                self.queryset = self.queryset.filter(createTime__range=(starttime, endtime))
            except Exception as e:
                logging.error(str(e))
                raise ParamsException(e.detail)

        if nickName:
            self.queryset = self.queryset.filter(userUuid__in=User.objects.filter(nickName__icontains=nickName).all())

        if tag:
            tag_info = Tag.objects.filter(uuid=tag, isDelete=False).first()
            if tag_info:
                self.queryset = self.queryset.filter(tags__id=tag_info.id)
        return self.queryset


# 内容审核
class CheckAudioStoryInfoView(ListAPIView):
    queryset = AudioStory.objects.filter(isDelete=False, isUpload=1) \
        .select_related('bgm', 'userUuid') \
        .prefetch_related('tags')

    serializer_class = CheckAudioStoryInfoSerializer
    filter_class = CheckAudioStoryInfoFilter
    pagination_class = MyPagination

    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('-createTime',)
    ordering_fields = ('id', 'createTime')

    def get_queryset(self):
        startTimestamp = self.request.query_params.get('starttime', '')
        endTimestamp = self.request.query_params.get('endtime', '')
        nickName = self.request.query_params.get('nickName', '')  # 用户名

        if (startTimestamp and not endTimestamp) or (not startTimestamp and endTimestamp):
            raise ParamsException('时间错误')
        if startTimestamp and endTimestamp:
            try:
                starttime, endtime = timestamp2datetime(startTimestamp, endTimestamp)
                self.queryset = self.queryset.filter(createTime__range=(starttime, endtime))
            except Exception as e:
                logging.error(str(e))
                raise ParamsException(e.detail)

        if nickName:
            self.queryset = self.queryset.filter(userUuid__in=User.objects.filter(nickName__icontains=nickName).all())

        return self.queryset


class QualifiedAudioStoryInfoView(ListAPIView):
    queryset = AudioStory.objects.filter(q).exclude(checkStatus="checkFail") \
        .select_related('bgm', 'userUuid') \
        .prefetch_related('tags')

    serializer_class = QualifiedAudioStoryInfoSerializer
    filter_class = QualifiedAudioStoryInfoFilter
    pagination_class = MyPagination

    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('-createTime',)
    ordering_fields = ('id', 'createTime')

    def get_queryset(self):
        startTimestamp = self.request.query_params.get('starttime', '')
        endTimestamp = self.request.query_params.get('endtime', '')
        nickName = self.request.query_params.get('nickName', '')  # 用户名

        if (startTimestamp and not endTimestamp) or (not startTimestamp and endTimestamp):
            raise ParamsException('时间错误')
        if startTimestamp and endTimestamp:
            try:
                starttime, endtime = timestamp2datetime(startTimestamp, endTimestamp)
                self.queryset = self.queryset.filter(createTime__range=(starttime, endtime))
            except Exception as e:
                logging.error(str(e))
                raise ParamsException(e.detail)

        if nickName:
            self.queryset = self.queryset.filter(userUuid__in=User.objects.filter(nickName__icontains=nickName).all())

        return self.queryset


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def check_audio(request):
    """审核通过和审核不通过"""
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    audioStoryUuid = data.get('audiostoryuuid', '')
    checkStatus = data.get('checkstatus', '')

    if not all([audioStoryUuid, checkStatus in ["check", "checkFail"]]):
        return http_return(400, '参数错误')

    audioStory = AudioStory.objects.filter(uuid=audioStoryUuid, checkStatus='unCheck', isDelete=False).first()
    if not audioStory:
        return http_return(400, '对象错误')

    userUuid = audioStory.userUuid_id

    # 审核通过，通知该音频作者   并存入系统消息表
    if checkStatus == "check":
        # 审核通过 audiouuid 这个作品
        type = 4
        title = "你的作品已通过审核"
        content = "您好，您录制的《{}》已通过审核，快去分享吧。".format(audioStory.name)
        extras = {"type": 0}
    else:
        # 没有审核通过存入
        type = 5
        title = "您的作品审核未通过"
        content = "您好，您录制的《{}》因含有违禁信息，审核不通过，将不能发布。请您遵守《绘童用户守则》，避免账号被封禁。如有疑问，请至客服中心反馈。".format(audioStory.name)
        extras = {"type": 0}

    publishState = 0
    if JPUSH == "ON":
        try:
            jpush_notification(title, content, extras, [userUuid])
            publishState = 1   # 推送成功
        except Exception as e:
            publishState = 2  # 推送失败
            logging.error(str(e))
            # 极光出错
            # return http_return(400, '极光出错！')

    # 绘童团队
    user = User.objects.filter(tel=HTTD).exclude(status="destroy").first()
    if user:
        httd = user.uuid
    else:
        httd = ""

    try:
        with transaction.atomic():
            uuid = get_uuid()
            SystemNotification.objects.create(
                uuid=uuid,
                userUuid=httd,
                title=title,
                content=content,
                publishDate=datetime.now(),
                linkAddress=audioStoryUuid,
                linkText="",
                type=type,
                targetType=2,  # 音频
                activityUuid="",
                publishState=publishState,
                audioUuid=audioStoryUuid,
                scheduleId="",
                isDelete=False,
            )
            audioStory.checkStatus = checkStatus
            audioStory.save()
        return http_return(200, '审核成功')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '审核失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def config_tags(request):
    """配置标签"""
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    audioStoryUuid = data.get('audiostoryuuid', '')
    tagsUuidList = data.get('tagsuuidlist', '')

    if not audioStoryUuid:
        return http_return(400, '参数错误')
    audioStory = AudioStory.objects.filter(uuid=audioStoryUuid).first()

    if not audioStory:
        return http_return(400, '找不到此音频')

    # 一个标签都没有选
    if not tagsUuidList:
        try:
            with transaction.atomic():
                audioStory.tags.clear()
                return http_return(200, '配置标签成功')
        except Exception as e:
            logging.error(str(e))
            return http_return(400, '配置标签失败')

    tags = []
    for tagUuid in tagsUuidList:
        tag = Tag.objects.filter(uuid=tagUuid).first()
        if not tag:
            return http_return(400, '无效标签')
        tags.append(tag)

    try:
        with transaction.atomic():
            audioStory.tags.clear()
            audioStory.tags.add(*tags)
            return http_return(200, '配置标签成功')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '配置标签失败')


class BgmView(ListAPIView):
    # 背景音乐管理
    # 音乐名，时间搜索
    # 展示BGM的ID 音乐名 上传时间
    queryset = Bgm.objects.exclude(status='destroy').only('uuid').order_by('sortNum')
    serializer_class = BgmSerializer
    filter_class = BgmFilter
    pagination_class = MyPagination

    def get_queryset(self):
        startTimestamp = self.request.query_params.get('starttime', '')
        endTimestamp = self.request.query_params.get('endtime', '')

        if (startTimestamp and not endTimestamp) or (not startTimestamp and endTimestamp):
            raise ParamsException('时间错误')
        if startTimestamp and endTimestamp:
            try:
                starttime, endtime = timestamp2datetime(startTimestamp, endTimestamp)
                return self.queryset.filter(createTime__range=(starttime, endtime))
            except Exception as e:
                logging.error(str(e))
                raise ParamsException(e.detail)

        return self.queryset


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def add_bgm(request):
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    url = data.get('url', '')
    name = data.get('name', '')
    duration = data.get('duration', '')

    if not all([url, name, duration]):
        return http_return(400, '参数错误')
    bgm = Bgm.objects.filter(url=url).exclude(status="destroy").first()
    if bgm:
        return http_return(400, '重复文件')
    bgm = Bgm.objects.filter(name=name).exclude(status="destroy").first()
    if bgm:
        return http_return(400, '重复音乐名')

    maxSortNum = Bgm.objects.exclude(status='destroy').aggregate(Max('sortNum'))['sortNum__max'] or 0

    try:
        with transaction.atomic():
            uuid = get_uuid()
            Bgm.objects.create(
                uuid=uuid,
                url=url,
                name=name,
                sortNum=maxSortNum + 1,
                duration=duration,
            )
        return http_return(200, '添加成功')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '添加失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def modify_bgm(request):
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')
    url = data.get('url', '')
    name = data.get('name', '')
    duration = data.get('duration', '')

    if not all([uuid, url, name, duration]):
        return http_return(400, '参数错误')

    bgm = Bgm.objects.filter(uuid=uuid).exclude(status="destroy").first()
    if not bgm:
        return http_return(400, '找不到对象')
    myUrl = bgm.url
    myName = bgm.name
    sortNum = bgm.sortNum or 1

    if myUrl != url:
        bgm = Bgm.objects.filter(url=url).exclude(status="destroy").first()
        if bgm:
            return http_return(400, '重复文件')
    if myName != name:
        bgm = Bgm.objects.filter(name=name).exclude(status="destroy").first()
        if bgm:
            return http_return(400, '重复音乐名')

    try:
        with transaction.atomic():
            bgm = Bgm.objects.filter(uuid=uuid).exclude(status="destroy").first()
            bgm.url = url
            bgm.name = name
            bgm.sortNum = sortNum
            bgm.duration = duration
            bgm.save()

        return http_return(200, '修改成功')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '修改失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def change_order(request):
    """改变音乐排序"""
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')
    direct = data.get('direct', '')

    if not all([uuid, direct in ["up", "down"]]):
        return http_return(400, "参数错误")

    bgm = Bgm.objects.filter(uuid=uuid).exclude(status="destroy").first()
    if not bgm:
        return http_return(400, "没有对象")
    mySortNum = bgm.sortNum
    swapSortNum = 0
    # 向上
    if direct == "up":
        # 比当前sortNum小的最大值
        swapSortNum = Bgm.objects.filter(sortNum__lt=mySortNum).exclude(status="destroy").aggregate(Max('sortNum'))[
            'sortNum__max']
        if not swapSortNum:
            return http_return(400, "已经到顶了")
    elif direct == "down":
        # 比当前sortNum大的最小值
        swapSortNum = Bgm.objects.filter(sortNum__gt=mySortNum).exclude(status="destroy").aggregate(Min('sortNum'))[
            'sortNum__min']
        if not swapSortNum:
            return http_return(400, "已经到底了")

    try:
        with transaction.atomic():
            swapBgm = Bgm.objects.filter(sortNum=swapSortNum).exclude(status="destroy").first()
            bgm.sortNum, swapBgm.sortNum = swapSortNum, mySortNum
            bgm.save()
            swapBgm.save()
        return http_return(200, '修改成功')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '修改失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def forbid_bgm(request):
    """停用/恢复背景音乐"""
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')
    status = data.get('status', '')
    if not all([uuid, status in ['normal', 'forbid']]):
        return http_return(400, '参数错误')

    bgm = Bgm.objects.filter(uuid=uuid).exclude(status="destroy").first()
    if not bgm:
        return http_return(400, '找不到对象')
    try:
        # forbid 停用 normal正常 在用  destroy 删除
        with transaction.atomic():
            if status == "normal":
                bgm.status = "normal"
            elif status == "forbid":
                bgm.status = "forbid"
            else:
                return http_return(400, '参数错误')
            bgm.save()
        return http_return(200, '修改成功')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '修改失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def del_audioStory(request):
    """删除模板音频 或者 自由音频"""

    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')
    if not uuid:
        return http_return(400, '参数错误')

    audioStory = AudioStory.objects.filter(uuid=uuid, isDelete=False).first()
    if not audioStory:
        return http_return(400, '找不到对象')
    """删除的音频 在首页模块显示 则不允许删除"""
    module = Module.objects.filter(audioUuid=audioStory, isDelete=False).first()
    if module:
        return http_return(400, '该音频已关联模块配置')
    # 音频关联广告
    ad = Ad.objects.filter(target=uuid, isDelete=False).first()
    if ad:
        return http_return(400, '该音频已关联广告')
    # 音频关联轮播图
    banner = CycleBanner.objects.filter(target=uuid, isDelete=False).first()
    if banner:
        return http_return(400, '该音频已关联轮播图')
    try:
        with transaction.atomic():
            audioStory.isDelete = True
            audioStory.save()
        return http_return(200, '修改成功')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '删除失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def del_bgm(request):
    """删除背景音乐"""
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')
    if not uuid:
        return http_return(400, '参数错误')

    bgm = Bgm.objects.filter(uuid=uuid).exclude(status="destroy").first()
    if not bgm:
        return http_return(400, '找不到对象')
    if AudioStory.objects.filter(bgm__uuid=uuid, isDelete=False).exists():
        return http_return(400, '该背景音乐在作品中使用')
    try:
        # forbid 停用 normal正常 在用  destroy 删除
        bgm = Bgm.objects.filter(uuid=uuid).exclude(status="destroy").first()
        with transaction.atomic():
            bgm.status = "destroy"
            bgm.save()
        return http_return(200, '修改成功')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '修改失败')


# 热搜词
class HotSearchView(ListAPIView):
    queryset = HotSearch.objects.filter(isDelete=False).only('id', 'keyword')
    serializer_class = HotSearchSerializer
    filter_class = HotSearchFilter
    pagination_class = MyPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('-isTop', '-searchNum')


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def add_keyword(request):
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    keyword = data.get('keyword', '')
    if not keyword:
        return http_return(400, "参数有误")

    hotSearch = HotSearch.objects.filter(keyword=keyword, isDelete=False).first()
    if hotSearch:
        return http_return(400, "重复名字")
    try:
        uuid = get_uuid()
        HotSearch.objects.create(
            uuid=uuid,
            keyword=keyword,
            searchNum=0,
            isAdminAdd=True
        )
        return http_return(200, '添加成功')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '添加失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def top_keyword(request):
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')
    if not uuid:
        return http_return(400, "参数有误")

    hotSearch = HotSearch.objects.filter(uuid=uuid, isDelete=False).first()
    if not hotSearch:
        return http_return(400, "没有对象")
    try:
        with transaction.atomic():
            if hotSearch.isTop:
                hotSearch.isTop = 0
            else:
                maxTop = HotSearch.objects.filter(isDelete=False).aggregate(Max('isTop'))['isTop__max']
                hotSearch.isTop = maxTop + 1
            hotSearch.save()
        return http_return(200, '置顶成功')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '置顶失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def del_keyword(request):
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')
    if not uuid:
        return http_return(400, "参数有误")

    hotSearch = HotSearch.objects.filter(uuid=uuid, isDelete=False).first()
    if not hotSearch:
        return http_return(400, "没有对象")
    try:
        with transaction.atomic():
            hotSearch.isDelete = True
            hotSearch.save()
        return http_return(200, '删除失败')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '删除失败')


class AdView(ListAPIView):
    queryset = Ad.objects.filter(isDelete=False).only('id').order_by('orderNum')
    serializer_class = AdSerializer
    filter_class = AdFilter
    pagination_class = MyPagination

    def get_queryset(self):
        startTimestamp = self.request.query_params.get('starttime', '')
        endTimestamp = self.request.query_params.get('endtime', '')

        if (startTimestamp and not endTimestamp) or (not startTimestamp and endTimestamp):
            raise ParamsException('时间错误')
        if startTimestamp and endTimestamp:
            try:
                starttime, endtime = timestamp2datetime(startTimestamp, endTimestamp, convert=False)
                return self.queryset.exclude(Q(startTime__gt=endtime) & Q(endTime__gt=endtime) |
                                             Q(endTime__lt=starttime) & Q(startTime__lt=starttime))
            except Exception as e:
                logging.error(str(e))
                raise ParamsException(e.detail)

        return self.queryset


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def add_ad(request):
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    name = data.get('name', '')
    icon = data.get('icon', '')
    type = data.get('type', '')
    target = data.get('target', '')
    orderNum = data.get('orderNum', '')
    startTime = data.get('startTime', '')
    endTime = data.get('endTime', '')
    if not all([name, icon, type in range(0, 5), startTime, orderNum, endTime, target]):
        return http_return(400, '参数错误')
    if Ad.objects.filter(name=name, isDelete=False).exists():
        return http_return(400, '重复标题')

    if Ad.objects.filter(orderNum=orderNum, isDelete=False).exists():
        return http_return(400, '重复排序')

    if startTime > endTime:
        return http_return(400, '时间错误')

    if not all([isinstance(startTime, int), isinstance(endTime, int)]):
        return http_return(400, '时间格式错误')

    startTime = startTime / 1000
    endTime = endTime / 1000

    try:
        startTime = datetime.fromtimestamp(startTime)
        endTime = datetime.fromtimestamp(endTime)
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '时间格式错误')

    if type == 0:
        if not Activity.objects.filter(uuid=target, status='normal').exists():
            return http_return(400, '没有此活动')

    if type == 1:
        if not Album.objects.filter(uuid=target, isDelete=False, checkStatus__in=["check", "exemption"]).exists():
            return http_return(400, '没有此专辑')

    if type == 2:  # 音频
        if not AudioStory.objects.filter(Q(uuid=target) & q).exclude(checkStatus="checkFail").exists():
            return http_return(400, '没有此音频')

    if type == 4:  # 外部链接
        if not target.startswith('http'):
            return http_return(400, '跳转地址格式错误')

    try:
        uuid = get_uuid()
        Ad.objects.create(
            uuid=uuid,
            name=name,
            type=type,
            startTime=startTime,
            endTime=endTime,
            orderNum=orderNum,
            target=target,
            icon=icon
        )
        return http_return(200, '添加成功')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '添加失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def modify_ad(request):
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')
    name = data.get('name', '')
    icon = data.get('icon', '')
    type = data.get('type', '')
    target = data.get('target', '')
    orderNum = data.get('orderNum', '')
    startTime = data.get('startTime', '')
    endTime = data.get('endTime', '')
    if not all([uuid, name, icon, type in range(0, 5), startTime, orderNum, endTime, target]):
        return http_return(400, '参数错误')

    ad = Ad.objects.filter(uuid=uuid, isDelete=False).first()
    if not ad:
        return http_return(400, '没有对象')

    myName = ad.name
    myOrderNum = ad.orderNum

    if myName != name:
        if CycleBanner.objects.filter(name=name, isDelete=False).exists():
            return http_return(400, '重复标题')
    if myOrderNum != orderNum:
        if CycleBanner.objects.filter(orderNum=orderNum, isDelete=False).exists():
            return http_return(400, '重复排序')

    if startTime > endTime:
        return http_return(400, '时间错误')

    if not all([isinstance(startTime, int), isinstance(endTime, int)]):
        return http_return(400, '时间错误')

    startTime = startTime / 1000
    endTime = endTime / 1000

    try:
        startTime = datetime.fromtimestamp(startTime)
        endTime = datetime.fromtimestamp(endTime)
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '时间格式错误')

    if type == 0:
        if not Activity.objects.filter(uuid=target, status='normal').exists():
            return http_return(400, '没有此活动')

    if type == 1:
        if not Album.objects.filter(uuid=target, isDelete=False, checkStatus__in=["check", "exemption"]).exists():
            return http_return(400, '没有此专辑')

    if type == 2:  # 音频
        if not AudioStory.objects.filter(Q(uuid=target) & q).exclude(checkStatus="checkFail").exists():
            return http_return(400, '没有此音频')

    if type == 4:  # 外部链接
        if not target.startswith('http'):
            return http_return(400, '跳转地址格式错误')

    try:
        ad = Ad.objects.filter(uuid=uuid, isDelete=False)
        ad.update(
            updateTime=datetime.now(),
            name=name,
            type=type,
            startTime=startTime,
            endTime=endTime,
            orderNum=orderNum,
            target=target,
            icon=icon
        )
        return http_return(200, '修改成功')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '修改失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def del_ad(request):
    # 删除
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')

    if not uuid:
        return http_return(400, '参数错误')

    ad = Ad.objects.filter(uuid=uuid, isDelete=False).first()
    if not ad:
        return http_return(400, '没有对象')

    try:
        with transaction.atomic():
            ad.isDelete = True
            ad.save()
            return http_return(200, '删除成功')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '删除失败')


# 模块配置
class ModuleView(ListAPIView):
    """显示模块类型 MOD1每日一读  MOD2抢先听  MOD3热门推荐"""
    queryset = Module.objects.filter(isDelete=False). \
        select_related('audioUuid', 'albumUuid').order_by('orderNum')
    serializer_class = ModuleSerializer

    # pagination_class = MyPagination

    def get_queryset(self):
        type = self.request.query_params.get('type', '')
        if type not in ['MOD1', 'MOD2', 'MOD3']:
            raise ParamsException({'code': 400, 'msg': '参数错误'})
        return self.queryset.filter(type=type)


# 显示所有作品的简单信息
class AllAudioSimpleView(ListAPIView):
    queryset = AudioStory.objects.filter(q).exclude(checkStatus="checkFail").order_by('-createTime')
    serializer_class = AudioStorySimpleSerializer
    filter_class = CheckAudioStoryInfoFilter
    pagination_class = MyPagination

    def get_queryset(self):
        startTimestamp = self.request.query_params.get('starttime', '')
        endTimestamp = self.request.query_params.get('endtime', '')

        nickName = self.request.query_params.get('nickName', '')  # 用户名
        name = self.request.query_params.get('name', '')  # 作品名

        # 审核状态 unCheck待审核 check审核通过 checkFail审核不通过 exemption 免检（后台上传的作品）

        if (startTimestamp and not endTimestamp) or (not startTimestamp and endTimestamp):
            raise ParamsException('时间错误')
        if startTimestamp and endTimestamp:
            try:
                starttime, endtime = timestamp2datetime(startTimestamp, endTimestamp)
                self.queryset = self.queryset.filter(createTime__range=(starttime, endtime))
            except Exception as e:
                logging.error(str(e))
                raise ParamsException(e.detail)

        if nickName:
            self.queryset = self.queryset.filter(userUuid__in=User.objects.filter(nickName__icontains=nickName).all())

        return self.queryset


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def add_story_into_module(request):
    """新增"""
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    type = data.get('type', '')
    contentType = data.get('contenttype', '')  # 1 自由音频 2 模板音频 3 专辑
    # audioUuid = data.get('audiouuid', '')
    targetUuid = data.get('targetuuid', '')
    if not all([type in ['MOD1', 'MOD2', 'MOD3'], targetUuid, contentType in [1, 2, 3]]):
        return http_return(400, '参数错误')
    if type == 'MOD1' and contentType != 2:
        return http_return(400, '每日一读只能添加模板音频')

    audioStory = None
    album = None
    if contentType in [1, 2]:
        audioStory = AudioStory.objects.filter(Q(uuid=targetUuid) & q).exclude(checkStatus="checkFail").first()
        if not audioStory:
            return http_return(400, '没有对象')
        module = Module.objects.filter(isDelete=False, audioUuid=audioStory, type=type, contentType=contentType).first()
        if module:
            return http_return(400, '已经添加')
    else:
        album = Album.objects.filter(uuid=targetUuid, isDelete=False,
                                     checkStatus__in=["check", "exemption"]).first()
        if not album:
            return http_return(400, '没有对象')
        module = Module.objects.filter(isDelete=False, albumUuid=album, type=type, contentType=contentType).first()
        if module:
            return http_return(400, '已经添加')

    maxOrderNum = Module.objects.filter(isDelete=False, type=type).aggregate(Max('orderNum'))['orderNum__max'] or 0
    try:
        with transaction.atomic():
            uuid = get_uuid()
            Module.objects.create(
                uuid=uuid,
                type=type,
                contentType=contentType,
                orderNum=maxOrderNum + 1,
                audioUuid=audioStory,
                albumUuid=album
            )
        return http_return(200, '添加成功')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '添加失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def change_story_in_module(request):
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    moduleUuid = data.get('moduleuuid', '')  # 要替换哪条uuid
    targetUuid = data.get('targetuuid', '')  # 替换uuid
    contentType = data.get('contenttype', '')

    if not all([moduleUuid, targetUuid, contentType in [1, 2, 3]]):
        return http_return(400, '参数错误')

    module = Module.objects.filter(uuid=moduleUuid, isDelete=False).first()
    if not module:
        return http_return(400, '没有对象')

    audioStory = None
    album = None
    type = module.type
    if contentType in [1, 2]:
        audioStory = AudioStory.objects.filter(Q(uuid=targetUuid) & q).exclude(checkStatus="checkFail").first()
        if not audioStory:
            return http_return(400, '没有对象')
        module = Module.objects.filter(isDelete=False, audioUuid=targetUuid, type=type, contentType=contentType).first()
        if module:
            return http_return(400, '已经添加')
    else:
        album = Album.objects.filter(uuid=targetUuid, isDelete=False,
                                     checkStatus__in=["check", "exemption"]).first()
        if not album:
            return http_return(400, '没有对象')
        module = Module.objects.filter(isDelete=False, albumUuid=targetUuid, type=type, contentType=contentType).first()
        if module:
            return http_return(400, '已经添加')

    module = Module.objects.filter(uuid=moduleUuid, isDelete=False).first()
    try:
        with transaction.atomic():
            module.audioUuid = audioStory
            module.albumUuid = album
            module.contentType = contentType
            module.save()
        return http_return(200, '替换成功')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '替换失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def del_story_in_module(request):
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    moduleUuid = data.get('moduleuuid', '')  # 要删除哪条uuid

    if not moduleUuid:
        return http_return(400, '参数错误')

    module = Module.objects.filter(uuid=moduleUuid, isDelete=False).first()
    if not module:
        return http_return(400, '没有对象')

    try:
        with transaction.atomic():
            module.isDelete = True
            module.save()
        return http_return(200, '删除成功')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '删除失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def change_module_order(request):
    """模块排序"""
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    moduleUuid = data.get('moduleuuid', '')
    direct = data.get('direct', '')

    if not all([moduleUuid, direct in ["up", "down"]]):
        return http_return(400, "参数错误")

    module = Module.objects.filter(uuid=moduleUuid, isDelete=False).first()
    if not module:
        return http_return(400, "没有对象")
    myOrderNum = module.orderNum
    type = module.type
    # 向上
    swapOrderNum = 0
    if direct == "up":
        # 比当前sortNum小的最大值
        swapOrderNum = \
        Module.objects.filter(orderNum__lt=myOrderNum, isDelete=False, type=type).aggregate(Max('orderNum'))[
            'orderNum__max']
        if not swapOrderNum:
            return http_return(400, "已经到顶了")
    elif direct == "down":
        # 比当前sortNum大的最小值
        swapOrderNum = \
        Module.objects.filter(orderNum__gt=myOrderNum, isDelete=False, type=type).aggregate(Min('orderNum'))[
            'orderNum__min']
        if not swapOrderNum:
            return http_return(400, "已经到底了")

    try:
        with transaction.atomic():
            swapModule = Module.objects.filter(orderNum=swapOrderNum, isDelete=False, type=type).first()
            module.orderNum, swapModule.orderNum = swapOrderNum, myOrderNum
            module.save()
            swapModule.save()
        return http_return(200, '修改成功')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '修改失败')


class UserView(ListAPIView):
    queryset = User.objects.exclude(status='destroy')
    serializer_class = UserDetailSerializer
    filter_class = UserFilter
    pagination_class = MyPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('-createTime',)
    ordering_fields = ('id', 'createTime')

    # 当前管理员不显示在用户列表里面
    # def get(self, request, *args, **kwargs):
    #     queryset = self.get_queryset().exclude(userID=request.user.userID)
    #     queryset = self.filter_queryset(queryset)
    #     page = self.paginate_queryset(queryset)
    #     if page is not None:
    #         serializer = self.get_serializer(page, many=True)
    #         return self.get_paginated_response(serializer.data)
    #
    #     serializer = self.get_serializer(queryset, many=True)
    #     return Response(serializer.data)

    def get_queryset(self):
        # 首先更新用户禁言禁止登录状态
        currentTime = datetime.now()
        # 到了生效时间
        # User.objects.filter(startTime__lt=currentTime, endTime__gt=currentTime, status="normal").\
        #     update(status=F("settingStatus"), updateTime=currentTime)
        # 过了结束时间
        User.objects.filter(endTime__lt=currentTime).exclude(status__in=["destroy", "normal"]). \
            update(status="normal", updateTime=currentTime, startTime=None, endTime=None, settingStatus=None)
        startTimestamp = self.request.query_params.get('starttime', '')
        endTimestamp = self.request.query_params.get('endtime', '')

        if (startTimestamp and not endTimestamp) or (not startTimestamp and endTimestamp):
            raise ParamsException('时间错误')
        if startTimestamp and endTimestamp:
            try:
                starttime, endtime = timestamp2datetime(startTimestamp, endTimestamp)
                self.queryset = self.queryset.filter(createTime__range=(starttime, endtime))
            except Exception as e:
                logging.error(str(e))
                raise ParamsException(e.detail)

        return self.queryset


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def validate_tel(request):
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    tel = data.get('tel', '')
    if not tel:
        return http_return(400, '手机号不能为空')
    if not re.match("^1[3456789]\d{9}$", tel):
        return http_return(400, '手机号码错误')

    # status 0 已经注册 1 迁移用户  2 新建用户
    user = User.objects.filter(tel=tel).exclude(status='destroy').first()
    if user:
        return http_return(200, 'OK', {'status': 0})

    # 2019年8月15日微信 沟通结果 删除的用户无法再从后台添加
    user = User.objects.filter(tel=tel, status='destroy').first()
    if user:
        return http_return(400, '此用户已删除，不允许添加')

    api = Api()
    userInfo = api.search_user_byphone(tel)
    if userInfo == -1:
        return http_return(400, '接口通信错误')
    if userInfo:
        return http_return(200, '迁移用户', {'status': 1})
    else:
        # 新用户
        return http_return(200, '新用户', {'status': 2})


# 迁移老用户
@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def migrate_user(request):
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    tel = data.get('tel', '')
    if not tel:
        return http_return(400, '手机号不能为空')
    if not re.match("^1[3456789]\d{9}$", tel):
        return http_return(400, '手机号码错误')

    user = User.objects.filter(tel=tel).exclude(status='destroy').first()
    if user:
        return http_return(400, '此手机号已经注册')

    nickName = data.get('nickName', '')
    city = data.get('city', '')
    roles = data.get('roles', '')
    gender = data.get('gender', '')

    if not all([gender in [0, 1, 2], nickName, roles in ['normalUser', 'adminUser']]):
        return http_return(400, '参数错误')

    if city:
        if not 1 < len(str(city)) < 40:
            return http_return(400, '城市长度错误')

    if not 1 < len(str(nickName)) < 20:
        return http_return(400, '昵称长度错误')

    if not isinstance(tel, str):
        tel = str(tel)

    # /api/sso/user/byphone 读取用户列表(手机号用户)
    api = Api()
    userID = ''
    userInfo = api.search_user_byphone(tel)
    if userInfo == -1:
        return http_return(400, '接口通信错误')
    if userInfo:
        userID = userInfo['userId']

    else:
        return http_return(400, '无法迁移用户')

    try:
        uuid = get_uuid()
        with transaction.atomic():
            User.objects.create(
                uuid=uuid,
                userID=userID,
                nickName=nickName or tel,
                avatar='https://hbb-ads.oss-cn-beijing.aliyuncs.com/file1111746672834.png',
                tel=tel,
                gender=gender,  # 性别 0未知  1男  2女
                status="normal",
                roles=roles,
                city=city
            )
        return http_return(200, '添加成功')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '添加失败')


# 添加新用户
@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def add_user(request):
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    tel = data.get('tel', '')
    if not tel:
        return http_return(400, '手机号不能为空')
    if not re.match("^1[3456789]\d{9}$", tel):
        return http_return(400, '手机号码错误')

    user = User.objects.filter(tel=tel).exclude(status='destroy').first()
    if user:
        return http_return(400, '此手机号已经注册')

    # 2019年8月15日微信 沟通结果 删除的用户无法再从后台添加
    user = User.objects.filter(tel=tel, status='destroy').first()
    if user:
        return http_return(400, '此用户已删除，不允许添加')

    nickName = data.get('nickName', '')
    city = data.get('city', '')
    roles = data.get('roles', '')
    gender = data.get('gender', '')
    pwd = data.get('pwd', '')

    if not all([gender in [0, 1, 2], nickName, roles in ['normalUser', 'adminUser'], pwd]):
        return http_return(400, '参数错误')

    if not 5 < len(str(pwd)) < 40:
        return http_return(400, '密码长度错误')

    if city:
        if not 1 < len(str(city)) < 40:
            return http_return(400, '城市长度错误')

    if not 1 < len(str(nickName)) < 20:
        return http_return(400, '昵称长度错误')

    if not isinstance(tel, str):
        tel = str(tel)

    # /api/sso/user/byphone 读取用户列表(手机号用户)
    api = Api()
    userID = ''
    userInfo = api.search_user_byphone(tel)
    if userInfo == -1:
        return http_return(400, '接口通信错误')
    if userInfo:
        # userID = userInfo['userId']
        return http_return(400, '此用户在其他平台已注册，请迁移用户')
    else:
        # /api/sso/createbyuserpasswd 管理员创建一个账号密码
        userInfo = api.create_user(tel, pwd)
        if userInfo == -1:
            return http_return(400, '接口通信错误')
        if userInfo:
            userID = userInfo
        else:
            return http_return(400, '创建用户失败')

    try:
        uuid = get_uuid()
        with transaction.atomic():
            User.objects.create(
                uuid=uuid,
                userID=userID,
                nickName=nickName or tel,
                avatar='https://hbb-ads.oss-cn-beijing.aliyuncs.com/file1111746672834.png',
                tel=tel,
                gender=gender,  # 性别 0未知  1男  2女
                status="normal",
                roles=roles,
                city=city
            )
        return http_return(200, '保存用户成功')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '保存用户失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def modify_user(request):
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')

    uuid = data.get('uuid', '')
    nickName = data.get('nickName', '')
    city = data.get('city', '')
    roles = data.get('roles', '')
    gender = data.get('gender', '')
    pwd = data.get('pwd', '')  # 没有填写密码则不用修改
    if not all([gender in [0, 1, 2], uuid, nickName, roles in ['normalUser', 'adminUser']]):
        return http_return(400, '参数错误')

    if city:
        if not 1 < len(str(city)) < 40:
            return http_return(400, '城市长度错误')

    if not 1 < len(str(nickName)) < 20:
        return http_return(400, '昵称长度错误')

    user = User.objects.filter(uuid=uuid).exclude(status="destroy").first()
    if not user:
        return http_return(400, '没有用户')

    if (not user.loginType == "USERPASSWD") or not user.loginType:
        if pwd:
            return http_return(400, '此用户不支持修改密码。')


    tel = user.tel
    if not tel:
        return http_return(400, '没有用户手机号')
    # 调用接口 管理员在后台 重置其他用户密码, 重置自己的密码清缓存
    if pwd:
        if not 5 < len(str(pwd)) < 40:
            return http_return(400, '密码长度错误')
        api = Api()
        if not api.admin_reset_pwd(tel, pwd, request.auth):
            return http_return(400, "重置密码失败")
        if request.user.uuid == uuid:
            caches['default'].delete(request.auth)

    data = {}
    if request.user.uuid == uuid:
        data['nickName'] = nickName
        if pwd:
            data['changepwd'] = 1
        else:
            data['changepwd'] = 0

    try:
        with transaction.atomic():
            user.roles = roles
            user.city = city
            user.nickName = nickName
            user.gender = gender
            user.save()
            return http_return(200, '修改成功', data)
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '修改失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def del_user(request):
    # 删除
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')

    if not uuid:
        return http_return(400, '参数错误')

    user = User.objects.filter(uuid=uuid).exclude(status='destroy').first()
    if not user:
        return http_return(400, '没有对象')

    try:
        with transaction.atomic():
            user.status = "destroy"
            user.save()
            return http_return(200, '删除成功')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '删除失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def forbidden_user(request):
    # 禁用
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')
    type = data.get('type', '')
    endTimestamp = data.get('endtime', '')

    # destroy  forbbiden_login  forbbiden_say
    if not all([endTimestamp, uuid, type in ["forbbiden_login", "forbbiden_say"]]):
        return http_return(400, '参数错误')

    if not isinstance(endTimestamp, int):
        return http_return(400, '时间格式错误')

    endTimestamp = int(endTimestamp) / 1000
    try:
        endTime = datetime.fromtimestamp(endTimestamp)
        currentTime = datetime.now()
        if currentTime >= endTime:
            return http_return(400, '结束时间错误')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '时间参数错误')

    user = User.objects.filter(uuid=uuid).exclude(status="destroy").first()
    if not user:
        return http_return(400, '没有对象')

    try:
        with transaction.atomic():
            user.startTime = currentTime
            user.endTime = endTime
            user.settingStatus = type
            user.status = type
            user.save()
            timeout = (endTime - currentTime).total_seconds()
            caches['api'].set(request.user.userID, type, timeout=timeout)
        return http_return(200, '添加成功')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '添加失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def cancel_forbid(request):
    # 恢复
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')

    user = User.objects.filter(uuid=uuid).exclude(status="destroy").first()
    if not user:
        return http_return(400, '没有对象')

    try:
        with transaction.atomic():
            user.startTime = None
            user.endTime = None
            user.settingStatus = None
            user.status = "normal"
            user.save()
            caches['api'].delete(request.user.userID)
        return http_return(200, '恢复成功')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '恢复失败')


# 配置轮播图
class CycleBannerView(ListAPIView):
    queryset = CycleBanner.objects.filter(isDelete=False)
    serializer_class = CycleBannerSerializer
    filter_class = CycleBannerFilter
    pagination_class = MyPagination

    def get_queryset(self):
        startTimestamp = self.request.query_params.get('starttime', '')
        endTimestamp = self.request.query_params.get('endtime', '')

        if (startTimestamp and not endTimestamp) or (not startTimestamp and endTimestamp):
            raise ParamsException('时间错误')
        if startTimestamp and endTimestamp:
            try:
                starttime, endtime = timestamp2datetime(startTimestamp, endTimestamp, convert=False)
                return self.queryset.exclude(Q(startTime__gt=endtime) & Q(endTime__gt=endtime) |
                                             Q(endTime__lt=starttime) & Q(startTime__lt=starttime))
            except Exception as e:
                logging.error(str(e))
                raise ParamsException(e.detail)

        return self.queryset


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def add_cycle_banner(request):
    # 添加轮播图
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    name = data.get('name', '')
    icon = data.get('icon', '')
    type = data.get('type', '')
    target = data.get('target', '')
    orderNum = data.get('orderNum', '')
    startTime = data.get('startTime', '')
    endTime = data.get('endTime', '')
    if not all([name, icon, type in range(0, 5), startTime, orderNum, endTime, target]):
        return http_return(400, '参数错误')
    if CycleBanner.objects.filter(name=name, isDelete=False).exists():
        return http_return(400, '重复标题')

    if CycleBanner.objects.filter(orderNum=orderNum, isDelete=False).exists():
        return http_return(400, '重复排序')

    if startTime > endTime:
        return http_return(400, '时间错误')

    if not all([isinstance(startTime, int), isinstance(endTime, int)]):
        return http_return(400, '时间错误')

    startTime = startTime / 1000
    endTime = endTime / 1000

    try:
        startTime = datetime.fromtimestamp(startTime)
        endTime = datetime.fromtimestamp(endTime)
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '时间参数错误')

    if type == 0:
        if not Activity.objects.filter(uuid=target, status='normal').exists():
            return http_return(400, '没有此活动')

    if type == 1:
        if not Album.objects.filter(uuid=target, isDelete=False, checkStatus__in=["check", "exemption"]).exists():
            return http_return(400, '没有此专辑')

    if type == 2:  # 音频
        if not AudioStory.objects.filter(Q(uuid=target) & q).exclude(checkStatus="checkFail").exists():
            return http_return(400, '没有此音频')

    if type == 4:  # 外部链接
        if not target.startswith('http'):
            return http_return(400, '跳转地址格式错误')

    try:
        uuid = get_uuid()
        CycleBanner.objects.create(
            uuid=uuid,
            name=name,
            type=type,
            startTime=startTime,
            endTime=endTime,
            orderNum=orderNum,
            target=target,
            location=0,
            icon=icon
        )
        return http_return(200, '添加成功')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '添加失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def modify_cycle_banner(request):
    # 修改轮播图
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')
    name = data.get('name', '')
    icon = data.get('icon', '')
    type = data.get('type', '')
    target = data.get('target', '')
    orderNum = data.get('orderNum', '')
    startTime = data.get('startTime', '')
    endTime = data.get('endTime', '')
    if not all([uuid, name, icon, type in range(0, 5), startTime, orderNum, endTime, target]):
        return http_return(400, '参数错误')

    cycleBanner = CycleBanner.objects.filter(uuid=uuid, isDelete=False).first()
    if not cycleBanner:
        return http_return(400, '没有对象')

    myName = cycleBanner.name
    myOrderNum = cycleBanner.orderNum

    if myName != name:
        if CycleBanner.objects.filter(name=name, isDelete=False).exists():
            return http_return(400, '重复标题')
    if myOrderNum != orderNum:
        if CycleBanner.objects.filter(orderNum=orderNum, isDelete=False).exists():
            return http_return(400, '重复排序')

    if startTime > endTime:
        return http_return(400, '时间错误')

    if not all([isinstance(startTime, int), isinstance(endTime, int)]):
        return http_return(400, '时间错误')

    startTime = startTime / 1000
    endTime = endTime / 1000

    try:
        startTime = datetime.fromtimestamp(startTime)
        endTime = datetime.fromtimestamp(endTime)
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '时间错误')

    if type == 0:
        if not Activity.objects.filter(uuid=target, status='normal').exists():
            return http_return(400, '没有此活动')

    if type == 1:
        if not Album.objects.filter(uuid=target, isDelete=False, checkStatus__in=["check", "exemption"]).exists():
            return http_return(400, '没有此专辑')

    if type == 2:  # 音频
        if not AudioStory.objects.filter(Q(uuid=target) & q).exclude(checkStatus="checkFail").exists():
            return http_return(400, '没有此音频')

    if type == 4:  # 外部链接
        if not target.startswith('http'):
            return http_return(400, '跳转地址格式错误')
    try:
        cycleBanner = CycleBanner.objects.filter(uuid=uuid, isDelete=False)
        cycleBanner.update(
            updateTime=datetime.now(),
            name=name,
            type=type,
            startTime=startTime,
            endTime=endTime,
            orderNum=orderNum,
            target=target,
            location=0,
            icon=icon
        )
        return http_return(200, '修改成功')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '修改失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def change_cycle_banner_status(request):
    # 停用/恢复/删除
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')
    type = data.get('type', '')

    if not all([uuid, type in ["stop", "recover", "delete"]]):
        return http_return(400, '参数错误')

    cycleBanner = CycleBanner.objects.filter(uuid=uuid, isDelete=False).first()
    if not cycleBanner:
        return http_return(400, '没有对象')

    try:
        with transaction.atomic():
            if type == "stop":
                cycleBanner.isUsing = False
            elif type == "recover":
                cycleBanner.isUsing = True
            elif type == "delete":
                cycleBanner.isDelete = True
            cycleBanner.save()
            return http_return(200, '删除成功')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '删除失败')


# 反馈管理列表
class FeedbackView(ListAPIView):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    filter_class = FeedbackFilter
    pagination_class = MyPagination

    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('-createTime',)
    ordering_fields = ('id', 'createTime')

    def get_queryset(self):
        startTimestamp = self.request.query_params.get('starttime', '')
        endTimestamp = self.request.query_params.get('endtime', '')

        if (startTimestamp and not endTimestamp) or (not startTimestamp and endTimestamp):
            raise ParamsException('时间错误')
        if startTimestamp and endTimestamp:
            try:
                starttime, endtime = timestamp2datetime(startTimestamp, endTimestamp)
                return self.queryset.filter(createTime__range=(starttime, endtime))
            except Exception as e:
                logging.error(str(e))
                raise ParamsException(e.detail)
        return self.queryset


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def reply(request):
    """后台回复"""
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    feedbackUuid = data.get('uuid', '')
    replyInfo = data.get('replyInfo', '')
    if not all([feedbackUuid, replyInfo]):
        return http_return(400, '参数错误')
    adminUserUuid = data['_cache'].get('uuid')
    if not adminUserUuid:
        return http_return(400, '没有管理员信息')

    # 后台可以多次回复
    feedback = Feedback.objects.filter(uuid=feedbackUuid).first()
    if not feedback:
        return http_return(400, '没有对象')

    if feedback.status == 1:
        oldReplyInfo = feedback.replyInfo
        if oldReplyInfo == replyInfo:
            return http_return(400, '两次回复消息一样')

    try:
        with transaction.atomic():
            feedback.replyInfo = replyInfo
            feedback.status = 1
            feedback.isRead = False
            feedback.save()
            # 记录哪个管理员回复了什么
            operationUuid = get_uuid()
            Operation.objects.create(
                uuid=operationUuid,
                adminUserUuid=adminUserUuid,
                operation='create',
                objectUuid=feedbackUuid,
                remark=replyInfo
            )
            return http_return(200, '回复成功')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '回复失败')


class NotificationView(ListAPIView):
    queryset = SystemNotification.objects.filter(isDelete=False).exclude(type__in=[4, 5])
    serializer_class = NotificationSerializer
    filter_class = NotificationFilter
    pagination_class = MyPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('-createTime',)
    ordering_fields = ('id', 'createTime')

    def get_queryset(self):
        startTimestamp = self.request.query_params.get('starttime', '')
        endTimestamp = self.request.query_params.get('endtime', '')

        if (startTimestamp and not endTimestamp) or (not startTimestamp and endTimestamp):
            raise ParamsException('时间错误')
        if startTimestamp and endTimestamp:
            try:
                starttime, endtime = timestamp2datetime(startTimestamp, endTimestamp)
                return self.queryset.filter(publishDate__range=(starttime, endtime))
            except Exception as e:
                logging.error(str(e))
                raise ParamsException(e.detail)
        return self.queryset



@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def add_notification(request):
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    title = data.get('title', '')
    content = data.get('content', '')
    publishDate = data.get('publishDate', '')  # 时间戳
    # 系统消息类型 1：后台通知（纯文本） 2：外部连接 3：活动邀请 4：审核信息
    type = data.get('type', '')
    linkAddress = data.get('linkAddress', '')
    linkText = data.get('linkText', '')
    activityUuid = data.get('activityUuid', '')  # 活动的uuid

    if not all([limit_of_text(content, 256), limit_of_text(title, 256)]):
        return http_return(400, "标题或内容格式错误或超出长度！")
    if not all([limit_of_text(linkAddress, 256), limit_of_text(linkText, 256)]):
        return http_return(400, "链接或链接地址格式错误或超出长度！")

    if not type in [1, 2, 3]:
        return http_return(400, "type字段错误")

    if not all([title, content, publishDate]):
        return http_return(400, "参数有空")

    if not limit_of_text(content, 256):
        return http_return(400, "消息内容格式错误或超出256个字符")

    # 使用百度接口审核title 、content文字内容
    text = TextAudit()
    res, msg = text.work_on(title + content)
    # 如果是int整数，则是百度接口的错误码
    if isinstance(res, int):
        if res == 18:
            return http_return(400, "请求接口频繁，请重试。")
        return http_return(400, msg)
    if res == "checkFail":
        if msg != "恶意推广":
            return http_return(400, "发布文字涉及违规信息，请重新编辑！")

    if type == 2:
        if not linkAddress:
            return http_return(400, "跳转地址不能为空")

        if not isinstance(linkAddress, str):
            return http_return(400, "格式错误")
        if not linkAddress.startswith("http"):
            return http_return(400, "跳转地址请以http或https开头")

    if SystemNotification.objects.filter(title=title).exists():
        return http_return(400, "重复活动标题")

    # 判断推送时间是否合法
    _, publishDate = timestamp2datetime(1, publishDate, convert=False)

    if (publishDate - datetime.now()).total_seconds() < 0:
        return http_return(400, "已过了发布时间，请重新填写发布时间。")

    # 临近时间推送，建议间隔5分钟
    if (publishDate-datetime.now()).total_seconds() < 5*60:
        return http_return(400, "临近发送时间，建议发送时间在未来5分钟以上。")

    if (publishDate - datetime.now()).days > 365:
        return http_return(400, "发布日期不要超过一年")

    # 跳转活动
    targetType = 4
    if type == 3:
        if not activityUuid:
            return http_return(400, "活动参数不能为空")
        targetType = 0
        activity = Activity.objects.filter(uuid=activityUuid, status="normal").first()
        if not activity:
            return http_return(400, "该活动不存在！")
        if activity.endTime < datetime.now():
            return http_return(400, "该活动已过期")
        if publishDate > activity.endTime:
            return http_return(400, "该发布时间活动已结束！")
        # 跳转的是活动则拼接活动路由
        linkAddress = urljoin(activity.url, activity.uuid) + "/false"

    # 默认此账号为  绘童团队
    # 绘童团度
    user = User.objects.filter(tel=HTTD).exclude(status="destroy").first()
    if user:
        httd = user.uuid
    else:
        httd = ""

    # ===================添加到极光定时推送  横幅 全部用户 定时 =================
    # {value: 0, label: "活动"},
    # {value: 1, label: "专辑"},
    # {value: 2, label: "音频"},
    # {value: 3, label: "商品"},
    # {value: 4, label: "链接"},
    # {value: 5, label: "模板"}
    timestr = time2str(publishDate)
    if JPUSH == "ON":
        try:
            extras = {"type": 0} # 这里的自定义消息type： 0 系统消息 1 关注 2 点赞 3 评论
            result = post_schedule_notification(title, content, extras, timestr, title)
            if result.status_code == 200:
                schedule_id = result.payload.get("schedule_id", "")
                publishState = 7
                if not schedule_id:
                    publishState = 8
                    return http_return(400, "极光推送错误，暂无法创建系统消息！")
            else:
                schedule_id = ""
                publishState = 8
                return http_return(400, "极光推送错误，暂无法创建系统消息！")
        except Exception as e:
            schedule_id = ""
            publishState = 8
            logging.error(str(e))
            return http_return(400, "极光推送错误，暂无法创建系统消息！")
    else:
        schedule_id = ""
        publishState = 0

    try:
        with transaction.atomic():
            uuid = get_uuid()
            SystemNotification.objects.create(
                uuid=uuid,
                userUuid=httd,
                title=title,
                content=content,
                publishDate=publishDate,
                linkAddress=linkAddress,
                linkText=linkText or linkAddress,
                type=type,
                targetType=targetType,  # 活动
                activityUuid=activityUuid,
                publishState=publishState,
                scheduleId=schedule_id,
                isDelete=False,
            )

            return http_return(200, '创建成功')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '创建失败')


# #  停用/启用
# @api_view(['POST'])
# @authentication_classes((CustomAuthentication,))
# def publish_notification(request):
#     data = request_body(request, 'POST')
#     if not data:
#         return http_return(400, '参数错误')
#     uuid = data.get('uuid', '')
#
#     if not uuid:
#         return http_return(400, '参数有误')
#     notification = SystemNotification.objects.filter(uuid=uuid, isDelete=False).first()
#     if not notification:
#         return http_return(400, '没有对象')
#     try:
#         with transaction.atomic():
#             # 1 已发布 2 未发布
#             notification.publishState = 2 if notification.publishState == 1 else 1
#             notification.save()
#             return http_return(200, '操作成功', {"status": notification.publishState})
#     except Exception as e:
#         logging.error(str(e))
#         return http_return(400, '操作失败')



# 编辑
@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def modify_notification(request):
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')
    title = data.get('title', '')
    content = data.get('content', '')
    publishDate = data.get('publishDate', '')  # 时间戳
    # 系统消息类型 1：后台通知（纯文本） 2：外部连接 3：活动邀请 4：审核信息
    type = data.get('type', '')
    linkAddress = data.get('linkAddress', '')
    linkText = data.get('linkText', '')
    activityUuid = data.get('activityUuid', '')  # 活动的uuid

    if not all([limit_of_text(content, 256), limit_of_text(title, 256)]):
        return http_return(400, "标题或内容格式错误或超出长度！")
    if not all([limit_of_text(linkAddress, 256), limit_of_text(linkText, 256)]):
        return http_return(400, "链接或链接地址格式错误或超出长度！")


    # 1.先判断参数是否合法
    if not type in [1, 2, 3]:
        return http_return(400, "type字段错误")

    if type == 1:
        linkAddress = ""
        linkText = ""
        activityUuid = ""

    if not all([title, content, publishDate, uuid]):
        return http_return(400, "参数有空")

    notification = SystemNotification.objects.filter(uuid=uuid, isDelete=False).first()
    if not notification:
        return http_return(400, "无此消息")

    # 不支持type字段修改
    if notification.type != type:
        return http_return(400, "不支持类型修改")

    # 2.此时此刻是否支持修改
    if (notification.publishDate - datetime.now()).total_seconds() < 0:
        return http_return(400, "过期消息，不支持修改")

    if (notification.publishDate - datetime.now()).total_seconds() < 5*60:
        return http_return(400, "临近发送，不支持修改")

    # 3. 判断参数逻辑
    if SystemNotification.objects.filter(title=title, isDelete=False).exclude(uuid=uuid).exists():
        return http_return(400, "重复活动标题")

    if not isinstance(content, str):
        return http_return(400, "消息内容格式需为字符串")

    if len(content) > 256:
        return http_return(400, "消息内容超出256个字符")

    if type == 2:
        if not linkAddress:
            return http_return(400, "跳转地址不能为空")

        if not isinstance(linkAddress, str):
            return http_return(400, "格式错误")
        if not linkAddress.startswith("http"):
            return http_return(400, "跳转地址请以http或https开头")


    # 4. 判断发布时间合法
    _, publishDate = timestamp2datetime(1, publishDate, convert=False)

    if (publishDate - datetime.now()).total_seconds() < 0:
        return http_return(400, "已过了发布时间，请重新填写发布时间。")

    # 临近时间推送，建议间隔5分钟
    if (publishDate - datetime.now()).total_seconds() < 5 * 60:
        return http_return(400, "临近发送时间，建议发送时间在未来5分钟以上。")

    if (publishDate - datetime.now()).days > 365:
        return http_return(400, "发布日期不要超过一年")

    # 跳转活动
    if type == 3:
        if not activityUuid:
            return http_return(400, "活动参数不能为空")
        activity = Activity.objects.filter(uuid=activityUuid, status="normal").first()
        if not activity:
            return http_return(400, "该活动不存在！")
        if activity.endTime < datetime.now():
            return http_return(400, "该活动已过期")
        if publishDate > activity.endTime:
            return http_return(400, "该发布时间活动已结束！")
        # 跳转的是活动则拼接活动路由
        linkAddress = urljoin(activity.url, activity.uuid) + "/false"

    # 使用百度接口审核title 、content文字内容
    text = TextAudit()
    res, msg = text.work_on(title + content)
    # 如果是int整数，则是百度接口的错误码
    if isinstance(res, int):
        if res == 18:
            return http_return(400, "请求接口频繁，请重试。")
        return http_return(400, msg)
    if res == "checkFail":
        if msg != "恶意推广":
            return http_return(400, "发布文字涉及违规信息，请重新编辑！")

    # =====================修改极光推送  修改定时的极光推送
    publishState = notification.publishState
    if notification.scheduleId:
        try:
            timestr = time2str(publishDate)
            extras = {"type": 0}
            result = put_schedule_notification(notification.scheduleId, content, title, extras, timestr, title)
            publishState = 3
            if result.status_code != 200:
                publishState = 4
                return http_return(400, "极光错误，暂无法修改")
            if result.payload.get("taskid") != notification.scheduleId:
                publishState = 4
                return http_return(400, "极光错误，暂无法修改")

        except Exception as e:
            publishState = 4
            logging.error(str(e))
            return http_return(400, "极光错误，暂无法修改")


    try:
        with transaction.atomic():
            notification.title = title
            notification.content = content
            notification.type = type
            notification.publishDate = publishDate
            notification.publishState = publishState
            notification.linkAddress = linkAddress
            notification.linkText = linkText
            notification.activityUuid = activityUuid
            notification.save()

            return http_return(200, '修改成功')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '创建失败')


# 删除
@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def del_notification(request):
    data = request_body(request, "POST")
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')
    if not uuid:
        return http_return(400, '参数为空')


    # 未删除未发布的消息，才可以删除
    notification = SystemNotification.objects.filter(uuid=uuid, isDelete=False).first()
    if not notification:
        return http_return(400, '没有对象')


    # 删除还没有发送的极光推送
    publishState = 0
    if notification.scheduleId:
        if (notification.publishDate-datetime.now()).total_seconds() > 5*60:
            try:
                result = delete_schedule(notification.scheduleId)
                if result.status_code == 200 and result.payload == 'success':
                    publishState = 5
                else:
                    publishState = 6
                    return http_return(400, "极光错误，暂无法删除")
            except Exception as e:
                publishState = 6
                logging.error(str(e))
                return http_return(400, "极光错误，暂无法删除")
        elif 5*60 > (notification.publishDate-datetime.now()).total_seconds()>0:
            publishState = 6
            return http_return(400, "临近极光发布时间，暂无法删除！")


    try:
        with transaction.atomic():
            notification.isDelete = True
            notification.publishState = publishState
            notification.save()
            return http_return(200, '删除成功')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '删除失败')


class AlbumView(ListAPIView):
    queryset = Album.objects.filter(isDelete=False, checkStatus__in=["check", "exemption"]). \
        prefetch_related('audioStory')
    serializer_class = AlbumSerializer
    filter_class = AlbumFilter
    pagination_class = MyPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('-createTime',)
    ordering_fields = ('id', 'createTime')

    def get_queryset(self):
        startTimestamp = self.request.query_params.get('starttime', '')
        endTimestamp = self.request.query_params.get('endtime', '')

        if (startTimestamp and not endTimestamp) or (not startTimestamp and endTimestamp):
            raise ParamsException('时间错误')
        if startTimestamp and endTimestamp:
            try:
                starttime, endtime = timestamp2datetime(startTimestamp, endTimestamp)
                return self.queryset.filter(createTime__range=(starttime, endtime))
            except Exception as e:
                logging.error(str(e))
                raise ParamsException(e.detail)
        return self.queryset


class AuthorAudioStoryView(ListAPIView):
    """只有此作者的音频 不包含已经添加的"""
    queryset = AudioStory.objects.filter(q).exclude(checkStatus="checkFail") \
        .select_related('bgm', 'userUuid') \
        .prefetch_related('tags').order_by('-createTime')

    serializer_class = AuthorAudioStorySerializer
    filter_class = AuthorAudioStoryFilter
    pagination_class = MyPagination

    def get_queryset(self):
        authorUuid = self.request.query_params.get('authoruuid', '')
        albumUuid = self.request.query_params.get('albumuuid', '')
        if not authorUuid:
            raise ParamsException('参数不能为空')
        user = User.objects.filter(uuid=authorUuid).exclude(status='destroy').first()
        if not user:
            raise ParamsException('没有此用户')
        album = Album.objects.filter(uuid=albumUuid, isDelete=False).first()
        if not album:
            raise ParamsException('没有此专辑')
        res = []
        audioStoryList = AlbumAudioStory.objects.filter(album=album)
        for audioStory in audioStoryList:
            res.append(audioStory.audioStory_id)
        return self.queryset.filter(userUuid=user).exclude(id__in=res)


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def add_album(request):
    # 创建专辑
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    title = data.get('title', '')
    intro = data.get('intro', '')
    faceIcon = data.get('faceicon', '')
    bgIcon = data.get('bgicon', '')
    authorUuid = data.get('authoruuid', '')
    tagsUuidList = data.get('tagsuuidlist', '')
    if not all([title, intro, faceIcon, authorUuid]):
        return http_return(400, '参数错误')

    if not limit_of_text(str(title), 14):
        return http_return(400, '名字长度超过14个字符')

    author = User.objects.exclude(status="destroy").filter(uuid=authorUuid).first()
    if not author:
        return http_return(400, '作者不存在')

    if Album.objects.filter(title=title, isDelete=False).exists():
        return http_return(400, '专辑名重复')

    tags = []
    for tagUuid in tagsUuidList:
        tag = Tag.objects.filter(uuid=tagUuid).first()
        if not tag:
            return http_return(400, '无效标签')
        tags.append(tag)

    try:
        uuid = get_uuid()
        with transaction.atomic():
            Album.objects.create(
                uuid=uuid,
                title=title,
                intro=intro,
                isManagerCreate=1,
                faceIcon=faceIcon,
                bgIcon=bgIcon,
                author=author,
                checkStatus="exemption",
                creator=request.user
            ).tags.add(*tags)
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '添加失败')
    return http_return(200, '添加成功')


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def modify_album(request):
    # 修改专辑
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    albumUuid = data.get('albumuuid', '')
    title = data.get('title', '')
    intro = data.get('intro', '')
    faceIcon = data.get('faceicon', '')
    bgIcon = data.get('bgicon', '')
    tagsUuidList = data.get('tagsuuidlist', '')
    if not all([albumUuid, title, intro, faceIcon]):
        return http_return(400, '参数错误')

    if not limit_of_text(str(title), 14):
        return http_return(400, '名字长度超过14个字符')

    if Album.objects.filter(title=title, isDelete=False).exclude(uuid=albumUuid).exists():
        return http_return(400, '专辑名重复')

    album = Album.objects.filter(uuid=albumUuid).first()
    if not album:
        return http_return(400, '没有专辑对象')

    tags = []
    for tagUuid in tagsUuidList:
        tag = Tag.objects.filter(uuid=tagUuid).first()
        if not tag:
            return http_return(400, '无效标签')
        tags.append(tag)

    try:
        with transaction.atomic():
            album.title = title
            album.intro = intro
            album.faceIcon = faceIcon
            album.bgIcon = bgIcon
            album.tags.clear()
            album.tags.add(*tags)
            album.save()
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '添加失败')
    return http_return(200, '添加成功')


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def album_tags(request):
    # 配置专辑标签
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    albumUuid = data.get('albumuuid', '')
    tagsUuidList = data.get('tagsuuidlist')
    if not tagsUuidList:
        return http_return(400, '标签参数有误')

    album = Album.objects.filter(uuid=albumUuid).first()
    if not album:
        return http_return(400, '没有专辑对象')

    tags = []
    for tagUuid in tagsUuidList:
        tag = Tag.objects.filter(uuid=tagUuid).first()
        if not tag:
            return http_return(400, '无效标签')
        tags.append(tag)

    try:
        with transaction.atomic():
            album.tags.clear()
            album.tags.add(*tags)
            album.save()
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '配置标签失败')
    return http_return(200, '配置标签成功')


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def del_album(request):
    # 删除专辑
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    albumUuid = data.get('albumuuid', '')

    album = Album.objects.filter(isDelete=False, uuid=albumUuid).first()
    if not album:
        return http_return(400, '没有专辑对象')

    """删除专辑 影响到的范围 """
    module = Module.objects.filter(albumUuid=album, isDelete=False).first()
    if module:
        return http_return(400, '该专辑已关联模块配置')
    # 音频关联广告
    ad = Ad.objects.filter(target=albumUuid, isDelete=False).first()
    if ad:
        return http_return(400, '该专辑已关联广告')
    # 音频关联轮播图
    banner = CycleBanner.objects.filter(target=albumUuid, isDelete=False).first()
    if banner:
        return http_return(400, '该专辑已关联轮播图')

    try:
        with transaction.atomic():
            album.isDelete = True
            album.save()
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '删除失败')
    return http_return(200, '删除成功')


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def add_audio2album(request):
    # 专辑添加音频
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    albumUuid = data.get('albumuuid', '')
    audioStoryUuidList = data.get('audiostoryuuidlist', '')

    if not all([albumUuid, audioStoryUuidList]):
        return http_return(400, '参数有误')

    album = Album.objects.filter(isDelete=False, uuid=albumUuid, checkStatus__in=["check", "exemption"]).first()
    if not album:
        return http_return(400, '没有专辑对象')

    audioStoryList = []
    for audioStoryUuid in audioStoryUuidList:
        audioStory = AudioStory.objects.filter(Q(uuid=audioStoryUuid) & q).exclude(checkStatus="checkFail").first()
        if not audioStory:
            return http_return(400, '没有音频对象')

        if album.author != audioStory.userUuid:
            return http_return(400, "专辑里音频作者不统一")

        if AlbumAudioStory.objects.filter(album=album, audioStory=audioStory).exists():
            return http_return(400, "专辑里已添加此音乐", {"duplicateUuid": audioStoryUuid})

        audioStoryList.append(audioStory)

    try:
        with transaction.atomic():
            for audioStory in audioStoryList:
                uuid = get_uuid()
                AlbumAudioStory.objects.create(
                    uuid=uuid,
                    album=album,
                    audioStory=audioStory)
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '专辑添加音乐失败')
    return http_return(200, '专辑添加音乐成功')


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def disable_audioStoty_in_album(request):
    # 停用恢复专辑里的音频
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    albumUuid = data.get('albumuuid', '')
    audioStoryUuid = data.get('audiostoryuuid', '')
    # isUsing = data.get('isusing', '')

    if not all([albumUuid, audioStoryUuid]):
        return http_return(400, '参数有误')
    album = Album.objects.filter(uuid=albumUuid).first()
    if not album:
        return http_return(400, '没有专辑对象')

    audioStory = AudioStory.objects.filter(uuid=audioStoryUuid).first()
    if not audioStory:
        return http_return(400, '没有音频对象')

    audioStotyInAlbum = AlbumAudioStory.objects.filter(album=album, audioStory=audioStory).first()

    try:
        with transaction.atomic():
            audioStotyInAlbum.isUsing = int(not audioStotyInAlbum.isUsing)
            audioStotyInAlbum.save()
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '操作失败')
    return http_return(200, '操作成功', {"isUsing": audioStotyInAlbum.isUsing})


# class AlbumDetailView(ListAPIView):
#     queryset = AlbumAudioStory.objects.all().order_by('createTime')
#     serializer_class = AlbumAudioStoryDetailSerializer
#     pagination_class = MyPagination
#
#     def get_queryset(self):
#         albumUuid = self.request.query_params.get('albumuuid', '')
#         album = Album.objects.filter(uuid=albumUuid).first()
#         if not album:
#             return http_return(400, '没有专辑对象')
#         return self.queryset.filter(album=album)
#
#     def get(self, request, *args, **kwargs):
#         albumUuid = self.request.query_params.get('albumuuid', '')
#         album = Album.objects.filter(uuid=albumUuid).first()
#         if not album:
#             return http_return(400, '没有专辑对象')
#         self.queryset = self.queryset.filter(album=album)
#         pg = MyPagination()
#         page_data = pg.paginate_queryset(queryset=self.queryset,request=request,view=self)
#         ser = AlbumAudioStoryDetailSerializer(instance=page_data, many=True)
#         res = {}
#         res['audioList'] = ser.data
#         res['albumInfo'] = {'intro': '我是专辑介绍'}
#         return Response(res)


@api_view(['GET'])
@authentication_classes((CustomAuthentication,))
def album_detail(request):
    # 专辑详情
    data = request_body(request, 'GET')
    if not data:
        return http_return(400, '参数错误')
    albumUuid = data.get('albumuuid', '')

    album = Album.objects.filter(uuid=albumUuid).first()
    if not album:
        return http_return(400, '没有专辑对象')

    return Response(AlbumDetailSerializer(album).data)


class CheckAlbumView(ListAPIView):
    queryset = Album.objects.filter(isDelete=False).prefetch_related('tags')
    serializer_class = CheckAlbumSerializer
    filter_class = AlbumFilter
    pagination_class = MyPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('-createTime',)
    ordering_fields = ('id', 'createTime')

    def get_queryset(self):
        startTimestamp = self.request.query_params.get('starttime', '')
        endTimestamp = self.request.query_params.get('endtime', '')

        if (startTimestamp and not endTimestamp) or (not startTimestamp and endTimestamp):
            raise ParamsException('时间错误')
        if startTimestamp and endTimestamp:
            try:
                starttime, endtime = timestamp2datetime(startTimestamp, endTimestamp)
                return self.queryset.filter(createTime__range=(starttime, endtime))
            except Exception as e:
                logging.error(str(e))
                raise ParamsException(e.detail)
        return self.queryset


@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def check_album(request):
    # 审核专辑
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    albumUuid = data.get('albumuuid', '')
    checkStatus = data.get('checkstatus')

    if checkStatus not in ["check", "checkFail"]:
        return http_return(400, '参数无效')

    album = Album.objects.filter(isDelete=False, uuid=albumUuid, checkStatus="unCheck").first()
    if not album:
        return http_return(400, '没有此专辑或已被审核')

    try:
        with transaction.atomic():
            album.checkStatus = checkStatus
            album.save()
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '审核失败')
    return http_return(200, '审核成功！')


# 显示评论列表  评论用户 时间范围  审核状态  评论内容
class CommentView(ListAPIView):
    queryset = Behavior.objects.filter(type=2, isDelete=False)
    serializer_class = CommentSerializer
    filter_class = CommentFilter
    pagination_class = MyPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('-createTime',)
    ordering_fields = ('id', 'createTime')

    def get_queryset(self):
        startTimestamp = self.request.query_params.get('starttime', '')
        endTimestamp = self.request.query_params.get('endtime', '')

        if (startTimestamp and not endTimestamp) or (not startTimestamp and endTimestamp):
            raise ParamsException('时间错误')
        if startTimestamp and endTimestamp:
            try:
                starttime, endtime = timestamp2datetime(startTimestamp, endTimestamp)
                return self.queryset.filter(createTime__range=(starttime, endtime))
            except Exception as e:
                logging.error(str(e))
                raise ParamsException(e.detail)
        return self.queryset


# 审核 通过/不通过
@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def check_comment(request):
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')
    checkStatus = data.get('checkStatus')

    if checkStatus not in ["check", "checkFail"]:
        return http_return(400, '参数无效')

    comment = Behavior.objects.filter(type=2, isDelete=False, uuid=uuid).\
        exclude(adminStatus__in=["check", "checkFail"]).first()

    if not comment:
        return http_return(400, '没有此评论')

    try:
        with transaction.atomic():
            comment.adminStatus = checkStatus
            comment.save()
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '审核失败')
    return http_return(200, '审核成功！')

# 删除
@api_view(['POST'])
@authentication_classes((CustomAuthentication,))
def del_comment(request):
    # 删除专辑
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')

    comment = Behavior.objects.filter(type=2, isDelete=False, uuid=uuid).first()
    if not comment:
        return http_return(400, '没有此评论')

    try:
        with transaction.atomic():
            comment.isDelete = True
            comment.save()
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '删除失败')
    return http_return(200, '删除成功')


