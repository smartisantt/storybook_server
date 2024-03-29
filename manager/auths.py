import logging
from datetime import datetime

from django.core.cache import caches
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission

from manager.managerCommon import get_uuid, get_ip_address, create_session
from manager.models import User, LoginLog
from common.api import Api
from storybook_sever.config import USER_CACHE_OVER_TIME
from utils.errors import ParamsException


logger = logging.getLogger('ipandpath')


class CustomAuthentication(BaseAuthentication):

    def authenticate(self, request):

        token = request.META.get('HTTP_TOKEN')
        if not token:
            raise AuthenticationFailed('提供有效的身份认证标识')

        # 日志消息
        remote_info = ''
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            remote_info = ' HTTP_X_FORWARDED_FOR:' + x_forwarded_for.split(',')[0]
        else:
            remote_addr = request.META.get('REMOTE_ADDR')
            remote_info += ' REMOTE_ADDR:' + remote_addr
        # nickName = 'None'
        # if request.user:
        #     nickName = request.user.nickName
        token = request.META.get('HTTP_TOKEN')
        user_agent = request.META.get('HTTP_USER_AGENT')


        logger.info( remote_info + ' URL:' + request.path + ' METHOD:' + request.method +
                     ' TOKEN:' + token + ' USER_AGENT:' + user_agent)


        try:
            user_info = caches['default'].get(token)
        except Exception as e:
            logging.error(str(e))
            raise AuthenticationFailed('连接Redis失败')

        user = None
        # 缓存有数据  没有写登录日志
        if user_info:
            user = User.objects.filter(userID=user_info.get('userId', '')).\
                exclude(status="destroy").only('userID').first()
            if not user:
                raise AuthenticationFailed('没有管理员权限')


            # 获取登录ip
            # loginIp = get_ip_address(request)
            # try:
            #     LoginLog.objects.create(
            #         uuid=get_uuid(),
            #         ipAddr=loginIp,
            #         userUuid=user,
            #         platform=user_info.get('platform', ''),
            #         isManager=True
            #     )
            # except Exception as e:
            #     logging.error(str(e))
            #     raise AuthenticationFailed('保存日志失败')
        # 缓存中没有数据 - 校验token -  数据库中是否存有此管理员信息 -写日志- 写入缓存
        if not user_info:
            api = Api()
            user_info = api.check_token(token)
            if not user_info:
                raise AuthenticationFailed(detail='提供有效的token')

            user = User.objects.filter(userID=user_info.get('userId', '')).\
                exclude(status="destroy").first()
            if not user:
                raise AuthenticationFailed('该用户已删除，请联系管理员！')

            user = User.objects.filter(userID=user_info.get('userId', ''), roles='adminUser').\
                exclude(status="destroy").first()
            if not user:
                raise AuthenticationFailed('没有管理员权限')

            loginIp = get_ip_address(request)
            humanTime = user_info.get('loginTime').get("humanTime")

            lastLoginTime = datetime.strptime(humanTime, "%Y-%m-%d %H:%M:%S")
            if (datetime.now() - lastLoginTime).total_seconds() > USER_CACHE_OVER_TIME:
                raise AuthenticationFailed("登录失效，请重新登录！")
            if not create_session(user, token, loginIp):
                raise AuthenticationFailed('写缓存失败')

            # 如果有登陆出现，则存登录日志
            try:
                LoginLog.objects.create(
                    uuid=get_uuid(),
                    ipAddr=user_info.get('loginIp', ''),
                    userUuid=user,
                    userAgent=request.META.get('HTTP_USER_AGENT', ''),
                    isManager = True
                )
            except Exception as e:
                logging.error(str(e))
                raise AuthenticationFailed('保存日志失败')
        return user, token


class CustomAuthorization(BasePermission):

    def has_permission(self, request, view):
        if request.user and request.user.roles == 'adminUser':
            return True
        raise ParamsException({'code':403, 'msg': '没有管理员权限'})