#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Create your views here.

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView


from manager.filters import StoryFilter, FreedomAudioStoryInfoFilter, CheckAudioStoryInfoFilter, AudioStoryInfoFilter, \
    UserSearchFilter, BgmFilter, HotSearchFilter, UserFilter, GameInfoFilter, ActivityFilter
from manager.models import *
from manager.managerCommon import *
from manager.paginations import MyPagination
from manager.serializers import StorySerializer, FreedomAudioStoryInfoSerializer, CheckAudioStoryInfoSerializer, \
    AudioStoryInfoSerializer, TagsSimpleSerialzer, StorySimpleSerializer, UserSearchSerializer, BgmSerializer, \
    HotSearchSerializer, AdSerializer, ModuleSerializer, UserDetailSerializer, \
    AudioStorySimpleSerializer, GameInfoSerializer, ActivitySerializer
from storybook_sever.api import Api
from django.db.models import Count, Q, Max, Min, F
from datetime import datetime
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
            # 登录前更新用户状态
            currentTime = datetime.now()
            # 到了生效时间
            User.objects.filter(startTime__lt=currentTime, endTime__gt=currentTime, status="normal"). \
                update(status=F("settingStatus"), updateTime=currentTime)
            # 过了结束时间
            User.objects.filter(endTime__lt=currentTime).exclude(status__in=["destroy", "normal"]). \
                update(status="normal", updateTime=currentTime, startTime=None, endTime=None, settingStatus=None)

            # 获取缓存用户信息
            user_data = caches['default'].get(token)
            user = User.objects.filter(userID=user_data.get('userID', '')).\
                exclude(status="destroy").only('userID').first()
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
        return http_return(400, '无效时间')
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
    pagination_class = MyPagination




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
    """"""
    queryset = Story.objects.filter(status="normal")
    serializer_class = StorySimpleSerializer
    filter_class = StoryFilter
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
    queryset = AudioStory.objects.filter(Q(isDelete=False), Q(audioStoryType=1),
                                         Q(checkStatus='check')|Q(checkStatus='exemption'))\
        .select_related('bgm', 'userUuid')\
        .prefetch_related('tags').order_by('-createTime')

    serializer_class = AudioStoryInfoSerializer
    filter_class = AudioStoryInfoFilter
    pagination_class = MyPagination

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
            tag_info = Tag.objects.filter(name=tag).first()
            if tag_info:
                self.queryset = self.queryset.filter(tags__id=tag_info.id)
            else:
                self.queryset = self.queryset.filter(tags__id=0)

        return self.queryset


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



class FreedomAudioStoryInfoView(ListAPIView):
    """自由音频"""
    queryset = AudioStory.objects.filter(Q(isDelete=False), Q(audioStoryType=0),
                                         Q(checkStatus='check')|Q(checkStatus='exemption')) \
        .select_related('bgm', 'userUuid') \
        .prefetch_related('tags').order_by('-createTime')

    serializer_class = FreedomAudioStoryInfoSerializer
    filter_class = FreedomAudioStoryInfoFilter
    pagination_class = MyPagination

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
            tag_info = Tag.objects.filter(name=tag).first()
            if tag_info:
                self.queryset = self.queryset.filter(tags__id=tag_info.id)
            else:
                self.queryset = self.queryset.filter(tags__id=0)

        return self.queryset



# 内容审核
class CheckAudioStoryInfoView(ListAPIView):
    queryset = AudioStory.objects.filter(isDelete=False )\
        .select_related('bgm', 'userUuid')\
        .prefetch_related('tags').order_by('-createTime')

    serializer_class = CheckAudioStoryInfoSerializer
    filter_class = CheckAudioStoryInfoFilter
    pagination_class = MyPagination

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


# 审核通过和审核不通过
def check_audio(request):
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
    pagination_class = MyPagination

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
    try:
        with transaction.atomic():
            audioStory.isDelete = True
            audioStory.save()
        return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '删除失败')


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

# 添加关键词
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


# 置顶 取消置顶
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


# 删除关键词
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
    queryset = Ad.objects.filter(isDelete=False).only('id')
    serializer_class = AdSerializer



# 添加


# 编辑



# 删除



