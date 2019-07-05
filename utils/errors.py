
from rest_framework.exceptions import APIException


class ParamsException(APIException):
    status_code = 400
    default_detail = '请求参数错误'

    def __init__(self, error):
        self.detail = error
