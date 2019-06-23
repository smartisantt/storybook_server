#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from django.urls import path

from manager import views
from manager.views import TemplateStoryView

app_name = 'manager'

urlpatterns = [
    path('admin/', views.admin, name='admin'),
    path('login/', views.login, name='login'),
    path('totaldata/', views.total_data, name='total_data'),
    path('tags/', views.add_tags, name='add_tags'),
    path('alltags/', views.show_all_tags, name='show_all_tags'),
    path('deltags/', views.del_tags, name='del_tags'),
    path('addchildtags/', views.add_child_tags, name='add_child_tags'),
    path('modifychildtags/', views.modify_child_tags, name='modify_child_tags'),

    path('modifychildtags/', TemplateStoryView.as_view()),


]
