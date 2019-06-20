#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging

import requests

from storybook_sever.config import version


class FileInfo(object):
    def __init__(self):
        self.file_host = ""
        self.url = ""
        if version == 'ali_test':
            self.file_host = ""
            self.url = ""

    def get_url(self, uuid):
        data = {
            "uuid": uuid
        }
        re = requests.get(self.url, data)
        try:
            if re.status_code == 200:
                return re.status_code, re.json().get('data').get('url', '')
            else:
                return re.status_code, re.json().get('msg')
        except Exception as e:
            logging.error(e)
            return False


if __name__ == "__main__":
    file = FileInfo()
    uuidList = []
    result = file.get_url(uuidList)
    print(result)
