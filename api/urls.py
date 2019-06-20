#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from django.urls import path

from api import views
from api.apiCommon import check_identify

app_name = 'api'

urlpatterns = [
    path('identify/code', views.identify_code, name='identify'),  # 获取验证码
    path('check/identifycode', views.check_identify_code, name='check_identify_code'),  # 核对验证码
    path('index/list', views.index_list, name='index_list'),  # 用户故事列表
    path('index/banner', views.index_banner, name='index_banner'),  # 用户首页轮播图


]
