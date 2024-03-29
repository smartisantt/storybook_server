import logging

import requests

from storybook_sever.config import version


class MixAudio(object):
    """
    发送合并请求
    """

    def __init__(self):
        self.host = 'http://192.168.100.235:8008'
        if version == "ali_test":
            self.host = 'http://huitong.hbbclub.com'

    def audio_product(self, uuid):
        """
        测试音频
        :return:
        """
        url = self.host + '/api/product/audio'
        data = {
            'uuid': uuid,
        }
        try:
            txt = requests.post(url, json=data)
            result = txt.json()
        except Exception as e:
            logging.error(str(e))
            return False
        return result


if __name__ == "__main__":
    mix = MixAudio()
    info = mix.audio_product("56250D14B46B4998B6D27A6361C44EFF")
    print(info)

