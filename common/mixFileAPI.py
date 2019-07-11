import requests


class MixAudio(object):
    """
    发送合并请求
    """

    def __init__(self):
        self.host = 'http://192.168.100.235:8008'

    def audio_product(self, uuid):
        """
        测试音频
        :return:
        """
        url = self.host + '/api/product/audio'
        data = {
            'uuid': uuid,
        }
        txt = requests.post(url, json=data)

        result = txt.json()
        return result


if __name__ == "__main__":
    mix = MixAudio()
    info = mix.audio_product("56250D14B46B4998B6D27A6361C44EFF")
    print(info)

