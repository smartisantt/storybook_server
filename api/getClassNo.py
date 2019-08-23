"""
获取课程兑换码
"""
import logging

import requests


class ClassObj(object):

    def __init__(self):
        self.host ="http://39.108.94.46:4081"
        self.url = "/api/ht/code"

    def getCode(self,classType):
        data = {
            "type": classType,
        }
        re = requests.get(self.host + self.url, params=data)
        resultStr = re.content.decode("utf-8")
        resultDict = eval(resultStr)
        try:
            if resultDict["code"] == 200:
                return resultDict["data"]["code"]
            else:
                return False
        except Exception as e:
            logging.error(e)
            return False

if __name__ == "__main__":
    classObj = ClassObj()
    print(classObj.getCode(1))