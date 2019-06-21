#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from django.urls import path

from api import views
from api.apiCommon import check_identify

app_name = 'api'

urlpatterns = [
    path('identify/code', views.identify_code, name='identify'),  # 获取验证码
    path('check/identifycode', views.check_identify_code, name='check_identify_code'),  # 核对验证码
    path('recording/index/list', views.recording_index_list, name='recording_index_list'),  # 用户故事列表
    path('recording/banner', views.recording_banner, name='recording_banner'),  # 用户首页轮播图
    path('recording/story/detail', views.recording_stroy_detail, name='recording_stroy_detail'),  # 故事详情（录制页面）
    path('recording/bgmusic/list', views.recording_bgmusic_list, name='recording_bgmusic_list'),  # 背景音乐列表
    path('recording/send', views.recording_send, name='recording_send'),  # 故事发布
    path('recording/tag/list', views.recording_tag_list, name='recording_tag_list'),  # 故事发布标签列表

]
