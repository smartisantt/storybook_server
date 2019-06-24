#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Create your views here.
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, mixins
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView

from manager import managerCommon
from manager.filters import  TemplateStoryFilter
from manager.models import *
from manager.managerCommon import *
from manager.paginations import TenPagination
from storybook_sever.api import Api
from datetime import datetime
from django.db.models import Count

from manager.serializers import TemplateStorySerializer
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
                    username=user_info.get('wxNickname', ''),
                    roles="adminUser",
                    # roles="normalUser",
                    userLogo=user_info.get('wxNickname', ''),
                    gender=user_info.get('wxSex', 0),
                    status='normal'
                )
                try:
                    with transaction.atomic():
                        user.save()
                except Exception as e:
                    logging.error(str(e))
                    return http_return(400, '保存失败')
            user = User.objects.filter(userID=userID).only('userID').first()
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
    data = managerCommon.request_body(request, 'GET')
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
        totalWorks = Works.objects.all().count()
        # 专辑总数
        totalAlbums = Album.objects.all().count()
        # 新增用户人数
        newUsers = User.objects.filter(createTime__range=(t1, t2)).count()
        # 活跃用户人数
        activityUsers = LoginLog.objects.filter(createTime__range=(t1, t2)).values('userUuid_id').annotate(Count('userUuid_id')).count()
        # 新增音频数
        newWorks = Works.objects.filter(createTime__range=(t1, t2)).count()

        return http_return(200, 'OK',
                           {
                               'totalUsers': totalUsers,
                               'totalWorks': totalWorks,
                               'totalAlbums': totalAlbums,
                               'newUsers': newUsers,
                               'activityUsers': activityUsers,
                               'newWorks': newWorks
                           })


"""
内容分类
"""
def show_all_tags(request):
    """发布故事标签选择列表"""
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    tags = Tag.objects.filter(code="SEARCHSORT", parent_id__isnull=True, isDelete=False).all().order_by('sortNum')

    tagList = []
    for tag in tags:
        childTagList= []
        for child_tag in tag.child_tag.only('uuid', 'sortNum', 'tagName'):
            if child_tag.isDelete == False:
                childTagList.append({
                    "uuid": child_tag.uuid,
                    "tagName": child_tag.tagName,
                    "sortNum": child_tag.sortNum,
                })
        tagList.append({
            "uuid": tag.uuid,
            "tagName": tag.tagName,
            "sortNum": tag.sortNum,
            "iconUrl": tag.iconUrl,
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
    iconUrl = data.get('iconUrl', '')
    tagName = data.get('tagName', '')
    sortNum = data.get('sortNum', '')

    # all 都为True 才返回True
    if not all([tagName, sortNum, iconUrl]):
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
    tag = Tag.objects.filter(tagName=tagName, parent_id__isnull=True, isDelete=False).first()
    if tag:
        return http_return(400, '重复分类名')
    try:
        with transaction.atomic():
            uuid = get_uuid()
            tag = Tag(
                uuid = uuid,
                code = 'SEARCHSORT',
                tagName = tagName,
                iconUrl = iconUrl,
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
    iconUrl = data.get('iconUrl', '')
    tagName = data.get('tagName', '')
    sortNum = data.get('sortNum', '')
    uuid = data.get('uuid', '')
    if not all([tagName, sortNum, uuid, iconUrl]):
        return http_return(400, '参数错误')
    if not isinstance(sortNum, int):
        return http_return(400, '序号错误')
    if sortNum <= 0:
        return http_return(400, '序号错误')
    tag = Tag.objects.filter(uuid=uuid).first()
    if not tag:
        return http_return(400, '没有对象')
    mySortNum = tag.sortNum
    myTagName = tag.tagName
    iconUrl = tag.iconUrl

    if sortNum != mySortNum:
        tag = Tag.objects.filter(sortNum=sortNum, code='SEARCHSORT', isDelete=False, parent_id__isnull=False).first()
        if tag:
            return http_return(400, '重复序号')

    if tagName != myTagName:
        tag = Tag.objects.filter(tagName=tagName, code='SEARCHSORT', isDelete=False, parent_id__isnull=False).first()
        if tag:
            return http_return(400, '重复标签')
    tag = Tag.objects.filter(uuid=uuid).first()
    try:
        with transaction.atomic():
            tag.sortNum = sortNum
            tag.tagName = tagName
            tag.save()
            return http_return(200, 'OK', {
                'tagName': tagName,
                'iconUrl': iconUrl,
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
            return http_return(200, 'OK')
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
    tagName = data.get('tagName', '')
    sortNum = data.get('sortNum', '')
    if not all([parentUuid, tagName, sortNum]):
        return http_return(400, '参数错误')
    if not isinstance(sortNum, int):
        return http_return(400, '序号错误')
    if sortNum <= 0:
        return http_return(400, '序号错误')

    parentTag = Tag.objects.filter(uuid=parentUuid, code='SEARCHSORT', isDelete=False, parent_id__isnull=True).first()
    if not parentTag:
        return http_return(400, '参数有误')
    # 查询是否有重复tagName
    tag = Tag.objects.filter(tagName=tagName, code='SEARCHSORT', isDelete=False, parent_id__isnull=False).first()
    if tag:
        return http_return(400, '重复标签')
    # 查询是否有重复tagName
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
                tagName=tagName,
                sortNum=sortNum,
                parent=parentTag
            )
            tag.save()
            return http_return(200, 'OK', {
                'uuid': uuid,
                'tagName': tagName,
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
    tagName = data.get('tagName', '')
    sortNum = data.get('sortNum', '')
    uuid = data.get('uuid', '')
    if not all([parentUuid, tagName, sortNum, uuid]):
        return http_return(400, '参数错误')
    if not isinstance(sortNum, int):
        return http_return(400, '序号错误')
    if sortNum <= 0:
        return http_return(400, '序号错误')
    tag = Tag.objects.filter(uuid=uuid).first().sortNum
    if not tag:
        return http_return(400, '没有对象')
    mySortNum = tag.sortNum
    myTagName = tag.tagName

    if sortNum != mySortNum:
        tag = Tag.objects.filter(sortNum=sortNum, code='SEARCHSORT', isDelete=False, parent_id__isnull=False).first()
        if tag:
            return http_return(400, '重复序号')
    parentTag = Tag.objects.filter(uuid=parentUuid, code='SEARCHSORT', isDelete=False, parent_id__isnull=True).first()
    if not parentTag:
        return http_return(400, '参数有误')

    if tagName != myTagName:
        tag = Tag.objects.filter(tagName=tagName, code='SEARCHSORT', isDelete=False, parent_id__isnull=False).first()
        if tag:
            return http_return(400, '重复标签')

    try:
        with transaction.atomic():
            tag.sortNum = sortNum
            tag.tagName = tagName
            tag.save()
            return http_return(200, 'OK', {
                'uuid': uuid,
                'tagName': tagName,
                'sortNum': sortNum,
                'parentUuid': parentUuid
            })

    except Exception as e:
        logging.error(str(e))
        return http_return(400, '修改分类失败')


"""
模板管理
"""
"""GET 显示所有模板列表"""

class TemplateStoryView(ListAPIView):
    queryset = TemplateStory.objects.exclude(status='destroy').\
        only('id', 'uuid', 'title', 'createTime', 'recordNum', 'status').order_by('-createTime')
    serializer_class = TemplateStorySerializer
    filter_class = TemplateStoryFilter

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


"""根据时间、模板ID、模板名搜索"""

"""显示模板的详细信息"""

""""添加模板"""
""""修改模板"""
""""删除模板"""








