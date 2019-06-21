#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Create your views here.
from django.db import transaction
from django.db.models import Q

from common.common import *
from manager.models import *
from storybook_sever import api
from manager.managerCommon import *
from storybook_sever.api import Api
from datetime import datetime
from django.db.models import Count

def admin(request):
    """
    后台路由测试
    :param request:
    :return:
    """
    return http_return(200, 'ok')


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
            # 获取登录ip
            loginIp = get_ip_address(request)

            # 写入缓存
            if not create_cache(user,  loginIp, token):
                return http_return(400, '用户不存在')
            # 登录成功生成登录日志，缓存存入信息
            loginLog_uuid = get_uuid()
            loginLog = LoginLog(
                uuid=loginLog_uuid,
                ipAddr=loginIp,
                userUuid=user
            )
            try:
                with transaction.atomic():
                    loginLog.save()
            except Exception as e:
                logging.error(str(e))
                return http_return(400, '保存日志失败')

    return http_return(200, '登陆成功', {'roles': role})


def total_data(request):
    if request.method == 'POST':
        try:
            startTimestamp = int(request.POST.get('startTime', 0))
            endTimestamp = int(request.POST.get('endTime', 0))
        except Exception as e:
            logging.error(str(e))
            http_return(400, '参数有误无法查询')
        if endTimestamp < startTimestamp or endTimestamp < 0 or startTimestamp < 0:
            http_return(400, '参数有误无法查询')
        if startTimestamp and endTimestamp:
            # 给定时间查询
            startTime = datetime.fromtimestamp(startTimestamp)
            endTime = datetime.fromtimestamp(endTimestamp)
            t1 = datetime(startTime.year, startTime.month, startTime.day)
            t2 = datetime(endTime.year, startTime.month, startTime.day, 23, 59, 59, 999999)
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



def add_sort_search_tags(request):
    """添加搜索分类（一级类）"""

    pass






