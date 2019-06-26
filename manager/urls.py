#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from django.urls import path
from rest_framework.routers import SimpleRouter

from manager import views
from manager.views import StoryView, AudioStoryInfoView, FreedomAudioStoryInfoView, CheckAudioStoryInfoView, \
    TypeTagView, StorySimpleView, UserSearchView

app_name = 'manager'

urlpatterns = [
    path('admin/', views.admin, name='admin'),
    path('login/', views.login, name='login'),
    path('home/totaldata/', views.total_data, name='total_data'),
    path('tags/alltags/', views.show_all_tags, name='show_all_tags'),
    path('tags/addtags/', views.add_tags, name='add_tags'),
    path('tags/modifytags/', views.modify_tags, name='modify_tags'),
    path('tags/deltags/', views.del_tags, name='del_tags'),
    path('tags/stoptags/', views.stop_tags, name='stop_tags'),
    path('tags/addchildtags/', views.add_child_tags, name='add_child_tags'),
    path('tags/modifychildtags/', views.modify_child_tags, name='modify_child_tags'),
    # 所有分类标签的字标签
    path('tags/typetags/', TypeTagView.as_view()),


    # 模板故事路由
    path('story/stories/', StoryView.as_view()),
    # 所有模板的模板名
    path('story/allstoriesname/', StorySimpleView.as_view()),
    path('story/addstory/', views.add_story, name='add_story'),
    path('story/modifystory/', views.modify_story, name='modify_story'),
    path('story/delstory/', views.del_story, name='del_story'),
    path('story/changestorystatus/', views.change_story_status, name='change_story_status'),





    # 模板音频
    path('story/audio/', AudioStoryInfoView.as_view()),
    # 用户名模糊搜索
    path('story/searchnickname/', UserSearchView.as_view()),
    path('story/addaudiostory/', views.add_audio_story, name='add_audio_story'),

    # 自由音频
    path('story/freedomaudio/', FreedomAudioStoryInfoView.as_view()),

    # 审核
    path('check/checkaudio/', CheckAudioStoryInfoView.as_view()),

    path('check/configtags/', views.config_tags, name='config_tags'),

]

# router = SimpleRouter()
# router.register('/template/templatestories', TemplateStoryView)
#
# urlpatterns += router.urls