#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Create your views here.
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import authentication, viewsets, mixins
from rest_framework.decorators import authentication_classes, api_view, action
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from api.apiCommon import get_default_name
from manager.auths import CustomAuthentication
from manager.filters import StoryFilter, FreedomAudioStoryInfoFilter, CheckAudioStoryInfoFilter, AudioStoryInfoFilter, \
    UserSearchFilter, BgmFilter, HotSearchFilter, UserFilter, ActivityFilter, CycleBannerFilter, \
    AdFilter, FeedbackFilter, QualifiedAudioStoryInfoFilter
from manager.models import *
from manager.managerCommon import *
from manager.paginations import MyPagination
from manager.serializers import StorySerializer, FreedomAudioStoryInfoSerializer, CheckAudioStoryInfoSerializer, \
    AudioStoryInfoSerializer, TagsSimpleSerialzer, StorySimpleSerializer, UserSearchSerializer, BgmSerializer, \
    HotSearchSerializer, AdSerializer, ModuleSerializer, UserDetailSerializer, \
    AudioStorySimpleSerializer, ActivitySerializer, CycleBannerSerializer, FeedbackSerializer, TagsChildSerialzer, \
    TagsSerialzer, QualifiedAudioStoryInfoSerializer
from common.api import Api
from django.db.models import Count, Q, Max, Min, F
from datetime import datetime, timedelta
from utils.errors import ParamsException


def admin(request):
    """
    后台路由测试
    :param request:
    :return:
    """
    return http_return(200, 'ok')

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
        user = User.objects.filter(userID=user_info.get('userId', ''), roles='adminUser').\
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
                uuid = get_uuid(),
                ipAddr = loginIp,
                userUuid = user,
                userAgent=request.META.get('HTTP_USER_AGENT', ''),
                isManager=True
            )
            loginLog.save()

        except Exception as e:
            logging.error(str(e))
            return http_return(401, '登陆失败')
        nickName = user.nickName or get_default_name(user.tel, '')
        return http_return(200, 'OK', {'nickName':nickName, 'roles': role})
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
                    return http_return(200, 'OK', {'nickName': nickName, 'roles': role})
            except Exception as e:
                logging.error(str(e))
                return http_return(400, '保存日志失败')



