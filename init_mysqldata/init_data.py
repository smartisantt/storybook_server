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


def init_admin():
    json_file = BASE_DIR + '/init_mysqldata/adminuser.json'
    with open(json_file,encoding='utf-8') as f:
        json_str = f.read()
        json_data = json.loads(json_str)

        for item in json_data:
            user = User()
            user.id = item['id']
            user.uuid = item['uuid']
            user.createTime = datetime.now()
            user.updateTime = datetime.now()
            user.tel = item['tel']
            user.userID = item['userID']
            user.roles = item['roles']
            user.status = item['status']
            user.gender = item['gender']
            user.avatar = item['avatar']
            user.nickName = item['nickName']
            user.save()

if __name__ == '__main__':
    init_tag()