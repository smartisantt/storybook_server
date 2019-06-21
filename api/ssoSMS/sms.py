#!/usr/local/bin/python3
#-*- coding:utf-8 -*-

import http.client
import urllib


host = "106.ihuyi.com"
sms_send_uri = "/webservice/sms.php?method=Submit"

#用户名是登录用户中心->验证码短信->产品总览->APIID
account = "C12119435"
#密码 查看密码请登录用户中心->验证码短信->产品总览->APIKEY
password = "1a76d2721bdd3196fa34559a28d4e431"


def send_sms(text, mobile):
    if isinstance(text, str):
        text = text.encode('utf-8')
    params = urllib.parse.urlencode({'account': account, 'password': password, 'content': text, 'mobile': mobile, 'format': 'json'})
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
    conn = http.client.HTTPConnection(host, port=80, timeout=30)
    conn.request("POST", sms_send_uri, params, headers)
    response = conn.getresponse()
    response_str = response.read()
    conn.close()
    return response_str

if __name__ == '__main__':

    mobile = "18487241833"
    text = "您的验证码是：121254。请不要把验证码泄露给其他人。"

    print(send_sms(text, mobile))