# 模块配置
class ModuleView(ListAPIView):
    """显示模块类型 MOD1每日一读  MOD2抢先听  MOD3热门推荐"""
    queryset = Module.objects.filter(isDelete=False).\
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
        Q(isDelete=False),Q(checkStatus='check')|Q(checkStatus='exemption')).order_by('-createTime')
    serializer_class = AudioStorySimpleSerializer
    filter_class = CheckAudioStoryInfoFilter
    pagination_class = MyPagination

    def get_queryset(self):
        startTime = self.request.query_params.get('starttime', '')
        endTime = self.request.query_params.get('endtime', '')

        nickName = self.request.query_params.get('nickName', '')  # 用户名
        name = self.request.query_params.get('name', '')  # 作品名

        # 审核状态 unCheck待审核 check审核通过 checkFail审核不通过 exemption 免检（后台上传的作品）

        if (startTime and not endTime) or (not startTime and endTime):
            raise ParamsException({'code': 400, 'msg': '时间错误'})
        if startTime and endTime:
            if not all([startTime.isdigit(), endTime.isdigit()]):
                raise ParamsException({'code': 400, 'msg': '时间错误'})

            startTime = int(startTime) / 1000
            endTime = int(endTime) / 1000
            if endTime < startTime:
                raise ParamsException({'code': 400, 'msg': '结束时间早于结束时间'})
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
            self.queryset = nameInAudioStoryQuerySet | nameInFreedomAudioStoryQuerySet
        return self.queryset





def add_story_into_module(request):
    """新增"""
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    type = data.get('type', '')
    audioUuid = data.get('audiouuid', '')
    if not all([type in ['MOD1', 'MOD2', 'MOD3'], audioUuid]):
        return http_return(400, '参数错误')

    audioStory = AudioStory.objects.filter(Q(isDelete=False), Q(uuid=audioUuid),
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


# 替换
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

    audioStory = AudioStory.objects.filter(Q(isDelete=False), Q(uuid=audioUuid),
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



# 删除
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

    def get_queryset(self):
        # 首先更新用户禁言禁止登录状态
        currentTime = datetime.now()
        # 到了生效时间
        User.objects.filter(startTime__lt=currentTime, endTime__gt=currentTime, status="normal").\
            update(status=F("settingStatus"), updateTime=currentTime)
        # 过了结束时间
        User.objects.filter(endTime__lt=currentTime).exclude(status__in=["destroy", "normal"]).\
            update(status="normal", updateTime=currentTime, startTime=None, endTime=None, settingStatus=None)
        startTime = self.request.query_params.get('starttime', '')
        endTime = self.request.query_params.get('endtime', '')

        if (startTime and not endTime) or (not startTime and endTime):
            raise ParamsException({'code': 400, 'msg': '时间错误'})
        if startTime and endTime:
            if not all([startTime.isdigit(), endTime.isdigit()]):
                raise ParamsException({'code': 400, 'msg': '时间错误'})

            startTime = int(startTime) / 1000
            endTime = int(endTime) / 1000
            if endTime < startTime:
                raise ParamsException({'code': 400, 'msg': '结束时间早于结束时间'})
            startTime = datetime.fromtimestamp(startTime)
            endTime = datetime.fromtimestamp(endTime)
            starttime = datetime(startTime.year, startTime.month, startTime.day)
            endtime = datetime(endTime.year, endTime.month, endTime.day, 23, 59, 59, 999999)
            self.queryset = self.queryset.filter(createTime__range=(starttime, endtime))
        return self.queryset


# 添加用户
def add_user(request):
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    tel = data.get('tel', '')
    nickName = data.get('nickName', '')
    city = data.get('city', '')
    roles = data.get('roles', '')
    userID = data.get('userID', '')
    # 可选参数
    gender = data.get('gender', '')
    intro = data.get('intro', '')
    avatar = data.get('avatar', '')
    if not all([tel, nickName, city, roles in ['normalUser','adminUser'], userID]):
        return http_return(400, '参数错误')

    user = User.objects.filter(tel=tel).exclude(status='destroy').first()
    if user:
        return http_return(400, '重复手机号')

    user = User.objects.filter(userID=userID).exclude(status='destroy').first()
    if user:
        return http_return(400, '重复注册')

    # user = User.objects.filter(nickName=nickName).exclude(status='destroy').first()
    # if user:
    #     return http_return(400, '重复用户名')

    try:
        uuid = get_uuid()
        with transaction.atomic():
            User.objects.create(
                uuid = uuid,
                userID = userID,
                nickName = nickName,
                tel = tel,
                intro = intro,
                avatar = avatar,
                gender = gender or 0,  # 性别 0未知  1男  2女
                status = "normal",
                roles = roles,
                city = city
            )
        return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '添加失败')





# 编辑
def modify_user(request):
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')
    nickName = data.get('nickName', '')
    city = data.get('city', '')
    roles = data.get('roles', '')
    if not all([uuid, nickName, city, roles]):
        return http_return(400, '参数错误')
    user = User.objects.filter(uuid=uuid).first()
    if not user:
        return http_return(400, '没有用户')
    try:
        with transaction.atomic():
            user.roles = roles
            user.city = city
            user.nickName = nickName
            user.save()
            return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '修改失败')




