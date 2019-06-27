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
from manager.filters import StoryFilter, FreedomAudioStoryInfoFilter, CheckAudioStoryInfoFilter, AudioStoryInfoFilter, \
    UserSearchFilter, BgmFilter
from manager.models import *
from manager.managerCommon import *
from manager.paginations import TenPagination
from manager.serializers import StorySerializer, FreedomAudioStoryInfoSerializer, CheckAudioStoryInfoSerializer, \
    AudioStoryInfoSerializer, TagsSimpleSerialzer, StorySimpleSerializer, UserSearchSerializer, BgmSerializer, \
    HotSearchSerializer
from storybook_sever.api import Api
from datetime import datetime
from django.db.models import Count, Q, Exists, Max, Min

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
    tag = Tag.objects.filter(name=name, parent_id__isnull=True, code='SEARCHSORT', isDelete=False).first()
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



class StorySimpleView(ListAPIView):
    queryset = Story.objects.filter(status="normal")
    serializer_class = StorySimpleSerializer
    pagination_class = None


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
            # Todo
            self.queryset = self.queryset.filter(
                tags=Tag.objects.filter(name=tag).first())

        return self.queryset




"""批量下载"""
def download_works(request):
    pass



# 用户名模糊搜索
class UserSearchView(ListAPIView):
    queryset = User.objects.only('uuid', 'nickName').order_by("nickName")
    serializer_class = UserSearchSerializer
    filter_class = UserSearchFilter
    pagination_class = None



"""添加音频"""
def add_audio_story(request):
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    storyUuid = data.get('storyuuid', '')
    userUuid = data.get('useruuid', '')
    remarks = data.get('remarks', '')
    duration = data.get('duration', '')
    url = data.get('url', '')
    tagsUuidList = data.get('tagsuuidlist', '')


    if not all([storyUuid, userUuid, remarks, url, duration, tagsUuidList]):
        return http_return(400, '参数不能为空')

    story = Story.objects.filter(uuid=storyUuid).first()
    if not story:
        return http_return(400, '模板错误')

    user = User.objects.filter(uuid=userUuid).first()
    if not user:
        return http_return(400, '找不到用户')

    tags = []
    for tagUuid in tagsUuidList:
        tag = Tag.objects.filter(uuid=tagUuid).first()
        if not tag:
            return http_return(400, '无效标签')
        tags.append(tag)
    # 相同用户，相同模板，相同音频，则是重复上传
    audioStory = AudioStory.objects.filter(userUuid=user, storyUuid=story, voiceUrl=url).first()
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
            storyUuid=story,
            remarks=remarks,
            duration=duration,
            checkStatus="exemption"
        ).tags.add(*tags)
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '添加失败')
    return http_return(200, 'OK')





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
            # Todo
            self.queryset = self.queryset.filter(
                tags=Tag.objects.filter(name=tag).first())

        return self.queryset



# 内容审核
class CheckAudioStoryInfoView(ListAPIView):
    queryset = AudioStory.objects.filter(isDelete=False )\
        .select_related('bgm', 'userUuid')\
        .prefetch_related('tags').order_by('-createTime')

    serializer_class = CheckAudioStoryInfoSerializer
    filter_class = CheckAudioStoryInfoFilter

    def get_queryset(self):
        startTime = self.request.query_params.get('starttime', '')
        endTime = self.request.query_params.get('endtime', '')

        # id = self.request.query_params.get('id', '')                # 故事ID
        nickName = self.request.query_params.get('nickName', '')    # 用户名
        name = self.request.query_params.get('name', '')          # 作品名

        # 审核状态 unCheck待审核 check审核通过 checkFail审核不通过 exemption 免检（后台上传的作品）
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
        if nickName:
            self.queryset = self.queryset.filter(userUuid__in=User.objects.filter(nickName__icontains=nickName).all())

        # name 要在自由作品和模板作品中选择
        # 作品类型  是用的模板1 还是自由录制0
        if name:
            nameInAudioStoryQuerySet = self.queryset.filter(
                storyUuid__in=Story.objects.filter(name__icontains=name).all())
            nameInFreedomAudioStoryQuerySet = self.queryset.filter(name__icontains=name).all()
            self.queryset = nameInAudioStoryQuerySet|nameInFreedomAudioStoryQuerySet
        return self.queryset