"""
首页数据
"""
@api_view(['POST'])
@authentication_classes((CustomAuthentication, ))
def total_data(request):
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    # 前端传入毫秒为单位的时间戳
    startTimestamp = data.get('startTime', '')
    endTimestamp = data.get('endTime', '')

    if not all([startTimestamp, endTimestamp]): # 最近7天数据，不包含今天的数据
        currentTime =timezone.now()
        t1 = currentTime + timedelta(days=-8)
        t2 = currentTime + timedelta(days=-1)
        t1 = datetime(t1.year, t1.month, t1.day)
        t2 = datetime(t2.year, t2.month, t2.day, 23, 59, 59, 999999)
    else:
        try:
            t1,t2 = timestamp2datetime(startTimestamp, endTimestamp)
        except Exception as e:
            logging.error(str(e))
            return http_return(e.status_code, e.detail)

        # 结束小于2019-05-30 00:00:00的时间不合法
        if t2 < datetime(2019, 5, 30):
            return http_return(200, '此时间没有数据', {'status':1})


        if (t2-t1).days > 31:
            return http_return(400, '超出时间范围')

    # 用户总人数
    totalUsers = User.objects.exclude(status='destroy').count()
    # 音频总数
    totalAudioStory = AudioStory.objects.filter(isDelete=False, isUpload=1,
                                                checkStatus__in=["check", "exemption"]).count()
    # 专辑总数
    totalAlbums = Album.objects.filter(isDelete=False).count()
    # 新增用户人数
    newUsers = User.objects.filter(createTime__range=(t1, t2)).exclude(status='destroy').count()
    # 活跃用户人数
    activityUsers = LoginLog.objects.filter(createTime__range=(t1, t2), isManager=False).values('userUuid_id').\
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
    aduioStoryCount = AudioStory.objects.filter(
        isDelete=False, audioStoryType=1, isUpload=1, createTime__range=(t1, t2),
        checkStatus__in=["check", "exemption"]).count()

    # 自由录制
    freedomStoryCount = AudioStory.objects.filter(
        isDelete=False, audioStoryType=0, isUpload=1, createTime__range=(t1, t2),
        checkStatus='check').count()

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
                            for name,tagsNum,userNum in zip(tagNameList, tagsNumList, userNumList)
                            ]

    # 活跃用户排行
    data1_list = []
    # result = AudioStory.objects.filter(isDelete=False, createTime__range=(t1, t2)).values('userUuid_id').annotate(Count('userUuid_id'))[:1]
    res = User.objects.annotate(audioStory_count_by_user = Count("useAudioUuid")).order_by('-audioStory_count_by_user')[:5]
    for index,item in enumerate(res.values()):
        data = {
            'orderNum': index+1,
            'name': item['nickName'],
            'recordCount': item['audioStory_count_by_user']
        }
        data1_list.append(data)
    # 热门录制排行
    data2_list = []
    res = Story.objects.filter(status="normal", createTime__range=(t1, t2)).order_by('-recordNum')[:5]
    for index,item in enumerate(res.values()):
        data = {
            'orderNum': index + 1 or -1,
            'name': item['name'] or '',
            'recordNum': item['recordNum'] or 0
        }
        data2_list.append(data)

    # 热门播放排行
    data3_list = []
    audioStory = AudioStory.objects.filter(isDelete=False, createTime__range=(t1, t2), isUpload=1).order_by('-playTimes')[:5]
    for index,item in enumerate(audioStory):
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
        graphList.append({'time':d.strftime("%m-%d"), 'userNum':0})
        d += delta


    # 图表数据--新增用户
    graph1 = User.objects.filter(createTime__range=(t1, t2)). \
        only('createTime', 'id'). \
        extra(select={"time": "DATE_FORMAT(createTime,'%%m-%%d')"}).\
        order_by('time').values('time')\
        .annotate(userNum=Count('createTime')).values('time', 'userNum')
    # if graph1:
    #     graph1 = list(graph1)
    # else:
    #     graph1 = []
    if graph1:
        graph1 = list(graph1)
        res1 = graphList[:]
        for item in graph1:
            res1.remove({'time':item['time'], 'userNum':0})
        res1.extend(graph1)
        res1 = sorted(res1, key=lambda s: s['time'], reverse=False)
    else:
        res1 = graphList

    # 活跃用户
    graph2 = LoginLog.objects.filter(createTime__range=(t1, t2), isManager=False).\
        only('time', 'userUuid_id'). \
        extra(select={"time": "DATE_FORMAT(createTime,'%%m-%%d')"}). \
        values('time').annotate(userNum=Count('userUuid_id', distinct=True)).\
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


    return http_return(200, 'OK',
                       {
                           'totalUsers': totalUsers,            # 总用户人数
                           'totalAudioStory': totalAudioStory,  # 音频总数
                           'totalAlbums': totalAlbums,          # 总的专辑数
                           'newUsers': newUsers,                # 新增用户人数
                           'activityUsers': activityUsers,      # 活跃用户人数
                           'newAudioStory': newAudioStory,      # 新增音频数
                           'activityUsersRank': data1_list,     # 活跃用户排行
                           'male': male,                         # 男性
                           'female': female,                     # 女性
                           'unkonwGender': unkonwGender,        # 未知性别
                           'aduioStoryCount': aduioStoryCount,  # 模板音频数量
                           'freedomStoryCount': freedomStoryCount,  # 自由录制音频数量
                           'recordTypePercentage': recordTypePercentage,
                           'hotRecordRank': data2_list,         # 热门录制排行
                           'hotPlayAudioStoryRank': data3_list,     # 热门播放排行
                           'newUserGraph': res1,              # 新增用户折线图
                           'activityUserGraph': res2,         # 活跃用户折线图
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
@authentication_classes((CustomAuthentication, ))
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
    if sortNum <= 0 :
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
            return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '添加分类失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication, ))
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
            tag.name = myName       # 保存的还是老标签，一级标签不能修改
            tag.save()
            return http_return(200, 'OK', {
                'name': myName,
                'icon': icon,
                'sortNum': sortNum,
            })

    except Exception as e:
        logging.error(str(e))
        return http_return(400, '修改分类失败')



@api_view(['POST'])
@authentication_classes((CustomAuthentication, ))
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
            return http_return(200, 'OK', {"status":tag.isUsing})
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '保存分类失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication, ))
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
            return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '删除分类失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication, ))
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
    #创建新标签
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
            return http_return(200, 'OK', {
                'uuid': uuid,
                'name': name,
                'sortNum': sortNum,
                'parentUuid': parentUuid
            })
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '保存失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication, ))
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

    if sortNum != mySortNum:
        tag = Tag.objects.filter(sortNum=sortNum, code='SEARCHSORT', isDelete=False, parent_id__isnull=False).first()
        if tag:
            return http_return(400, '重复序号')
    parentTag = Tag.objects.filter(uuid=parentUuid, code='SEARCHSORT', isDelete=False, parent_id__isnull=True).first()
    if not parentTag:
        return http_return(400, '参数有误')

    if name != myName:
        tag = Tag.objects.filter(name=name, code='SEARCHSORT', isDelete=False, parent_id__isnull=False).first()
        if tag:
            return http_return(400, '重复标签')
    tag = Tag.objects.filter(uuid=uuid).first()
    try:
        with transaction.atomic():
            tag.sortNum = sortNum
            tag.name = name
            tag.save()
            return http_return(200, 'OK', {
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
    queryset = Tag.objects.filter(code='SEARCHSORT', parent__name='类型', isDelete=False).\
        only('id', 'name', 'sortNum', 'uuid').all()
    serializer_class = TagsSimpleSerialzer
    pagination_class = MyPagination



# 获取所有子标签
class ChildTagView(ListAPIView):
    queryset = Tag.objects.filter(code='SEARCHSORT', parent_id__isnull=False, isDelete=False).\
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

        if (startTimestamp and not endTimestamp) or  (not startTimestamp and endTimestamp):
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
@authentication_classes((CustomAuthentication, ))
def add_story(request):
    """添加模板"""
    data = request_body(request, "POST")
    if not data:
        return http_return(400, '参数错误')
    faceIcon = data.get('faceIcon', '')
    listIcon = data.get('listIcon', '') # 非必填
    name = data.get('name', '')
    intro = data.get('intro', '')
    content = data.get('content', '')
    isRecommd = data.get('isRecommd', '')
    isTop = data.get('isTop', '')

    # all 都为True 才返回True
    if not all([name, faceIcon, content, intro, isRecommd, isTop]):
        return http_return(400, '参数有误')

    story = Story.objects.filter(name=name).exclude(status = 'destroy').first()
    if story:
        return http_return(400, '重复模板名')

    try:
        with transaction.atomic():
            uuid = get_uuid()
            story = Story(
                uuid = uuid,
                faceIcon = faceIcon,
                listIcon = listIcon,
                name = name,
                intro = intro,
                content = content,
                isRecommd = isRecommd,
                isTop = isTop,
                recordNum = 0
            )
            story.save()
            return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '添加模板失败')



@api_view(['POST'])
@authentication_classes((CustomAuthentication, ))
def modify_story(request):
    """修改模板"""
    data = request_body(request, "POST")
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')
    faceIcon = data.get('faceIcon', '')
    listIcon = data.get('listIcon', '') # 非必填
    name = data.get('name', '')
    intro = data.get('intro', '')
    content = data.get('content', '')
    isRecommd = data.get('isRecommd', '')
    isTop = data.get('isTop', '')

    # all 都为True 才返回True
    if not all([faceIcon, name, content, intro, isRecommd, isTop]):
        return http_return(400, '参数有误')

    story = Story.objects.filter(uuid=uuid).exclude(status = 'destroy').first()
    if not story:
        return http_return(400, '没有对象')

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
            return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '添加模板失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication, ))
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
            return http_return(200, 'OK', {"status": story.status})
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '改变模板状态失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication, ))
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
            return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '删除模板失败')


class AudioStoryInfoView(ListAPIView):
    """模板音频"""
    queryset = AudioStory.objects.filter(Q(isDelete=False), Q(audioStoryType=1),Q(isUpload=1),
                                         Q(checkStatus='check')|Q(checkStatus='exemption'))\
        .select_related('bgm', 'userUuid')\
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
        nickName = self.request.query_params.get('nickName', '')    # 用户名
        tag = self.request.query_params.get('tag', '')      # 类型标签

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
@authentication_classes((CustomAuthentication, ))
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
    type = data.get('type', '')         # 录制形式 0宝宝录制 1爸妈录制
    tagsUuidList = data.get('tagsuuidlist', '')

    if not all([storyUuid, userUuid, remarks, url, duration, tagsUuidList, type in [0, 1]]):
        return http_return(400, '参数不能为空')

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
            audioStoryType=1, # 1模板录制 0 自由音频
            type=type,
            name= story.name,
            bgIcon= story.faceIcon,
            storyUuid=story,
            remarks=remarks,
            duration=duration,
            checkStatus="exemption"
        ).tags.add(*tags)
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '添加失败')
    return http_return(200, 'OK')



