#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# Create your views here.
from common.common import *


def index(request):
    """
    主页展示
    :param request:
    :return:
    """
    data = request_body_not_token(request)
    if not data:
        return http_return(400, '参数错误')
    value = data.get('value', '')
    return http_return(200, 'ok')
