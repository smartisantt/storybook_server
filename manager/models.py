#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models

from common.models import BaseModle


class Activity(models.Model, BaseModle):
    """
    活动表
    """
    name = models.CharField(max_length=255, blank=True, verbose_name="活动名称", null=True)
    intro = models.CharField(max_length=1024, blank=True, verbose_name="活动介绍", null=True)
    status = models.CharField(max_length=32, blank=True, verbose_name="活动状态", null=True)
    mediaUuid = models.CharField(max_length=256, verbose_name="活动图片", blank=True, null=True)
    starttime = models.DateTimeField(blank=True, verbose_name='活动开始时间', null=True)
    endtime = models.DateTimeField(blank=True, verbose_name='活动结束时间', null=True)

    class Meta:
        db_table = 'tb_activity'


class Ad(models.Model, BaseModle):
    """
    首页弹屏广告
    """
    mediaUuid = models.CharField(max_length=64, blank=True, verbose_name='广告图片', null=True)
    jumpUrl = models.CharField(db_column='jumpUrl', max_length=128, verbose_name='跳转地址', blank=True, null=True)
    starttime = models.DateTimeField(blank=True, verbose_name='时效开始时间', null=True)
    endtime = models.DateTimeField(blank=True, verbose_name='时效结束时间', null=True)
    isdelete = models.BooleanField(blank=True, verbose_name='软删除', null=True)

    class Meta:
        db_table = 'tb_ad'


class Baby(models.Model, BaseModle):
    """
    宝宝表
    """
    name = models.CharField(max_length=24, blank=True, verbose_name='宝宝姓名', null=True)
    babybirthday = models.DateTimeField(blank=True, verbose_name='宝宝生日', null=True)
    gender = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'tb_baby'


class Bgm(models.Model, BaseModle):
    """
    背景音乐
    """
    name = models.CharField(max_length=32, blank=True, null=True)
    mediaUuid = models.CharField(db_column='mediaUuid', max_length=64, blank=True, null=True)
    bgmTime = models.TimeField(db_column='bgmTime', verbose_name='背景音乐时长', blank=True, null=True)
    isUsing = models.IntegerField(blank=True, verbose_name='是否在用', null=True)  # 0 停用 1 在用
    sortNum = models.IntegerField(blank=True, verbose_name='排序编号', null=True)

    class Meta:
        db_table = 'tb_bgm'


