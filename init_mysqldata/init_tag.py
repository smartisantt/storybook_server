#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime
import json
from storybook_sever.settings import BASE_DIR
from manager.models import *

def init_tag():
    json_file = BASE_DIR + '/init_mysqldata/tag.json'
    with open(json_file,encoding='utf-8') as f:
        json_str = f.read()
        json_data = json.loads(json_str)

        for item in json_data:
            tag = Tag()
            tag.id = item['id']
            tag.uuid = item['uuid']
            tag.createTime = datetime.now()
            tag.updateTime = datetime.now()
            tag.code = item['code']
            tag.name = item['name']
            tag.icon = item['icon']
            tag.sortNum = item['sortNum']
            tag.parent_id = item['parent']
            tag.isUsing = True
            tag.isDelete = False
            tag.save()



if __name__ == '__main__':
    init_tag()