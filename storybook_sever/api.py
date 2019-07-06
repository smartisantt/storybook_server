#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import logging

from storybook_sever.config import version


class Api(object):

    def __init__(self):
        self.comm_host = 'http://wsdev.pymom.com'
        self.create_user_host = 'http://casdev.pymom.com'
        self.sts_token_host = 'https://aiupload.hbbclub.com'

        self.token_url = '/api/sso/token/check'
        self.sts_token_url = '/api/oss/sts'
        self.create_user_url = '/api/sso/createbyuserpasswd'

        self.search_user_byphone_url = '/api/sso/user/byphone'

        if version == 'ali_test':
            self.comm_host = 'https://castest.hbbclub.com/'
            self.create_user_host = 'https://castest.hbbclub.com/'

    def check_token(self, token):
        url = '{0}{1}'.format(self.comm_host, self.token_url)

        data = {
            'token': token
        }
        re = requests.post(url, json=data)
        try:
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
        url = '{0}{1}'.format(self.create_user_host, self.create_user_url)
        data = {
            "loginId": tel,
            "phone": True,
            "passwd": password
        }
        re = requests.post(url, json=data)

        try:
            if re.status_code == 200:
                return re.status_code, re.json().get('data').get('userId', '')
            else:
                # return re.status_code, re.json().get('msg')
                return False
        except Exception as e:
            logging.error(e)
            return False

    def get_sts_token(self, token):
        """
        获取文件上传token临时临牌
        :return:
        """

        url = '{0}{1}'.format(self.sts_token_host, self.sts_token_url)

        headers = {'token': token}

        re = requests.get(url, headers=headers)
        try:
            if re.status_code == 200:
                if re.json().get('data'):
                    return re.json().get('data')
            return {}
        except Exception as e:
            logging.error(e)
            return {}

    def search_user_byphone(self, tel):
        url = f'{self.comm_host}{self.search_user_byphone_url}?phone={tel}'

        re = requests.get(url)
        try:
            if re.status_code == 200:
                if re.json()['data'].get('data'):
                    return re.json()['data'].get('data')[0]
            return False
        except Exception as e:
            logging.error(e)
            return -1


if __name__ == '__main__':
    api = Api()
    api.search_user_byphone('15928140429')
    # if not api.check_token('285C430F99A9C706BFB925DA55F18665'):
    #     print ('111')
    # api.create_user('18683367392', '123456')
    # print(api.get_sts_token('0F4741AEF563F5894577912CADB2B5F3'))