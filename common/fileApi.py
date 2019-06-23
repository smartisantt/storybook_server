#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging

import requests


class FileInfo(object):
    def __init__(self):
        self.file_host = "http://192.168.100.29:8000"
        self.url = "/api/pub/file/urls"

    def get_url(self, mediaUuidStr, request):
        data = {
            "mediaUuid": mediaUuidStr,
        }
        token = request.META.get('HTTP_TOKEN')
        headers = {'token': token}
        re = requests.get(self.file_host + self.url, headers=headers, params=data)
        try:
            if re.status_code == 200:
                return re.json().get('data')
            else:
                return False
        except Exception as e:
            logging.error(e)
            return False


if __name__ == "__main__":
    file = FileInfo()
    uuidList = ''
    result = file.get_url(uuidList)
    print(result)
