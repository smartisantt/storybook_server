#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Create your views here.
from django_filters.rest_framework import DjangoFilterBackend
from requests import Response
from rest_framework import viewsets, mixins, status
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView, RetrieveAPIView, GenericAPIView, CreateAPIView, UpdateAPIView
from rest_framework.viewsets import GenericViewSet
from serializers import serializer

from manager import managerCommon
from manager.filters import StoryFilter, FreedomAudioStoryInfoFilter, CheckAudioStoryInfoFilter, AudioStoryInfoFilter
from manager.models import *
from manager.managerCommon import *
from manager.paginations import TenPagination
from manager.serializers import StorySerializer, FreedomAudioStoryInfoSerializer, CheckAudioStoryInfoSerializer, \
    AudioStoryInfoSerializer, TagsSimpleSerialzer
from storybook_sever.api import Api
from datetime import datetime
from django.db.models import Count, Q

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
    user_data = caches['default'].get(token)
    # 缓存有数据,则在缓存中拿数据，登录日志添加新数据
    if user_data:
        try:
            # 获取缓存用户信息
            user_data = caches['default'].get(token)
            user = User.objects.filter(userID=user_data.get('userID', '')).only('userID').first()
            role = user.roles
            status = user.status
            if status == 'forbbiden_login':
                return http_return(400, '此用户被禁止登录')
                # 获取登录ip
            loginIp = get_ip_address(request)

            # 登录成功生成登录日志，缓存存入信息

            loginLog = LoginLog(
                uuid = get_uuid(),
                ipAddr = loginIp,
                userUuid = user
            )
            loginLog.save()

        except Exception as e:
            logging.error(str(e))
            return http_return(400, '登陆失败')
        return http_return(200, '登陆成功', {'roles': role})
    # 缓存中没有数据
    if not user_data:
        api = Api()
        # 校验前端传过来的token值
        user_info = api.check_token(token)

        if not user_info:
            return http_return(400, '未获取到用户信息')
        else:
            # 用户表中是否有该用户
            userID = user_info.get('userId', '')
            if not userID:
                return http_return(400, '参数错误')
            user = User.objects.filter(userID=userID).only('userID').first()
            # 状态 normal  destroy  forbbiden_login  forbbiden_say
            if user and user.status == 'destroy':
                return http_return(400, '无此用户')
            if user and user.status == 'forbbiden_login':
                return http_return(400, '此用户被禁止登录')


            # 当前表中没有此用户信息则在数据库中创建
            if not user:
                user = User(
                    uuid=get_uuid(),
                    tel=user_info.get('phone', ''),
                    userID=userID,
                    nickName=user_info.get('wxNickname', ''),
                    roles="normalUser",
                    avatar=user_info.get('wxAvatarUrl', ''),
                    gender=user_info.get('wxSex', 0),
                    status='normal'
                )
                try:
                    with transaction.atomic():
                        user.save()
                except Exception as e:
                    logging.error(str(e))
                    return http_return(400, '保存失败')
            user = User.objects.filter(userID=userID).exclude(status__in=['destroy','forbbiden_login']).first()
            print(user.uuid)
            role = user.roles

            # 写入缓存
            if not create_cache(user, token):
                return http_return(400, '用户不存在')
            try:
                with transaction.atomic():
                    loginLog_uuid = get_uuid()
                    loginLog = LoginLog(
                        uuid=loginLog_uuid,
                        ipAddr=user_info.get('loginIp', ''),
                        userUuid=user
                    )
                    loginLog.save()
                    return http_return(200, '登陆成功', {'roles': role})
            except Exception as e:
                logging.error(str(e))
                return http_return(400, '保存日志失败')



