import datetime
import json
import logging
import uuid

from django.core.cache import cache
from django.http import HttpResponse


def request_body(request, method='GET'):
    """
    转换request.body
    :param request:
    :return:
    """
    if not request:
        return request
    if request.method != method:
        return http_return(400, '请求方式不正确')
    try:
        token = request.META.get('HTTP_TOKEN')
        if not token:
            return http_return(400, '非法请求')
        data = {
            '_cache': cache.get(token)
        }
        if request.method == 'POST':
            if request.body:
                try:
                    for key, value in json.loads(request.body).items():
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


def datetime_to_string(mydate, rule='%Y-%m-%d %H:%M:%S'):
    """
    将datetime.datetime转为string
    :param mydate:
    :return:
    """
    if isinstance(mydate, datetime.datetime) or isinstance(mydate, datetime.date):
        return mydate.strftime(rule)
    else:
        return mydate


def string_to_datetime(mystr, rule='%Y-%m-%d %H:%M:%S'):
    """
    将string转为 datetime.datetime
    :param mydate:
    :return:
    """
    if isinstance(mystr, str):
        return datetime.datetime.strptime(mystr, rule)
    else:
        return mystr


def page_index(myList, page=1, limit=10):
    """
    分页
    :param page: 页码  第一页为1
    :param limit: 每一页显示条数
    :return: total + list
    """
    page = page if page else 0
    limit = limit if limit else 20

    if not all([isinstance(page, int), isinstance(limit, int)]):
        try:
            page = int(page)
            limit = int(limit)
        except Exception as e:
            logging.error(str(e))
            return myList
    total = len(myList)
    if page == 0:
        startPage = 0
        endPage = limit
    else:
        startPage = (page - 1) * limit
        endPage = page * limit
    if total < startPage:
        return total, []
    if total < endPage:
        endPage = total
    return total, myList[startPage: endPage]
