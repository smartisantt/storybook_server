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

# 极光推送开关，ON打开极光推送  OFF 关闭（默认关闭）
# 针对创建定时推送，立即推送有效， 修改，删除无效
JPUSH = "ON"


# 分享域名
SHAREURL = "http://192.168.100.235:8009"
SLECTAUDIOURL = "http://192.168.100.235:8010"
if version == 'ali_test':
    SHAREURL = 'http://h5huitong.hbbclub.com'
    SLECTAUDIOURL = "活动正式服域名"


