#!/usr/bin/env python3
# -*- coding: utf-8 -*-

version = "test"

# 用户端端session过期时间
USER_SESSION_OVER_TIME = 30 * 24 * 60 * 60

# 手机验证码缓存时间
TEL_IDENTIFY_CODE = 5 * 60

# 管理端cache过期时间
USER_CACHE_OVER_TIME = 12 * 60 * 60

# 是否正式发送短信
if version == 'ali_test':
    IS_SEND = True
else:
    IS_SEND = False

activityHostUrl = 'http://huitonghuodong.hbbclub.com/'