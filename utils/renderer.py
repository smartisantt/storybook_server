
from rest_framework.renderers import JSONRenderer


class MyJsonRenderer(JSONRenderer):

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
            data转化为：
            {
                'code': 200,
                'msg': '请求成功'，
                'data': data
            }
        """
        try:
            # 如果运行try中的内容，则表示code和msg是我们自己返回的数据
            # 表示程序出现问题，需自己返回响应数据
            code = data.pop('code')
            msg = data.pop('msg')
            res = {
                'code': code,
                'msg': msg,
            }
        except:
            # 表示程序是正常运行的，需自己组装code和msg参数
            code = 200
            msg = 'OK'
            res = {
                'code': code,
                'msg': msg,
                'data': data
            }
        return super().render(res)
        # if renderer_context:
        #     if isinstance(data, dict):
        #         code = data.pop('msg', 200)
        #         msg = data.pop('msg', 'OK')
        #     else:
        #         msg = 'aaaa'
        #         code = 400
        #     res = {
        #         'code': code,
        #         'msg': msg,
        #         'data': data
        #     }
        #     return super().render(res, accepted_media_type, renderer_context)
        # else:
        #     return super().render(data, accepted_media_type, renderer_context)