class Feedback(models.Model, BaseModle):
    """
    用户反馈表
    """
    questiontype = models.CharField(db_column='questionType', max_length=26, blank=True,
                                    null=True)
    content = models.CharField(max_length=1024, blank=True, null=True)
    mediauuid1 = models.CharField(db_column='mediaUuid1', max_length=64, blank=True, null=True)
    mediauuid2 = models.CharField(db_column='mediaUuid2', max_length=64, blank=True, null=True)
    mediauuid3 = models.CharField(db_column='mediaUuid3', max_length=64, blank=True, null=True)
    mediauuid4 = models.CharField(db_column='mediaUuid4', max_length=64, blank=True, null=True)
    tel = models.CharField(max_length=20, blank=True, null=True)
    user = models.ForeignKey('User', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        db_table = 'tb_feedback'


class LoginLog(models.Model, BaseModle):
    """
    登录日志
    """
    ipAddr = models.CharField(max_length=126, verbose_name='IP地址', blank=True, null=True)
    logDate = models.DateTimeField(blank=True, verbose_name='登录日期时间', null=True)
    devCode = models.CharField(max_length=256, verbose_name='设备编号', blank=True, null=True)
    user = models.ForeignKey('User', models.CASCADE, blank=True, null=True, related_name='longinLogUuid')

    class Meta:
        db_table = 'tb_login_log'


class Module(models.Model, BaseModle):
    """
    首页显示模块
    """
    name = models.CharField(max_length=32, blank=True, null=True)
    ordernNum = models.IntegerField(blank=True, verbose_name='排序编号', null=True)
    type = models.CharField(max_length=32, blank=True, null=True)

    class Meta:
        db_table = 'tb_module'


class Rank(models.Model, BaseModle):
    """活动排名"""
    userRank = models.IntegerField(blank=True, null=True)
    popularity = models.IntegerField(blank=True, verbose_name='人气', null=True)
    userUuid = models.ForeignKey('User', models.CASCADE, db_column='userUuid',
                                 null=True, related_name='userRankUuid', to_field='uuid')
    activityUuid = models.ForeignKey(Activity, models.CASCADE, db_column='userUuid',
                                     null=True, related_name='activityUuid', to_field='uuid')

    class Meta:
        db_table = 'tb_rank'


class Records(models.Model, BaseModle):
    """播放记录和最近录过记录表"""
    playdatetime = models.DateTimeField(blank=True, verbose_name='播放/录制 日期时间', null=True)
    userUuid = models.ForeignKey('User', models.CASCADE, db_column='userUuid',
                                 null=True, related_name='userRecordUuid', to_field='uuid')
    workUuid = models.ForeignKey('Works', models.CASCADE, db_column='workUuid',
                                 null=True, related_name='workRecordUuid', to_field='uuid')
    record_type = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'tb_records'


class Relation(models.Model, BaseModle):
    """当前用户和其他用户关系表"""
    user = models.ForeignKey('User', models.DO_NOTHING, blank=True, null=True)
    relattion_type = models.IntegerField(blank=True, null=True)
    elation_user = models.ForeignKey('User', models.DO_NOTHING, blank=True, null=True)
    status = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'tb_relation'


class Search(models.Model, BaseModle):
    id = models.IntegerField(blank=True, null=True)
    keyword = models.CharField(max_length=32, blank=True, null=True)
    ordernum = models.IntegerField(blank=True, null=True)
    isdelete = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'tb_search'


class Searchhistory(models.Model, BaseModle):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=20, blank=True, null=True)
    searchtime = models.DateTimeField(db_column='searchTime', blank=True, null=True)
    user = models.ForeignKey('User', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        db_table = 'tb_searchhistory'


class Tag(models.Model, BaseModle):
    id = models.IntegerField(primary_key=True)
    code = models.CharField(max_length=20, blank=True, null=True)
    tag_name = models.CharField(max_length=32, blank=True, null=True)
    parent_id = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'tb_tag'


class Templatestory(models.Model, BaseModle):
    id = models.IntegerField(primary_key=True)
    icon = models.CharField(max_length=128, blank=True, null=True)
    intro = models.CharField(max_length=512, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    recordnum = models.IntegerField(blank=True, null=True)
    scene = models.CharField(max_length=16, blank=True, null=True)
    createtime = models.DateField(blank=True, null=True)

    class Meta:
        db_table = 'tb_templatestory'


class User(models.Model, BaseModle):
    """
    用户表
    """
    tb_field = models.ForeignKey('Searchhistory', models.DO_NOTHING, db_column='tb__id', blank=True,
                                 null=True)  # Field renamed because it ended with '_'.
    is_delete = models.IntegerField()
    forbiddentype = models.CharField(db_column='forbiddenType', max_length=16, null=True)
    starttime = models.DateTimeField(db_column='startTime', blank=True, null=True)
    endtime = models.DateTimeField(db_column='endTime', blank=True, null=True)
    tel = models.CharField(max_length=20)
    userphoto = models.CharField(max_length=255, blank=True, null=True)
    username = models.CharField(max_length=30)
    password = models.CharField(max_length=256)
    gender = models.IntegerField(blank=True, null=True)
    status = models.IntegerField(blank=True, null=True)
    regdate = models.DateField(blank=True, null=True)
    roles = models.CharField(max_length=1024, blank=True, null=True)
    lastvisit = models.DateTimeField(blank=True, null=True)
    version = models.ForeignKey('Version', models.CASCADE, blank=True, null=True)

    class Meta:
        db_table = 'tb_user'


class Version(models.Model, BaseModle):
    id = models.IntegerField(primary_key=True)
    version = models.CharField(max_length=26, blank=True, null=True)
    name = models.CharField(max_length=26, blank=True, null=True)
    company = models.CharField(max_length=26, blank=True, null=True)

    class Meta:
        db_table = 'tb_version'


class Viewpager(models.Model, BaseModle):
    id = models.IntegerField(primary_key=True)
    titlte = models.CharField(max_length=64, blank=True, null=True)
    ordernum = models.IntegerField(db_column='orderNum', blank=True, null=True)
    mediauuid = models.CharField(db_column='mediaUuid', max_length=64, blank=True, null=True)
    starttime = models.DateTimeField(blank=True, null=True)
    endtime = models.DateTimeField(blank=True, null=True)
    jumptype = models.CharField(db_column='jumpType', max_length=64, blank=True, null=True)
    works_id = models.CharField(max_length=64, blank=True, null=True)
    isusing = models.IntegerField(db_column='isUsing', blank=True, null=True)

    class Meta:
        db_table = 'tb_viewpager'


class Works(models.Model, BaseModle):
    id = models.IntegerField(primary_key=True)
    isupload = models.IntegerField(blank=True, null=True)
    mediauuid = models.CharField(db_column='mediaUuid', max_length=64, blank=True, null=True)
    uservolume = models.IntegerField(blank=True, null=True)
    bgm = models.CharField(max_length=126, blank=True, null=True)
    bgmvolume = models.IntegerField(blank=True, null=True)
    recordtype = models.IntegerField(blank=True, null=True)
    recorddate = models.DateTimeField(blank=True, null=True)
    playtimes = models.IntegerField(blank=True, null=True)
    workstype = models.IntegerField(blank=True, null=True)
    template_id = models.CharField(max_length=10, blank=True, null=True)
    name = models.CharField(max_length=128, blank=True, null=True)
    icon = models.CharField(max_length=512, blank=True, null=True)
    feeling = models.CharField(max_length=512, blank=True, null=True)
    workstime = models.TimeField(blank=True, null=True)
    tags = models.CharField(max_length=16, blank=True, null=True)
    module_id = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        db_table = 'tb_works'