class FreedomAudioStoryInfoView(ListAPIView):
    """自由音频"""
    queryset = AudioStory.objects.filter(isDelete=False, audioStoryType=0, isUpload=1,
                                         checkStatus='check') \
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
        nickName = self.request.query_params.get('nickName', '')    # 用户名
        tag = self.request.query_params.get('tag', '')      # 类型标签


        if (startTimestamp and not endTimestamp) or  (not startTimestamp and endTimestamp):
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
    queryset = AudioStory.objects.filter(isDelete=False, isUpload=1 )\
        .select_related('bgm', 'userUuid')\
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
        nickName = self.request.query_params.get('nickName', '')    # 用户名

        if (startTimestamp and not endTimestamp) or  (not startTimestamp and endTimestamp):
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
    queryset = AudioStory.objects.filter(isDelete=False, isUpload=1,checkStatus__in=["check", "exemption"])\
        .select_related('bgm', 'userUuid')\
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
        nickName = self.request.query_params.get('nickName', '')    # 用户名

        if (startTimestamp and not endTimestamp) or  (not startTimestamp and endTimestamp):
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
@authentication_classes((CustomAuthentication, ))
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

    try:
        with transaction.atomic():
            audioStory.checkStatus = checkStatus
            audioStory.save()
        return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '添加失败')



