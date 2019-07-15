
from rest_framework.exceptions import APIException


class ParamsException(APIException):
    status_code = 400
    default_detail = '请求参数错误'

    def __init__(self, error):
        self.detail = error

class OutoOfRangeTimeException(APIException):
    status_code = 200
    default_detail = '查询超出时间范围'

    def __init__(self, error):
        self.detail = error

