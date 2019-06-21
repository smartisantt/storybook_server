#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from django.urls import path

from manager import views

app_name = 'manager'

urlpatterns = [
    path('admin/', views.admin, name='admin'),
    path('login/', views.login, name='login'),
    path('totaldata/', views.total_data, name='get_total_data'),
]
