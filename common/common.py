import json
import logging
import uuid

from django.core.cache import cache
from django.http import HttpResponse


def request_body_not_token(request):
    """
    转换request.body
    :param request:
    :return:
    """
    if not request:
        return request
    try:
        token = request.META.get('HTTP_TOKEN')

        data = {
            '_cache': cache.get(token)
        }
        if request.method == 'POST':
            if request.body:
                try:
                    for key, value in json.loads(request.body.decode('utf-8')).items():
                        data[key] = value
                except Exception as e:
                    logging.error(str(e))
                    pass
            if request.POST:
                for key, value in request.POST.items():
                    data[key] = value
        elif request.method == 'GET':
            for key, value in request.GET.items():
                data[key] = value
        else:
            pass

    except Exception as e:
        logging.error(str(e))
        return False
    return data


def http_return(code, msg='', info=None):
    """
    返回封装
    :param code: 状态码
    :param msg: 返回消息
    :param info: 返回数据
    :return:
    """
    data = {
        'code': code,
        'msg': msg
    }
    if info is not None:
        data['data'] = info
    return HttpResponse(json.dumps(data), status=code)


def get_uuid():
    """
    生成数据库uuid
    :return:
    """
    return "".join(str(uuid.uuid4()).split("-")).upper()