"""
首页数据
"""
def total_data(request):
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    # 前端传入毫秒为单位的时间戳
    startTimestamp = data.get('startTime', '')
    endTimestamp = data.get('endTime', '')

    if startTimestamp and endTimestamp:
        startTimestamp = startTimestamp/1000
        endTimestamp = endTimestamp/1000
    else:
        return http_return(400, '参数有误')
    # 小于2019-05-30 00:00:00的时间不合法
    if endTimestamp < startTimestamp or endTimestamp <= 1559145600 or startTimestamp <= 1559145600:
        return http_return(400, '时间有误')
    if startTimestamp and endTimestamp:
        # 给定时间查询
        startTime = datetime.fromtimestamp(startTimestamp)
        endTime = datetime.fromtimestamp(endTimestamp)
        t1 = datetime(startTime.year, startTime.month, startTime.day)
        t2 = datetime(endTime.year, endTime.month, endTime.day, 23, 59, 59, 999999)
        # 用户总人数
        totalUsers = User.objects.exclude(status='destroy').count()
        # 音频总数
        totalAudioStory = AudioStory.objects.all().count()
        # 专辑总数
        totalAlbums = Album.objects.all().count()
        # 新增用户人数
        newUsers = User.objects.filter(createTime__range=(t1, t2)).count()
        # 活跃用户人数
        activityUsers = LoginLog.objects.filter(createTime__range=(t1, t2)).values('userUuid_id').\
            annotate(Count('userUuid_id')).count()
        # 新增音频数
        newAudioStory = AudioStory.objects.filter(createTime__range=(t1, t2)).count()

        return http_return(200, 'OK',
                           {
                               'totalUsers': totalUsers,
                               'totalAudioStory': totalAudioStory,
                               'totalAlbums': totalAlbums,
                               'newUsers': newUsers,
                               'activityUsers': activityUsers,
                               'newAudioStory': newAudioStory
                           })


"""
内容分类
"""
def show_all_tags(request):
    """发布故事标签选择列表"""
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    tags = Tag.objects.filter(code="SEARCHSORT", parent_id__isnull=True, isDelete=False).\
        all().order_by('sortNum')

    tagList = []
    for tag in tags:
        childTagList= []
        for child_tag in tag.child_tag.only('uuid', 'sortNum', 'name'):
            if child_tag.isDelete == False:
                childTagList.append({
                    "uuid": child_tag.uuid,
                    "name": child_tag.name,
                    "sortNum": child_tag.sortNum,
                })
        tagList.append({
            "uuid": tag.uuid,
            "name": tag.name,
            "sortNum": tag.sortNum,
            "icon": tag.icon,
            "isUsing": tag.isUsing,
            "childTagList": childTagList,
            "childTagsNum": len(childTagList)        # 子标签个数
        })
    total = len(tagList)
    return http_return(200, '成功', {"total": total, "tagList": tagList})


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
    tag = Tag.objects.filter(name=name, parent_id__isnull=True, isDelete=False).first()
    if tag:
        return http_return(400, '重复分类名')
    try:
        with transaction.atomic():
            uuid = get_uuid()
            tag = Tag(
                uuid = uuid,
                code = 'SEARCHSORT',
                name = name,
                icon = icon,
                sortNum = sortNum,
            )
            tag.save()
            return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '添加分类失败')


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
    icon = tag.icon

    if sortNum != mySortNum:
        tag = Tag.objects.filter(sortNum=sortNum, code='SEARCHSORT', isDelete=False, parent_id__isnull=False).first()
        if tag:
            return http_return(400, '重复序号')

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
                'name': name,
                'icon': icon,
                'sortNum': sortNum,
            })

    except Exception as e:
        logging.error(str(e))
        return http_return(400, '修改分类失败')


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
        with transaction.atomic():
            tag.isDelete = True
            tag.save()
            return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '删除分类失败')


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
    tag = Tag.objects.filter(name=name, code='SEARCHSORT', isDelete=False, parent_id__isnull=False).first()
    if tag:
        return http_return(400, '重复标签')
    # 查询是否有重复sortNum
    tag = Tag.objects.filter(sortNum=sortNum, code='SEARCHSORT', isDelete=False, parent_id__isnull=False).first()
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
    pagination_class = None




"""
模板管理
"""
class StoryView(ListAPIView):
    """GET 显示所有模板列表"""
    queryset = Story.objects.exclude(status='destroy').defer('tags').order_by('-createTime')
    serializer_class = StorySerializer
    filter_class = StoryFilter

    def get_queryset(self):
        startTime = self.request.query_params.get('starttime', '')
        endTime = self.request.query_params.get('endtime', '')
        if (startTime and not endTime) or  (not startTime and endTime):
            raise ParamsException({'code': 400, 'msg': '时间错误'})
        if startTime and endTime:
            if not all([startTime.isdigit(), endTime.isdigit()]):
                raise ParamsException({'code': 400, 'msg': '时间错误'})

            startTime = int(startTime)/1000
            endTime = int(endTime)/1000
            if endTime < startTime:
                raise ParamsException({'code':400, 'msg':'结束时间早于结束时间'})
            startTime = datetime.fromtimestamp(startTime)
            endTime = datetime.fromtimestamp(endTime)
            starttime = datetime(startTime.year, startTime.month, startTime.day)
            endtime = datetime(endTime.year, endTime.month, endTime.day, 23, 59, 59, 999999)
            return self.queryset.filter(createTime__range=(starttime, endtime))
        return self.queryset


