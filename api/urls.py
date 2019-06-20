#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from django.urls import path

from api import views

app_name = 'api'

urlpatterns = [
    path('identify/code', views.identify_code, name='identify'),  # 获取验证码
    path('check/identifycode', views.check_identify_code, name='check_identify_code'),  # 核对验证码
    path('index', views.user_index, name='index'),  # 用户首页

]
