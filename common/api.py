#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import logging

from storybook_sever.config import version


class Api(object):

    def __init__(self):
        # self.comm_host = 'http://wsdev.pymom.com'
        self.comm_host = 'http://casdev.pymom.com'
        # self.create_user_host = 'http://casdev.pymom.com'
        self.sts_token_host = 'https://aiupload.hbbclub.com'

        self.token_url = '/api/sso/token/check'
        self.sts_token_url = '/api/oss/sts'
        self.create_user_url = '/api/sso/createbyuserpasswd'
        self.reset_pwd_url = '/api/sso/admin/pwd/reset'

        self.search_user_byphone_url = '/api/sso/user/byphone'

        if version == 'ali_test':
            self.comm_host = 'https://castest.hbbclub.com/'
            # self.create_user_host = 'https://castest.hbbclub.com/'

    def check_token(self, token):
        url = '{0}{1}'.format(self.comm_host, self.token_url)

        data = {
            'token': token
        }
        try:
            re = requests.post(url, json=data)
            if re.status_code == 200:
                if re.json().get('data').get('valid'):
                    return re.json().get('data').get('info')
            return False
        except Exception as e:
            logging.error(e)
            return False

    def create_user(self, tel, password=''):
        """
        创建用户
        :param tel:
        :param password:
        :return:
        """
        url = '{0}{1}'.format(self.comm_host, self.create_user_url)
        data = {
            "loginId": tel,
            "phone": True,
            "passwd": password
        }

        try:
            re = requests.post(url, json=data)
            if re.status_code == 200:
                return re.json().get('data').get('userId', '')
            else:
                # return re.json().get('msg')
                return False
        except Exception as e:
            logging.error(e)
            return -1

    def get_sts_token(self, token):
        """
        获取文件上传token临时临牌
        :return:
        """

        url = '{0}{1}'.format(self.sts_token_host, self.sts_token_url)

        headers = {'token': token}

        try:
            re = requests.get(url, headers=headers)
            if re.status_code == 200:
                if re.json().get('data'):
                    return re.json().get('data')
            return {}
        except Exception as e:
            logging.error(e)
            return {}

    def search_user_byphone(self, tel):
        # url = f'{self.comm_host}{self.search_user_byphone_url}?phone={tel}'
        url = '{0}{1}?phone={2}'.format(self.comm_host,self.search_user_byphone_url,tel)


        try:
            re = requests.get(url)
            if re.status_code == 200:
                if re.json()['data'].get('data'):
                    return re.json()['data'].get('data')[0]
            return False
        except Exception as e:
            logging.error(e)
            return -1


    def admin_reset_pwd(self, tel, pwd, token):
        """管理员重置密码，管理员重置自己密码会造成token失效"""
        url = '{0}{1}'.format(self.comm_host, self.reset_pwd_url)
        data = {
            "loginId": tel,
            "passwd": pwd
        }
        headers = {'token': token}

        try:
            re = requests.post(url, json=data, headers=headers)
            if re.status_code == 200:
                return True
            else:
                return False
        except Exception as e:
            logging.error(e)
            return False


if __name__ == '__main__':
    api = Api()
    # api.admin_reset_pwd("13398876569", "1234567", "2C2936634B97A0C9EDDDFA0B7EC2A412")
    # 微信：D6D9D462296F38D642E21898EF3A4B5D
    # Q  Q：1DE3A5906F27400A0792B12F5F4F74D5
    print(api.check_token('D6D9D462296F38D642E21898EF3A4B5D'))
    # if not api.check_token('285C430F99A9C706BFB925DA55F18665'):
        # print ('111')
    # print(api.create_user('15928140420', '123456'))
    # print(api.get_sts_token('0F4741AEF563F5894577912CADB2B5F3'))