@api_view(['POST'])
@authentication_classes((CustomAuthentication, ))
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
                return http_return(200, 'OK')
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
            return http_return(200, 'OK')
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

        if (startTimestamp and not endTimestamp) or  (not startTimestamp and endTimestamp):
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
@authentication_classes((CustomAuthentication, ))
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
                sortNum=maxSortNum+1,
                duration=duration,
            )
        return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '添加失败')



@api_view(['POST'])
@authentication_classes((CustomAuthentication, ))
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
            bgm.url=url
            bgm.name=name
            bgm.sortNum=sortNum
            bgm.duration=duration
            bgm.save()

        return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '修改失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication, ))
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
        swapSortNum = Bgm.objects.filter(sortNum__lt=mySortNum).exclude(status="destroy").aggregate(Max('sortNum'))['sortNum__max']
        if not swapSortNum:
            return http_return(400, "已经到顶了")
    elif direct == "down":
        # 比当前sortNum大的最小值
        swapSortNum = Bgm.objects.filter(sortNum__gt=mySortNum).exclude(status="destroy").aggregate(Min('sortNum'))['sortNum__min']
        if not swapSortNum:
            return http_return(400, "已经到底了")

    try:
        with transaction.atomic():
            swapBgm = Bgm.objects.filter(sortNum=swapSortNum).exclude(status="destroy").first()
            bgm.sortNum, swapBgm.sortNum = swapSortNum, mySortNum
            bgm.save()
            swapBgm.save()
        return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '修改失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication, ))
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
            if status=="normal":
                bgm.status = "normal"
            elif status=="forbid":
                bgm.status = "forbid"
            else:
                return http_return(400, '参数错误')
            bgm.save()
        return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '修改失败')



@api_view(['POST'])
@authentication_classes((CustomAuthentication, ))
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
        return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '删除失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication, ))
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
        return http_return(400, '改背景音乐在作品中使用')
    try:
        # forbid 停用 normal正常 在用  destroy 删除
        bgm = Bgm.objects.filter(uuid=uuid).exclude(status="destroy").first()
        with transaction.atomic():
            bgm.status = "destroy"
            bgm.save()
        return http_return(200, 'OK')
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
@authentication_classes((CustomAuthentication, ))
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
            uuid = uuid,
            keyword = keyword,
            searchNum = 0,
            isAdminAdd = True
        )
        return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '添加失败')



