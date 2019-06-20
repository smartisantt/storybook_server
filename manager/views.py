#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Create your views here.
from django.db import transaction

from common.common import *
from manager.models import *
from storybook_sever import api


def admin(request):
    """
    后台路由测试
    :param request:
    :return:
    """
    return http_return(200, 'ok')


def login(request):
    """
    :param request:
    :return:
    """
    token = request.META.get('HTTP_TOKEN')
    user_data = cache.get(token)
    if not user_data:
        user_info = api.check_token(token)
        if not user_info:
            return http_return(400, '未获取到用户信息')
        else:
            user_data = User.objects.filter(userID=user_info.get('userId', '')).first()
            # 状态 normal  destroy  forbbiden_login  forbbiden_say
            if user_data and user_data.status == 'destroy':
                return http_return(400, '无此用户')
            if user_data and user_data.status == 'forbbiden_login':
                return http_return(400, '此用户被禁止')
            if not user_data:
                user_uuid = get_uuid()
                user = User(
                    uuid=user_uuid,
                    tel=user_info.get('phone', ''),
                    userID=user_info.get('userId', ''),
                    name=user_info.get('wxNickname', ''),
                    updateTime=datetime.datetime.now()
                )
                loginLog_uuid = get_uuid()
                loginLog = LoginLog(
                    uuid = loginLog_uuid,
                    ipAddr = user_info.get('loginIp', ''),
                )
                try:
                    with transaction.atomic():
                        user.save()
                        loginLog.save()
                except Exception as e:
                    logging.error(str(e))
                    return http_return(400, '保存失败')
                user_data = User.objects.filter(userID=user_info.get('userId', ''), status='normal').first()
            roles = user_data.user_role.all()

            rule_tree, user_rule = get_user_role_list(roles)
            if not rule_tree and not user_rule:
                return http_return(200, '登陆成功', {'ruleTree': rule_tree, 'userInfo': user_info})
            if not create_cache_admin(user_data, token, user_rule):
                return http_return(400, '用户不存在')
    else:
        rule_tree = user_data.get('rule_tree')
    try:
        user_info = cache.get(token)
        if user_info:
            user_info.pop('user_rule')
        User.objects.filter(uuid=user_info.get('uuid')).update(loginTime=datetime.datetime.now())
    except Exception as e:
        logging.error(str(e))
        return http_return(200, '登陆失败')

    return http_return(200, '登陆成功', {'ruleTree': rule_tree, 'userInfo': user_info})