#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from django.urls import path

from public import views

app_name = 'public'

urlpatterns = [
    path('address/create', views.address_create, name='address_create'),  # 新增收货地址
    path('address/list', views.address_list, name='address_list'),  # 收货地址列表
    path('address/change', views.address_change, name='address_change'),  # 收货地址信息修改
    path('address/del', views.address_del, name='address_del'),  # 删除收货地址
    path('address/choose', views.address_choose, name='address_choose'),  # 选择收货地址
    path('address/area/create', views.area_create, name='area_create'),  # 创建数据库地区
    path('address/area/query', views.area_query, name='area_query'),  # 地区数据获取


]