@api_view(['POST'])
@authentication_classes((CustomAuthentication, ))
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
        return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '置顶失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication, ))
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
        return http_return(200, 'OK')
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

        if (startTimestamp and not endTimestamp) or  (not startTimestamp and endTimestamp):
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
@authentication_classes((CustomAuthentication, ))
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

    startTime = startTime/1000
    endTime = endTime/1000

    try:
        startTime = datetime.fromtimestamp(startTime)
        endTime = datetime.fromtimestamp(endTime)
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '时间格式错误')

    if type == 0:
        if not Activity.objects.filter(uuid=target).exists():
            return http_return(400, '没有此活动')

    if type == 2:  # 音频
        if not AudioStory.objects.filter(uuid=target).exists():
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
        return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '添加失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication, ))
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

    startTime = startTime/ 1000
    endTime = endTime/ 1000

    try:
        startTime = datetime.fromtimestamp(startTime)
        endTime = datetime.fromtimestamp(endTime)
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '时间格式错误')

    if type == 0:
        if not Activity.objects.filter(uuid=target).exists():
            return http_return(400, '没有此活动')

    if type == 2: # 音频
        if not AudioStory.objects.filter(uuid=target).exists():
            return http_return(400, '没有此音频')

    if type == 4: # 外部链接
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
        return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '修改失败')



@api_view(['POST'])
@authentication_classes((CustomAuthentication, ))
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
            return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '删除失败')



# 模块配置
class ModuleView(ListAPIView):
    """显示模块类型 MOD1每日一读  MOD2抢先听  MOD3热门推荐"""
    queryset = Module.objects.filter(isDelete=False, audioUuid__isDelete=False).\
        select_related('audioUuid').order_by('orderNum')
    serializer_class = ModuleSerializer
    # pagination_class = MyPagination

    def get_queryset(self):
        type = self.request.query_params.get('type', '')
        if type not in ['MOD1', 'MOD2', 'MOD3']:
            raise ParamsException({'code': 400, 'msg': '参数错误'})
        return self.queryset.filter(type=type)


# 显示所有作品的简单信息
class AllAudioSimpleView(ListAPIView):
    queryset = AudioStory.objects.filter(
        Q(isDelete=False),Q(isUpload=1),Q(checkStatus='check')|Q(checkStatus='exemption')).order_by('-createTime')
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
@authentication_classes((CustomAuthentication, ))
def add_story_into_module(request):
    """新增"""
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    type = data.get('type', '')
    audioUuid = data.get('audiouuid', '')
    if not all([type in ['MOD1', 'MOD2', 'MOD3'], audioUuid]):
        return http_return(400, '参数错误')

    audioStory = AudioStory.objects.filter(Q(isDelete=False), Q(uuid=audioUuid),Q(isUpload=1),
                                           Q(checkStatus='check')|Q(checkStatus='exemption')).first()
    if not audioStory:
        return http_return(400, '没有对象')

    module = Module.objects.filter(isDelete=False, audioUuid=audioStory, type=type).first()
    if module:
        return http_return(400, '已经添加')

    maxOrderNum = Module.objects.filter(isDelete=False, type=type).aggregate(Max('orderNum'))['orderNum__max'] or 0
    try:
        with transaction.atomic():
            uuid = get_uuid()
            Module.objects.create(
                uuid=uuid,
                type=type,
                orderNum=maxOrderNum+1,
                audioUuid=audioStory,
            )
        return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '添加失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication, ))
def change_story_in_module(request):
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    moduleUuid = data.get('moduleuuid', '')              # 要替换哪条uuid
    audioUuid = data.get('audiouuid', '')                # 替换成哪个音频

    if not all([moduleUuid, audioUuid]):
        return http_return(400, '参数错误')

    module = Module.objects.filter(uuid=moduleUuid, isDelete=False).first()
    if not module:
        return http_return(400, '没有对象')

    audioStory = AudioStory.objects.filter(Q(isDelete=False), Q(uuid=audioUuid),Q(isUpload=1),
                                         Q(checkStatus='check')|Q(checkStatus='exemption')).first()
    if not audioStory:
        return http_return(400, '没有对象')

    # 替换的对象在这个模块中是否存在
    type = module.type
    module2 = Module.objects.filter(isDelete=False, audioUuid=audioStory, type=type).first()
    if module2:
        return http_return(400, '已经添加')

    try:
        with transaction.atomic():
            module.audioUuid = audioStory
            module.save()
        return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '替换失败')



