# coding: utf-8

import logging
import requests
from threading import Thread

from django.core.cache import caches

from storybook_sever.config import TEXT_AUDIO_TIMEOUT


class TextAudit(object):
    """内容审核"""

    def __init__(self):
        self.tokenHost = 'https://aip.baidubce.com/oauth/2.0/token'
        self.textHost = 'https://aip.baidubce.com/rest/2.0/antispam/v2/spam'
        self.AK = 'D5zZYuGY5LNTmkWLYKlGsQQt'
        self.SK = 'aE3mG2xPZKBMkGKg1krlx75sjF2SAlfr'

    def get_token(self):
        """获取access_token"""
        data = {
            "grant_type": "client_credentials",
            "client_id": self.AK,
            "client_secret": self.SK
        }
        headers = {'Content-Type': 'application/json; charset=UTF-8'}
        re = requests.get(self.tokenHost, headers=headers, params=data)
        try:
            if re.status_code == 200:
                self.access_token = re.json().get('access_token')
                caches['api'].set("textAudioToken", self.access_token, TEXT_AUDIO_TIMEOUT)
                return True
            else:
                return False
        except Exception as e:
            logging.error(e)
            return False

    def text_audit(self):
        """审核文本内容"""
        data = {
            "content": self.content,
            "access_token": self.access_token
        }
        headers = {
            "Content-Type": 'application/x-www-form-urlencoded; charset=UTF-8',
        }
        re = requests.post(self.textHost, headers=headers, params=data)
        try:
            if re.status_code == 200:
                if re.json().get('error_code') == 18:
                    return 18
                if re.json().get('result').get('spam') in [0, 1, 2]:
                    return re.json().get('result').get('spam')
                return False
            else:
                return False
        except Exception as e:
            logging.error(str(e))
            return False

    def work_on(self, text):
        """执行审核"""
        self.access_token = caches['api'].get("textAudioToken")
        if not self.access_token:
            self.get_token()
        self.content = text
        return self.text_audit()

    def thread_test(self):
        """多线程测试QPS"""
        c_list = []
        for i in range(10000):
            t = Thread(target=self.work_on, args=("咕咚来了",))
            c_list.append(t)
            t.start()
        for c in c_list:
            c.join()


if __name__ == "__main__":
    text = TextAudit()
    # print(text.work_on("咕咚来了"))
    # text.thread_test()