def add_story(request):
    """添加模板"""
    data = request_body(request, "POST")
    if not data:
        return http_return(400, '参数错误')
    faceIcon = data.get('faceIcon', '')
    listIcon = data.get('listIcon', '')
    name = data.get('name', '')
    intro = data.get('intro', '')
    content = data.get('content', '')
    isRecommd = data.get('isRecommd', '')
    isTop = data.get('isTop', '')

    # all 都为True 才返回True
    if not all([name, faceIcon, listIcon, content, intro, isRecommd, isTop]):
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



def modify_story(request):
    """修改模板"""
    data = request_body(request, "POST")
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')
    faceIcon = data.get('faceIcon', '')
    listIcon = data.get('listIcon', '')
    name = data.get('name', '')
    intro = data.get('intro', '')
    content = data.get('content', '')
    isRecommd = data.get('isRecommd', '')
    isTop = data.get('isTop', '')

    # all 都为True 才返回True
    if not all([faceIcon, listIcon, name, content, intro, isRecommd, isTop]):
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

# 改变模板状态
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


# """"删除模板"""
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


    story = Story.objects.filter(uuid=uuid).exclude(status='destroy').first()
    try:
        with transaction.atomic():
            story.status = 'destroy'
            story.save()
            return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '删除模板失败')


# """模板音频"""
class AudioStoryInfoView(ListAPIView):
    queryset = AudioStory.objects.filter(isDelete=False, audioStoryType=1)\
        .select_related('bgm', 'userUuid')\
        .prefetch_related('tags').order_by('-createTime')

    serializer_class = AudioStoryInfoSerializer
    filter_class = AudioStoryInfoFilter

    def get_queryset(self):
        startTime = self.request.query_params.get('starttime', '')
        endTime = self.request.query_params.get('endtime', '')

        # id = self.request.query_params.get('id', '')                # 故事ID
        nickName = self.request.query_params.get('nickName', '')    # 用户名
        name = self.request.query_params.get('name', '')    # 模板名
        tag = self.request.query_params.get('tag', '')      # 类型标签
        # type = self.request.query_params.get('type', '')      # 录制形式
        if (startTime and not endTime) or  (not startTime and endTime):
            raise ParamsException({'code': 400, 'msg': '时间错误'})
        if startTime and endTime:
            if not all([startTime.isdigit(), endTime.isdigit()]):
                raise ParamsException({'code': 400, 'msg': '时间错误'})

            startTime = int(startTime)/1000
            endTime = int(endTime)/1000
            if endTime < startTime:
                raise ParamsException({'code':400, 'msg':'结束时间早于结束时间'})
            startTime = datetime.fromtimestamp(startTime)
            endTime = datetime.fromtimestamp(endTime)
            starttime = datetime(startTime.year, startTime.month, startTime.day)
            endtime = datetime(endTime.year, endTime.month, endTime.day, 23, 59, 59, 999999)
            self.queryset = self.queryset.filter(createTime__range=(starttime, endtime))
        if nickName:
            self.queryset = self.queryset.filter(userUuid__in=User.objects.filter(nickName__icontains=nickName).all())
        if name:
            self.queryset = self.queryset.filter(
                storyUuid__in=Story.objects.filter(name__icontains=name).all())
        if tag:
            self.queryset = self.queryset.filter(
                tags=Tag.objects.filter(name=tag).first())

        return self.queryset




"""批量下载"""
def download_works(request):
    pass




"""添加音频"""
def add_works(request):
    pass


# 所有模板


