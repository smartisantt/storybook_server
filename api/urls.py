#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from django.urls import path

from api import views

app_name = 'api'

urlpatterns = [
    path('index/', views.index, name='index'),

]
