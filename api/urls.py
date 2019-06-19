#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from django.urls import path

from api import views

app_name = 'api'

urlpatterns = [
    path('identify/code', views.identify_code, name='identify'),
    path('check/identifycode', views.check_identify_code, name='check_identify_code'),


]