# 删除
def del_user(request):
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


# 禁用
def forbidden_user(request):
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')
    type = data.get('type', '')
    # 前端传入毫秒为单位的时间戳
    startTimestamp = data.get('starttime', '')
    endTimestamp = data.get('endtime', '')


    # destroy  forbbiden_login  forbbiden_say
    if not all([startTimestamp, endTimestamp, uuid, type in ["forbbiden_login", "forbbiden_say"]]):
        return http_return(400, '参数错误')

    if not all([isinstance(startTimestamp, int), isinstance(endTimestamp, int)]):
        return http_return(400, '时间格式错误')


    # if endTimestamp < startTimestamp or endTimestamp <= int(time.time()*1000) or startTimestamp <= int(time.time()*1000):
    if endTimestamp < startTimestamp or endTimestamp:
        return http_return(400, '无效时间')

    startTimestamp = startTimestamp/1000
    endTimestamp = endTimestamp/1000
    startTime = datetime.fromtimestamp(startTimestamp)
    endTime = datetime.fromtimestamp(endTimestamp)

    user = User.objects.filter(uuid=uuid).exclude(status="destroy") .first()
    if not user:
        return http_return(400, '没有对象')

    try:
        with transaction.atomic():
            user.startTime = startTime
            user.endTime = endTime
            user.settingStatus = type
            user.save()
        return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '添加失败')



# 恢复
def cancel_forbid(request):
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
        return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '恢复失败')


# 活动
class GameInfoView(ListAPIView):
    queryset = GameInfo.objects.all().prefetch_related().order_by('-createTime')
    serializer_class = GameInfoSerializer
    filter_class = GameInfoFilter
    pagination_class = MyPagination



class ActivityView(ListAPIView):
    queryset = Activity.objects.all().prefetch_related('activityRankUuid').order_by('-createTime')
    serializer_class = ActivitySerializer
    filter_class = ActivityFilter
    pagination_class = MyPagination

    def get_queryset(self):
        startTime = self.request.query_params.get('starttime', '')
        endTime = self.request.query_params.get('endtime', '')

        if (startTime and not endTime) or (not startTime and endTime):
            raise ParamsException({'code': 400, 'msg': '时间错误'})
        if startTime and endTime:
            if not all([startTime.isdigit(), endTime.isdigit()]):
                raise ParamsException({'code': 400, 'msg': '时间错误'})

            startTime = int(startTime) / 1000
            endTime = int(endTime) / 1000
            if endTime < startTime:
                raise ParamsException({'code': 400, 'msg': '结束时间早于结束时间'})
            startTime = datetime.fromtimestamp(startTime)
            endTime = datetime.fromtimestamp(endTime)
            # starttime = datetime(startTime.year, startTime.month, startTime.day)
            # endtime = datetime(endTime.year, endTime.month, endTime.day, 23, 59, 59, 999999)
            return self.queryset.filter(startTime__gt=startTime, endTime__lt=endTime)
        return self.queryset


# 创建活动
def create_activity(request):
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    name = data.get('name', '')
    intro = data.get('intro', '')
    icon = data.get('icon', '')
    startTime = data.get('starttime', '')
    endTime = data.get('endtime', '')
    if not all([name, intro, icon, startTime, endTime]):
        return http_return(400, '参数错误')
    if Activity.objects.filter(name=name).exists():
        return http_return(400, '重复活动名')

    if startTime > endTime:
        return http_return(400, '时间错误')

    if not all([isinstance(startTime, int), isinstance(endTime, int)]):
        return http_return(400, '时间错误')

    startTime = int(startTime) / 1000
    endTime = int(endTime) / 1000
    startTime = datetime.fromtimestamp(startTime)
    endTime = datetime.fromtimestamp(endTime)

    try:
        with transaction.atomic():
            uuid = get_uuid()
            Activity.objects.create(
                uuid = uuid,
                name = name,
                startTime = startTime,
                endTime = endTime,
                icon = icon,
                intro = intro,
                status = "normal"
            )
            return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '创建失败')








