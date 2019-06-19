

version = "test"

# 手机验证码缓存时间
TEL_IDENTIFY_CODE = 5 * 60

# 是否正式发送短信
if version == 'ali_test':
    IS_SEND = True
else:
    IS_SEND = False