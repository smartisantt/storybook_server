#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from django.urls import path

from api import views
from api.apiCommon import check_identify

app_name = 'api'

urlpatterns = [
    path('identify/code', views.identify_code, name='identify'),  # 获取验证码
    path('check/identifycode', views.check_identify_code, name='check_identify_code'),  # 核对验证码
    path('recording/index', views.recording_index_list, name='recording_index_list'),  # 用户故事列表
    path('recording/banner', views.recording_banner, name='recording_banner'),  # 用户首页轮播图
    path('recording/info', views.recording_stroy_detail, name='recording_stroy_detail'),  # 故事详情（录制页面）
    path('recording/bgmusic', views.recording_bgmusic_list, name='recording_bgmusic_list'),  # 背景音乐列表
    path('recording/send', views.recording_send, name='recording_send'),  # 故事发布
    path('recording/taglist', views.recording_tag_list, name='recording_tag_list'),  # 故事发布标签列表

    path('user/info', views.user_center, name='user_center'),  # 主播个人主页
    path('user/attation', views.become_fans, name='become_fans'),  # 关注用户
    path('user/audiostorylist', views.user_audio_list, name='user_audio_list'),  # 用户作品列表
    path('user/friendlist', views.user_fans, name='user_fans'),  # 用户粉丝或关注用户列表

    path('audiostory/list', views.audio_list, name='audio_list'),  # 所有故事列表
    path('audiostory/play', views.audio_play, name='audio_play'),  # 播放故事

    path('index/banner', views.index_banner, name='index_banner'),  # 首页轮播图
    path('index/list', views.index_list, name='index_list'),  # 首页展示列表
    path('index/more', views.index_more, name='index_more'),  # 展示更多

    path('search/all', views.search_all, name='search_all'),  # 搜索
    path('search/audiostory', views.search_audio, name='search_audio'),  # 搜索模板音频
    path('search/user', views.search_user, name='search_user'),  # 搜索主播
    path('search/hotkeyword', views.search_hot, name='search_hot'),  # 热搜词

    path('audiostory/category/detail', views.audiostory_category_detail, name='audiostory_category_detail'),  # 分类展示
    path('audiostory/category/list', views.index_category_list, name='index_category_list'),  # 分类标签展示
    path('audiostory/category/result', views.index_category_result, name='index_category_result'),  # 筛选结果
    path('audiostory/category/audiostory', views.index_category_audiostory, name='index_category_audiostory'),  # 筛选结果
    path('audiostory/category/user', views.index_category_user, name='index_category_user'),  # 筛选结果

    path('audiostory/praise', views.audiostory_praise, name='audiostory_praise'),  # 点赞作品
    path('audiostory/cancelpraise', views.audiostory_cancel_praise, name='audiostory_cancel_praise'),  # 取消点赞

    path('activity/detail', views.activity_detail, name='activity_detail'),  # 活动详情
    path('activity/ranklist', views.activity_rank, name='activity_rank'),  # 活动排行
    path('activity/audiostorylist', views.activity_audiostory_list, name='activity_audiostory_list'),  # 用户作品列表
    path('activity/join', views.activity_join, name='activity_join'),  # 参与比赛

]