"""自由音频"""
class FreedomAudioStoryInfoView(ListAPIView):
    queryset = AudioStory.objects.filter(isDelete=False, audioStoryType=0)\
        .select_related('bgm', 'userUuid')\
        .prefetch_related('tags').order_by('-createTime')

    serializer_class = FreedomAudioStoryInfoSerializer
    filter_class = FreedomAudioStoryInfoFilter

    def get_queryset(self):
        startTime = self.request.query_params.get('starttime', '')
        endTime = self.request.query_params.get('endtime', '')

        # id = self.request.query_params.get('id', '')                # 故事ID
        nickName = self.request.query_params.get('nickName', '')    # 用户名
        # name = self.request.query_params.get('name', '')    # 模板名
        tag = self.request.query_params.get('tag', '')      # 类型标签
        # type = self.request.query_params.get('type', '')      # 录制形式
        if (startTime and not endTime) or  (not startTime and endTime):
            raise ParamsException({'code': 400, 'msg': '时间错误'})
        if startTime and endTime:
            if not all([startTime.isdigit(), endTime.isdigit()]):
                raise ParamsException({'code': 400, 'msg': '时间错误'})

            startTime = int(startTime)/1000
            endTime = int(endTime)/1000
            if endTime < startTime:
                raise ParamsException({'code':400, 'msg':'结束时间早于结束时间'})
            startTime = datetime.fromtimestamp(startTime)
            endTime = datetime.fromtimestamp(endTime)
            starttime = datetime(startTime.year, startTime.month, startTime.day)
            endtime = datetime(endTime.year, endTime.month, endTime.day, 23, 59, 59, 999999)
            self.queryset = self.queryset.filter(createTime__range=(starttime, endtime))
        if nickName:
            self.queryset = self.queryset.filter(userUuid__in=User.objects.filter(nickName__icontains=nickName).all())

        if tag:
            self.queryset = self.queryset.filter(
                tags__exists=Tag.objects.filter(name=tag).first())

        return self.queryset



# 内容审核
class CheckAudioStoryInfoView(ListAPIView):
    queryset = AudioStory.objects.filter(isDelete=False )\
        .select_related('bgmUuid', 'userUuid')\
        .prefetch_related('tags').order_by('-createTime')

    serializer_class = CheckAudioStoryInfoSerializer
    filter_class = CheckAudioStoryInfoFilter

    def get_queryset(self):
        startTime = self.request.query_params.get('starttime', '')
        endTime = self.request.query_params.get('endtime', '')

        # id = self.request.query_params.get('id', '')                # 故事ID
        username = self.request.query_params.get('username', '')    # 用户名
        title = self.request.query_params.get('title', '')          # 作品名

        # 审核状态 unCheck待审核 check审核通过 checkFail审核不通过
        # checkstatus = self.request.query_params.get('checkstatus', '')      # 类型标签

        if (startTime and not endTime) or  (not startTime and endTime):
            raise ParamsException({'code': 400, 'msg': '时间错误'})
        if startTime and endTime:
            if not all([startTime.isdigit(), endTime.isdigit()]):
                raise ParamsException({'code': 400, 'msg': '时间错误'})

            startTime = int(startTime)/1000
            endTime = int(endTime)/1000
            if endTime < startTime:
                raise ParamsException({'code':400, 'msg':'结束时间早于结束时间'})
            startTime = datetime.fromtimestamp(startTime)
            endTime = datetime.fromtimestamp(endTime)
            starttime = datetime(startTime.year, startTime.month, startTime.day)
            endtime = datetime(endTime.year, endTime.month, endTime.day, 23, 59, 59, 999999)
            self.queryset = self.queryset.filter(createTime__range=(starttime, endtime))
        if username:
            self.queryset = self.queryset.filter(userUuid__in=User.objects.filter(username__icontains=username).all())

        # title 要在自由作品和模板作品中选择
        # worksType = models.BooleanField(default=True)  # 作品类型  是用的模板1 还是自由录制0
        if title:
            titleInTemplateQuerySet = self.queryset.filter(
                templateUuid__in=Story.objects.filter(title__icontains=title).all())
            titleInAudioStoryQuerySet = self.queryset.filter(title__icontains=title).all()
            self.queryset = titleInTemplateQuerySet|titleInAudioStoryQuerySet
        return self.queryset



# 配置标签
def config_tags(request):
    # data = request_body(request, 'POST')
    # if not data:
    #     return http_return(400, '参数错误')
    # worksUuid = data.get('worksuuid', '')
    # typeUuidList = data.get('typeUuidList', '')
    if request.method == 'POST':
        worksUuid = request.POST.get('worksuuid', '')
        typeUuidList = request.POST.getlist('typeUuidList', '')
        if not all([worksUuid, typeUuidList]):
            return http_return(400, '参数错误')

        if not worksUuid:
            return http_return(400, '参数错误')
        works = AudioStory.objects.filter(uuid=worksUuid).first()

        if not works:
            return http_return(400, '找不到此音频')
        # 作品类型  是用的模板1 还是自由录制0
        worksType = works.worksType

        tags = []
        for tagUuid in typeUuidList:
            tag = Tag.objects.filter(uuid=tagUuid).first()
            if not tag:
                return http_return(400, '无效标签')
            tags.append(tag)

        try:
            with transaction.atomic():
                works.tags.clear()
                works.tags.add(*tags)
                return http_return(200, 'OK')
        except Exception as e:
            logging.error(str(e))
            return http_return(400, '配置标签失败')






# 停用