@api_view(['POST'])
@authentication_classes((CustomAuthentication, ))
def del_story_in_module(request):
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    moduleUuid = data.get('moduleuuid', '')              # 要删除哪条uuid

    if not moduleUuid:
        return http_return(400, '参数错误')

    module = Module.objects.filter(uuid=moduleUuid, isDelete=False).first()
    if not module:
        return http_return(400, '没有对象')


    try:
        with transaction.atomic():
            module.isDelete = True
            module.save()
        return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '删除失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication, ))
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
        swapOrderNum = Module.objects.filter(orderNum__lt=myOrderNum, isDelete=False, type=type).aggregate(Max('orderNum'))['orderNum__max']
        if not swapOrderNum:
            return http_return(400, "已经到顶了")
    elif direct == "down":
        # 比当前sortNum大的最小值
        swapOrderNum = Module.objects.filter(orderNum__gt=myOrderNum, isDelete=False, type=type).aggregate(Min('orderNum'))['orderNum__min']
        if not swapOrderNum:
            return http_return(400, "已经到底了")

    try:
        with transaction.atomic():
            swapModule = Module.objects.filter(orderNum=swapOrderNum, isDelete=False, type=type).first()
            module.orderNum, swapModule.orderNum = swapOrderNum, myOrderNum
            module.save()
            swapModule.save()
        return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '修改失败')


class UserView(ListAPIView):
    queryset = User.objects.exclude(status='destroy')
    serializer_class = UserDetailSerializer
    filter_class = UserFilter
    pagination_class = MyPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('-createTime', )
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
        User.objects.filter(endTime__lt=currentTime).exclude(status__in=["destroy", "normal"]).\
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
@authentication_classes((CustomAuthentication, ))
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

    api = Api()
    userInfo = api.search_user_byphone(tel)
    if userInfo == -1:
        return http_return(400, '接口通信错误')
    if userInfo:
        return http_return(200, 'OK', {'status': 1})
    else:
        # 新用户
        return http_return(200, 'OK', {'status': 2})


# 迁移老用户
@api_view(['POST'])
@authentication_classes((CustomAuthentication, ))
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
                avatar='https://hbb-ads.oss-cn-beijing.aliyuncs.com/file110598494460.jpg',
                tel=tel,
                gender=gender,  # 性别 0未知  1男  2女
                status="normal",
                roles=roles,
                city=city
            )
        return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '添加失败')




# 添加新用户
@api_view(['POST'])
@authentication_classes((CustomAuthentication, ))
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

    nickName = data.get('nickName', '')
    city = data.get('city', '')
    roles = data.get('roles', '')
    gender = data.get('gender', '')
    pwd = data.get('pwd', '')

    if not all([gender in [0, 1, 2], nickName, roles in ['normalUser','adminUser'], pwd]):
        return http_return(400, '参数错误')

    if not 5<len(str(pwd))<40:
        return http_return(400, '密码长度错误')

    if city:
        if not 1<len(str(city))<40:
            return http_return(400, '城市长度错误')

    if not 1<len(str(nickName))<20:
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
                uuid = uuid,
                userID = userID,
                nickName = nickName or tel,
                avatar = 'https://hbb-ads.oss-cn-beijing.aliyuncs.com/file110598494460.jpg',
                tel = tel,
                gender = gender,  # 性别 0未知  1男  2女
                status = "normal",
                roles = roles,
                city = city
            )
        return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '保存用户失败')



@api_view(['POST'])
@authentication_classes((CustomAuthentication, ))
def modify_user(request):
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')

    uuid = data.get('uuid', '')
    nickName = data.get('nickName', '')
    city = data.get('city', '')
    roles = data.get('roles', '')
    gender = data.get('gender', '')
    pwd = data.get('pwd', '') # 没有填写密码则不用修改
    if not all([gender in [0, 1, 2], uuid, nickName, roles in ['normalUser','adminUser']]):
        return http_return(400, '参数错误')

    if city:
        if not 1<len(str(city))<40:
            return http_return(400, '城市长度错误')

    if not 1<len(str(nickName))<20:
        return http_return(400, '昵称长度错误')

    user = User.objects.filter(uuid=uuid).exclude(status="destroy").first()
    if not user:
        return http_return(400, '没有用户')

    tel = user.tel
    if not tel:
        return http_return(400, '没有用户手机号')
    # 调用接口 管理员在后台 重置其他用户密码, 重置自己的密码清缓存
    if pwd:
        if not 5<len(str(pwd))<40:
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
            return http_return(200, 'OK', data)
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '修改失败')




