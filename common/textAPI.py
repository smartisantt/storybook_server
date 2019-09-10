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
        except Exception as e:
            logging.error(e)

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
                if re.json().get('error_code'):
                    return re.json().get('error_code'), re.json().get('error_msg')
                code = re.json().get('result').get('spam')
                if code in [0, 1, 2]:
                    labelDict = {
                        0: "pass",
                        1: "reject",
                        2: "review",
                    }
                    targetDict = {
                        1: "暴恐违禁",
                        2: "文本色情",
                        3: "政治敏感",
                        4: "恶意推广",
                        5: "低俗辱骂",
                        6: "低质灌水",
                    }
                    labelList = []
                    for label in re.json().get('result').get(labelDict[code]):
                        labelList.append(targetDict[label["label"]])
                    return code, ",".join(labelList)
        except Exception as e:
            logging.error(str(e))
        return False, False

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
    print(text.work_on("咕咚来了"))
    # text.thread_test()
