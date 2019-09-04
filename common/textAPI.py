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
            "Content-Type": 'application/x-www-form-urlencoded',
        }
        re = requests.post(self.textHost, headers=headers, params=data)
        try:
            if re.status_code == 200:
                if re.json().get('result').get('spam') == 0:
                    print("审核通过")
                    return True
                else:
                    print("审核不通过")
                    return False
            else:
                return False
        except Exception as e:
            logging.error(e)
            return False

    def work_on(self, text):
        """执行审核"""
        audit = TextAudit()
        if audit.get_token():
            result = audit.text_audit(text)
            if result:
                return result
        return False


text = TextAudit()


if __name__ == "__main__":
    text = TextAudit()
    text.work_on("咕咚来了")
