import logging

from django.core.cache import caches
from django.db import transaction
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from manager.managerCommon import http_return, get_uuid, get_ip_address, create_session
from manager.models import User, LoginLog
from storybook_sever.api import Api



class CustomAuthentication(BaseAuthentication):

    def authenticate(self, request):
        token = request.META.get('HTTP_TOKEN')
        if not token:
            raise AuthenticationFailed('提供有效的身份认证标识')

        try:
            user_info = caches['default'].get(token)
        except Exception as e:
            logging.error(str(e))
            raise AuthenticationFailed('连接Redis失败')


        # 缓存有数据  - 写日志
        if user_info:
            user = User.objects.filter(userID=user_info.get('userId', ''), roles='adminUser').\
                exclude(status="destroy").only('userID').first()
            if not user:
                raise AuthenticationFailed('没有管理员权限')

            # 获取登录ip
            loginIp = get_ip_address(request)
            try:
                log = LoginLog(
                    uuid=get_uuid(),
                    ipAddr=loginIp,
                    userUuid=user,
                    platform= '',
                    isManager = True
                )
                log.save()
            except Exception as e:
                logging.error(str(e))
                raise AuthenticationFailed('保存日志失败')
        # 缓存中没有数据 - 校验token -  数据库中是否存有此管理员信息 -写日志- 写入缓存
        if not user_info:
            api = Api()
            user_info = api.check_token(token)
            if not user_info:
                raise AuthenticationFailed('未获取到用户信息')

            # 记录登录ip,存入缓存
            user_data = User.objects.filter(userID=user_info.get('userId', '') , roles='adminUser').\
            exclude(status="destroy").first()
            if not user_data:
                raise AuthenticationFailed('没有管理员权限')

            loginIp = get_ip_address(request)
            if not create_session(user_data, token, loginIp):
                raise AuthenticationFailed('用户不存在')

            # 如果有登陆出现，则存登录日志
            try:
                log = LoginLog(
                    uuid=get_uuid(),
                    ipAddr=user_info.get('loginIp', ''),
                    userUuid=user_data,
                    platform=user_info['data'].get('platform', ''),
                )
                log.save()
            except Exception as e:
                logging.error(str(e))
                return http_return(400, '日志保存失败')
        return None, None
