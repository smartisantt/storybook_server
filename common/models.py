#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from django.db import models


class BaseModle(models.Model):
    """
    共有属性
    """
    uuid = models.CharField(max_length=64, unique=True)
    createTime = models.DateTimeField(auto_now_add=True, verbose_name="创建时间", null=True)
    updateTime = models.DateTimeField(auto_now=True, verbose_name="更新时间", null=True)

    class Meta:
        abstract = True
