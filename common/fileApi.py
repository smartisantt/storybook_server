#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging

import requests

from storybook_sever.config import version


class FileInfo(object):
    def __init__(self):
        self.file_host = "http://192.168.100.29:8000"
        self.url = "/api/pub/file/urls"
        if version == 'ali_test':
            self.file_host = ""
            self.url = "/api/pub/file/urls"

    def get_url(self, mediaUuidList, request):
        data = {
            "mediaUuid": mediaUuidList,
        }
        headers = {'token': request.META.get('HTTP_TOKEN')}
        re = requests.get(self.file_host + self.url, headers=headers, json=data)
        try:
            if re.status_code == 200:
                return re.json().get('data')
            else:
                return False
        except Exception as e:
            logging.error(e)
            return False


fileApi = FileInfo()

if __name__ == "__main__":
    file = FileInfo()
    uuidList = []
    result = file.get_url(uuidList)
    print(result)
