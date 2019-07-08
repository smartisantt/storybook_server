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
    path('recording/info', views.recording_stroy_detail, name='recording_stroy_detail'),  # 故事详情（录制页面）
    path('recording/recent', views.recording_stroy_recent, name='recording_stroy_recent'),  # 最近录过
    path('recording/bgmusic', views.recording_bgmusic_list, name='recording_bgmusic_list'),  # 背景音乐列表
    path('recording/add', views.recording_send, name='recording_send'),  # 故事发布
    path('recording/taglist', views.recording_tag_list, name='recording_tag_list'),  # 故事发布标签列表

    path('user/info', views.user_center, name='user_center'),  # 主播个人主页
    path('user/attation', views.become_fans, name='become_fans'),  # 关注用户
    path('user/audiostorylist', views.user_audio_list, name='user_audio_list'),  # 用户作品列表
    path('user/friendlist', views.user_fans, name='user_fans'),  # 用户粉丝或关注用户列表

    path('audiostory/list', views.audio_list, name='audio_list'),  # 所有故事列表
    path('audiostory/play', views.audio_play, name='audio_play'),  # 播放故事
    path('audiostory/hostselect', views.audio_other, name='audio_other'),  # 主播精选
    path('audiostory/otherversion', views.audio_other_version, name='audio_other_version'),  # 其他主播版本

    path('index/banner', views.index_banner, name='index_banner'),  # 首页轮播图
    path('index/list', views.index_list, name='index_list'),  # 首页展示列表
    path('index/more', views.index_more, name='index_more'),  # 展示更多

    path('search/all', views.search_all, name='search_all'),  # 搜索
    path('search/each', views.search_each, name='search_each'),  # 搜索某一类
    path('search/hotkeyword', views.search_hot, name='search_hot'),  # 热搜词

    path('audiostory/category/list', views.index_category_list, name='index_category_list'),  # 分类标签展示
    path('audiostory/category/result', views.index_category_result, name='index_category_result'),  # 筛选结果
    path('audiostory/category/each', views.index_category_each, name='index_category_each'),  # 筛选某一类

    path('audiostory/praise', views.audiostory_praise, name='audiostory_praise'),  # 点赞作品
    path('audiostory/collection', views.audiostory_collection, name='audiostory_cancel_collection'),  # 收藏作品

    path('activity/detail', views.activity_detail, name='activity_detail'),  # 活动详情
    path('activity/ranklist', views.activity_rank, name='activity_rank'),  # 活动排行
    path('activity/audiostorylist', views.activity_audiostory_list, name='activity_audiostory_list'),  # 用户作品列表
    path('activity/join', views.activity_join, name='activity_join'),  # 参与比赛

    path('personal/index', views.personal_index, name='personal_index'),  # 个人主页
    path('personal/audiostorylist', views.personal_audiostory, name='personal_audiostory'),  # 个人作品
    path('personal/history/list', views.personal_history_list, name='personal_history_list'),  # 播放记录
    path('personal/history/del', views.personal_history_del, name='personal_history_del'),  # 清空播放记录
    path('personal/change', views.personal_change, name='personal_change'),  # 修改个人资料
    path('personal/feedback/add', views.feedback_add, name='feedback_add'),  # 添加反馈信息
    path('personal/feedback/list', views.feedback_reply_list, name='feedback_reply_list'),  # 回复列表
    path('personal/feedback/info', views.feedback_reply_info, name='feedback_reply_info'),  # 回复详情

    path('advertising/list', views.advertising_list, name='advertising_list'),  # 广告列表

]
