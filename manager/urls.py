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
    path('totaldata/', views.total_data, name='total_data'),
    path('alltags/', views.show_all_tags, name='show_all_tags'),
    path('tags/', views.add_tags, name='add_tags'),
    path('deltags/', views.del_tags, name='del_tags'),
    path('stoptags/', views.stop_tags, name='stop_tags'),


    path('addchildtags/', views.add_child_tags, name='add_child_tags'),
    path('modifychildtags/', views.modify_child_tags, name='modify_child_tags'),

    # path('templatestories/', views.show_all_template_stories, name='show_all_template_stories'),
    path('templatestories/', TemplateStoryView.as_view()),

]

# router = SimpleRouter()
# router.register('templatestories', TemplateStoryView)
#
# urlpatterns += router.urls