#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from django.urls import path
from rest_framework.routers import SimpleRouter

from manager import views
from manager.views import TemplateStoryView

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

    # path('templatestories/', views.show_all_template_stories, name='show_all_template_stories'),
    path('template/templatestories/', TemplateStoryView.as_view()),

]

# router = SimpleRouter()
# router.register('templatestories', TemplateStoryView)
#
# urlpatterns += router.urls