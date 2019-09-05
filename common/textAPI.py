# coding: utf-8

import importlib
import sys

importlib.reload(sys)

import logging

import requests


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
                return True
            else:
                return False
        except Exception as e:
            logging.error(e)
            return False

    def text_audit(self, text):
        """审核文本内容"""
        data = {
            "content": text,
            "access_token": self.access_token
        }
        headers = {
            "Content-Type": 'application/x-www-form-urlencoded; charset=UTF-8',
        }
        re = requests.post(self.textHost, headers=headers, params=data)
        try:
            logging.error("+++++++++++++++++++++++++++++++++++++++++-")
            logging.error("+++++++++++++++++++++++++++++++++++++++++-")
            logging.error("+++++++++++++++++++++++++++++++++++++++++-")
            logging.error(re.text)
            logging.error(re.json())
            logging.error(type(re.json()))
            logging.error("+++++++++++++++++++++++++++++++++++++++++-")
            logging.error(re.json().get('result'))
            logging.error(type(re.json().get('result')))
            logging.error("+++++++++++++++++++++++++++++++++++++++++-")
            logging.error(re.json().get('result').get('spam'))
            logging.error(type(re.json().get('result').get('spam')))
            logging.error("+++++++++++++++++++++++++++++++++++++++++-")
            logging.error("+++++++++++++++++++++++++++++++++++++++++-")
            logging.error("+++++++++++++++++++++++++++++++++++++++++-")
            if re.status_code == 200:
                if re.json().get('result').get('spam') == 0:
                    # print("审核通过")
                    logging.error("6-------------------------")
                    return True
                else:
                    # print("审核不通过")
                    logging.error("7-------------------------")
                    return False
            else:
                return False
        except Exception as e:
            logging.error(str(e))
            logging.error("8-------------------------")
            return False

    def work_on(self, text):
        """执行审核"""
        audit = TextAudit()
        logging.error("1-------------------------")
        if audit.get_token():
            logging.error("2-------------------------")
            result = audit.text_audit(text)
            if result:
                logging.error("3-------------------------")
                return result
        logging.error("4-------------------------")
        return False


if __name__ == "__main__":
    text = TextAudit()
    print(text.work_on("咕咚来了"))
