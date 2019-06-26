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

    path('user/center', views.user_center, name='user_center'),  # 主播个人主页
    path('user/become/fan', views.become_fans, name='become_fans'),  # 关注用户
    path('user/work/list', views.user_work_list, name='user_work_list'),  # 用户作品列表
    path('user/fans/list', views.user_fans, name='user_fans'),  # 用户粉丝或关注用户列表

    path('work/list', views.work_list, name='work_list'),  # 所有故事列表
    path('work/play', views.work_play, name='work_play'),  # 播放故事

    path('index/banner', views.index_banner, name='index_banner'),  # 首页轮播图
    path('index/list', views.index_list, name='index_list')  # 首页展示列表

]