# 配置标签
def config_tags(request):
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


# 添加背景音乐
def add_bgm(request):
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    url = data.get('url', '')
    name = data.get('name', '')
    duration = data.get('duration', '')

    if not all([url, name, duration]):
        return http_return(400, '参数错误')
    bgm = Bgm.objects.filter(url=url).exclude(status="destory").first()
    if bgm:
        return http_return(400, '重复文件')
    bgm = Bgm.objects.filter(name=name).exclude(status="destory").first()
    if bgm:
        return http_return(400, '重复音乐名')

    maxSortNum = Bgm.objects.aggregate(Max('sortNum'))['sortNum__max'] or 0

    try:
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




# 编辑音乐（音乐名，音频文件）
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

    bgm = Bgm.objects.filter(uuid=uuid).exclude(status="destory").first()
    if not bgm:
        return http_return(400, '找不到对象')
    myUrl = bgm.url
    myName = bgm.name
    sortNum = bgm.sortNum or 1


    if myUrl != url:
        bgm = Bgm.objects.filter(url=url).exclude(status="destory").first()
        if bgm:
            return http_return(400, '重复文件')
    if myName != name:
        bgm = Bgm.objects.filter(name=name).exclude(status="destory").first()
        if bgm:
            return http_return(400, '重复音乐名')


    try:
        bgm = Bgm.objects.filter(uuid=uuid).exclude(status="destory").first()
        bgm.url=url
        bgm.name=name
        bgm.sortNum=sortNum
        bgm.duration=duration
        bgm.save()

        return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '修改失败')


def change_order(request):
    """改变音乐排序"""
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')
    direct = data.get('direct', '')

    if not all([uuid, direct in ["up", "down"]]):
        return http_return(400, "参数错误")

    bgm = Bgm.objects.filter(uuid=uuid).exclude(status="destory").first()
    if not bgm:
        return http_return(400, "没有对象")
    mySortNum = bgm.sortNum
    # 向上
    if direct == "up":
        # 比当前sortNum小的最大值
        swapSortNum = Bgm.objects.filter(sortNum__lt=mySortNum).exclude(status="destory").aggregate(Max('sortNum'))['sortNum__max']
        if not swapSortNum:
            return http_return(400, "已经到顶了")
    elif direct == "down":
        # 比当前sortNum大的最小值
        swapSortNum = Bgm.objects.filter(sortNum__gt=mySortNum).exclude(status="destory").aggregate(Min('sortNum'))['sortNum__min']
        if not swapSortNum:
            return http_return(400, "已经到底了")

    try:
        swapBgm = Bgm.objects.filter(sortNum=swapSortNum).exclude(status="destory").first()
        bgm.sortNum, swapBgm.sortNum = swapSortNum, mySortNum
        bgm.save()
        swapBgm.save()
        return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '修改失败')


def forbid_bgm(request):
    """停用/恢复背景音乐"""
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')
    status = data.get('status', '')
    if not all([uuid, status in ['normal', 'forbid']]):
        return http_return(400, '参数错误')

    bgm = Bgm.objects.filter(uuid=uuid).exclude(status="destory").first()
    if not bgm:
        return http_return(400, '找不到对象')
    try:
        # forbid 停用 normal正常 在用  destroy 删除
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


def del_bgm(request):
    """删除背景音乐"""
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')
    if not uuid:
        return http_return(400, '参数错误')

    bgm = Bgm.objects.filter(uuid=uuid).exclude(status="destory").first()
    if not bgm:
        return http_return(400, '找不到对象')
    try:
        # forbid 停用 normal正常 在用  destroy 删除
        bgm = Bgm.objects.filter(uuid=uuid).exclude(status="destory").first()
        bgm.status = "destroy"
        bgm.save()
        return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '修改失败')



# 热搜词
class HotSearchView(ListAPIView):
    queryset = HotSearch.objects.exclude(isDelete=True).only('id')
    serializer_class = HotSearchSerializer








