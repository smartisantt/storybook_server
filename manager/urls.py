#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from django.urls import path

from manager import views

app_name = 'manager'

urlpatterns = [
    path('admin/', views.admin, name='admin'),
    path('login/', views.login, name='login'),
    path('totaldata/', views.total_data, name='get_total_data'),
    path('tags/', views.add_sort_search_tags, name='add_sort_search_tags'),
    path('childtags/', views.add_modify_child_tags, name='add_modify_child_tags'),
    path('delchildtags/', views.del_child_tags, name='del_child_tags'),
]