@api_view(['POST'])
@authentication_classes((CustomAuthentication, ))
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
            return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '删除失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication, ))
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

    endTimestamp = int(endTimestamp)/1000
    try:
        endTime = datetime.fromtimestamp(endTimestamp)
        currentTime = datetime.now()
        if currentTime >= endTime:
            return http_return(400, '结束时间错误')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '时间参数错误')

    user = User.objects.filter(uuid=uuid).exclude(status="destroy") .first()
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
        return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '添加失败')



@api_view(['POST'])
@authentication_classes((CustomAuthentication, ))
def cancel_forbid(request):
    # 恢复
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')

    user = User.objects.filter(uuid=uuid).exclude(status="destroy") .first()
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
        return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '恢复失败')


# 活动
# class GameInfoView(ListAPIView):
#     queryset = GameInfo.objects.all()
#     serializer_class = GameInfoSerializer
#     filter_class = GameInfoFilter
#     pagination_class = MyPagination
#
#     def get_queryset(self):
#         activityuuid = self.request.query_params.get('activityuuid', '')
#         if not activityuuid:
#             raise ParamsException({'code': 400, 'msg': '参数错误'})
#
#         act = Activity.objects.filter(uuid=activityuuid).first()
#         if not act:
#             raise ParamsException({'code': 400, 'msg': '活动信息不存在'})
#
#         self.queryset = self.queryset.filter(activityUuid__uuid=activityuuid).all()
#
#         self.queryset = sorted(self.queryset,
#                        key=lambda x: 0.75 * x.audioUuid.bauUuid.filter(type=1).count() + 0.25 * x.audioUuid.playTimes,
#                        reverse=True)
#         self.queryset.order_by()
#         return self.queryset


@api_view(['GET'])
@authentication_classes((CustomAuthentication, ))
def activity_rank(request):
    """活动排行"""
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    activityUuid = data.get('activityuuid', '')
    page = data.get('page', '')
    page_size = data.get('page_size', '')
    if not uuid:
        return http_return(400, '参数错误')
    act = Activity.objects.filter(uuid=activityUuid).first()
    if not act:
        return http_return(400, '活动信息不存在')
    config = ActivityConfig.objects.filter(status=0).first()
    if not config:
        return http_return(400, '未获取到参数配置')
    praiseNum = config.praiseNum / 100
    playTimesNum = config.playTimesNum / 100
    games = GameInfo.objects.filter(activityUuid__uuid=activityUuid).all()
    games = sorted(games,
                   key=lambda x: praiseNum * x.audioUuid.bauUuid.filter(
                       type=1).count() + playTimesNum * x.audioUuid.playTimes,
                   reverse=True)
    total, games = page_index(games, page, page_size)
    activityRankList = []
    for index,game in enumerate(games):
        name = game.audioUuid.name
        if game.audioUuid.audioStoryType:
            name = game.audioUuid.storyUuid.name
        activityRankList.append({
            "rank": index+1+(int(page)-1)*int(page_size) if page else index+1,
            "publisher": {
                "uuid": game.userUuid.uuid or '',
                "nickname": game.userUuid.nickName or '',
                "avatar": game.userUuid.avatar or '',
                "tel": game.userUuid.tel or '',
            },
            "audio": {
                "id": game.audioUuid.id or '',
                "uuid": game.audioUuid.uuid or '',
                "bgmUrl":  game.audioUuid.bgm.url if game.audioUuid.bgm else '',
                "voiceUrl": game.audioUuid.voiceUrl or '',
                "name": name or '',
            },
            "score": praiseNum * game.audioUuid.bauUuid.filter(type=1).count() + playTimesNum * game.audioUuid.playTimes,
        })
    return http_return(200, '成功', {"total": total, "activityRankList": activityRankList})



