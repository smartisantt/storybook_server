from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        # response.data['detail'].code
        response.data['code'] = response.data.get('code') or response.status_code
        # response.data['msg'] = response.data.get('msg') or list(response.data.values())[0]
        if response.data.get('msg'):
            response.data['msg'] = response.data.get('msg')
        elif response.data.get('id'):
            response.data['msg'] = response.data.get('id')[0]
        elif response.data.get('detail'):
            response.data['msg'] = response.data.get('detail')
        else:
            response.data['msg'] = '参数有误！！'
    return response