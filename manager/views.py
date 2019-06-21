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
    user_data = cache.get(token)
    # 缓存有数据,则在缓存中拿数据，登录日志添加新数据
    if user_data:
        try:
            # 获取缓存用户信息
            user_info = cache.get(token)
            user = User.objects.filter(userID=user_info.get('userId', '')).first()

            role = user.get('role')
            status = user.get('status')
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
    # 缓存中没有数据
    if not user_data:
        api = Api()
        # 校验前端传过来的token值
        user_info = api.check_token(token)
        if not user_info:
            return http_return(400, '未获取到用户信息')
        else:

            # 用户表中是否有该用户
            user = User.objects.filter(userID=user_info.get('userId', '')).first()
            # 状态 normal  destroy  forbbiden_login  forbbiden_say
            if user and user.status == 'destroy':
                return http_return(400, '无此用户')
            if user and user.status == 'forbbiden_login':
                return http_return(400, '此用户被禁止登录')


            # 当前表中没有此用户信息则在数据库中创建
            if not user:
                user_uuid = get_uuid()
                user = User(
                    uuid=user_uuid,
                    tel=user_info.get('phone', ''),
                    userID=user_info.get('userId', ''),
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
            user = User.objects.filter(Q(userID=user_info.get('userId', '')) and ~Q(status='forbbiden_login')).first()
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
            loginLog.save()

    return http_return(200, '登陆成功', {'roles': role, 'userInfo': user_info})


def total_data(request):
    if request.method == 'POST':
        startTime = request.POST.get('startTime', 0)
        endTime = request.POST.get('endTime', 0)
        currentDate = datetime.datetime.now().date()

        if startTime and endTime:
            startTime = unix_time_to_datetime(int(startTime)).date()
            endTime = unix_time_to_datetime(int(endTime)).date()
            totalUsers1 = User.objects.filter(createTime__gte=startTime).count()
            totalUsers2 = User.objects.filter(createTime__lte=endTime).count()
            totalUsers = User.objects.filter(Q(createTime__gte=startTime) and Q(createTime__lte=endTime)).count()

        else:
            # 返回所有数据
            totalUsers = User.objects.filter(~Q(status='destroy')).count()
            # 按时间范围搜索
            # 首先获取时间范围，然后再查询
            # 用户总人数
            # totalUsers =
            # 新增用户人数
            # 活跃用户人数
            # 故事总数
            # 模板故事总数
            # Entry.objects.filter(pub_date__range=(start_date, end_date))
        return http_return(200, 'OK',
                           {
                               'totalUsers': totalUsers,
                               'newUsers': 12,
                               'activityUsers': 23,
                               'totalStories': 23,
                               'totalTemplateStroies': 23
                           })