class ActivityView(ListAPIView):
    queryset = Activity.objects.all().prefetch_related('activityRankUuid').order_by('-createTime')
    serializer_class = ActivitySerializer
    filter_class = ActivityFilter
    pagination_class = MyPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('-createTime',)
    ordering_fields = ('id', 'createTime')


    def get_queryset(self):
        startTimestamp = self.request.query_params.get('starttime', '')
        endTimestamp = self.request.query_params.get('endtime', '')

        if (startTimestamp and not endTimestamp) or  (not startTimestamp and endTimestamp):
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
@authentication_classes((CustomAuthentication, ))
def create_activity(request):
    # 创建活动
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    name = data.get('name', '')
    intro = data.get('intro', '')
    startTime = data.get('starttime', '')
    endTime = data.get('endtime', '')
    url = data.get('url', '')
    icon = data.get('icon', '')         # 非必填
    if not all([url, name, intro, startTime, endTime]):
        return http_return(400, '参数错误')
    if Activity.objects.filter(name=name).exists():
        return http_return(400, '重复活动名')

    if startTime > endTime:
        return http_return(400, '时间错误')

    if not all([isinstance(startTime, int), isinstance(endTime, int)]):
        return http_return(400, '时间错误')

    if not isinstance(url ,str):
        return http_return(400, 'url错误')

    if not url.startswith( 'http' ):
        return http_return('url格式错误')

    startTime = startTime/1000
    endTime = endTime/1000

    try:
        startTime = datetime.fromtimestamp(startTime)
        endTime = datetime.fromtimestamp(endTime)
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '时间参数错误')

    try:
        with transaction.atomic():
            uuid = get_uuid()
            Activity.objects.create(
                uuid = uuid,
                name = name,
                url = url,
                startTime = startTime,
                endTime = endTime,
                intro = intro,
                icon = icon,
                status = "normal"
            )
            return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '创建失败')



@api_view(['POST'])
@authentication_classes((CustomAuthentication, ))
def modify_activity(request):
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')
    name = data.get('name', '')
    intro = data.get('intro', '')
    icon = data.get('icon', '') # 没有icon
    startTime = data.get('starttime', '')
    endTime = data.get('endtime', '')
    url = data.get('url', '')
    if not all([uuid, name, intro, startTime, endTime, url]):
        return http_return(400, '参数错误')
    activity = Activity.objects.filter(uuid=uuid).first()
    if not activity:
        return http_return(400, '没有对象')
    myName = activity.name
    if myName != name:
        if Activity.objects.filter(name=name).exists():
            return http_return(400, '重复活动名')

    if not all([isinstance(startTime, int), isinstance(endTime, int)]):
        return http_return(400, '时间错误')

    if startTime > endTime:
        return http_return(400, '时间错误')

    if not url.startswith( 'http' ):
        return http_return('url格式错误')

    startTime = startTime/1000
    endTime = endTime/1000
    try:
        startTime = datetime.fromtimestamp(startTime)
        endTime = datetime.fromtimestamp(endTime)
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '时间错误')

    activity = Activity.objects.filter(uuid=uuid).first()
    try:
        with transaction.atomic():
            activity.name = name
            activity.startTime = startTime
            activity.endTime = endTime
            activity.icon = icon
            activity.intro = intro
            activity.url = url
            activity.save()
            return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '修改失败')


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
                return self.queryset.exclude(Q(startTime__gt=endtime)&Q(endTime__gt=endtime)|
                                             Q(endTime__lt=starttime)&Q(startTime__lt=starttime))
            except Exception as e:
                logging.error(str(e))
                raise ParamsException(e.detail)

        return self.queryset



@api_view(['POST'])
@authentication_classes((CustomAuthentication, ))
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

    startTime = startTime/1000
    endTime = endTime/1000

    try:
        startTime = datetime.fromtimestamp(startTime)
        endTime = datetime.fromtimestamp(endTime)
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '时间参数错误')


    if type == 0:
        if not Activity.objects.filter(uuid=target).exists():
            return http_return(400, '没有此活动')

    if type == 2: # 音频
        if not AudioStory.objects.filter(uuid=target).exists():
            return http_return(400, '没有此音频')

    if type == 4: # 外部链接
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
        return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '添加失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication, ))
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

    startTime = startTime/1000
    endTime = endTime/1000

    try:
        startTime = datetime.fromtimestamp(startTime)
        endTime = datetime.fromtimestamp(endTime)
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '时间错误')

    if type == 0:
        if not Activity.objects.filter(uuid=target).exists():
            return http_return(400, '没有此活动')

    if type == 2:  # 音频
        if not AudioStory.objects.filter(uuid=target).exists():
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
        return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '修改失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication, ))
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
            return http_return(200, 'OK')
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
@authentication_classes((CustomAuthentication, ))
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
            return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '回复失败')

