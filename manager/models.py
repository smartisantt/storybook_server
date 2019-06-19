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


class Activity(BaseModle, models.Model):
    """
    活动表
    """
    name = models.CharField(max_length=255,  verbose_name="活动名称", null=True)
    intro = models.CharField(max_length=1024,  verbose_name="活动介绍", null=True)
    status = models.CharField(max_length=32,  verbose_name="活动状态", null=True)
    mediaUuid = models.CharField(max_length=256, verbose_name="活动图片",  null=True)
    starttime = models.DateTimeField( verbose_name='活动开始时间', null=True)
    endtime = models.DateTimeField( verbose_name='活动结束时间', null=True)

    class Meta:
        db_table = 'tb_activity'


class Ad(BaseModle, models.Model):
    """
    首页弹屏广告
    """
    mediaUuid = models.CharField(max_length=64,  verbose_name='广告图片', null=True)
    jumpUrl = models.CharField(max_length=128, verbose_name='跳转地址', null=True)
    starttime = models.DateTimeField( verbose_name='时效开始时间', null=True)
    endtime = models.DateTimeField( verbose_name='时效结束时间', null=True)
    isdelete = models.BooleanField( verbose_name='软删除', null=True)

    class Meta:
        db_table = 'tb_ad'


class Baby(BaseModle, models.Model):
    """
    宝宝表
    """
    name = models.CharField(max_length=24,  verbose_name='宝宝姓名', null=True)
    babybirthday = models.DateTimeField( verbose_name='宝宝生日', null=True)
    gender = models.IntegerField( null=True)

    class Meta:
        db_table = 'tb_baby'


class Bgm(BaseModle, models.Model):
    """
    背景音乐
    """
    name = models.CharField(max_length=32,  null=True)
    mediaUuid = models.CharField( max_length=64,  null=True)
    bgmTime = models.IntegerField(verbose_name='背景音乐时长',  null=True)
    isUsing = models.IntegerField( verbose_name='是否在用', null=True)  # 0 停用 1 在用
    sortNum = models.IntegerField( verbose_name='排序编号', null=True)

    class Meta:
        db_table = 'tb_bgm'


class Feedback(BaseModle, models.Model):
    """
    用户反馈表
    """
    questiontype = models.CharField( max_length=26, 
                                    null=True)
    content = models.CharField(max_length=1024,  null=True)
    mediauuid1 = models.CharField( max_length=64,  null=True)
    mediauuid2 = models.CharField( max_length=64,  null=True)
    mediauuid3 = models.CharField( max_length=64,  null=True)
    mediauuid4 = models.CharField( max_length=64,  null=True)
    tel = models.CharField(max_length=20,  null=True)
    userUuid = models.ForeignKey('User', models.CASCADE, null=True, related_name='userFeedbackUuid', to_field='uuid')

    class Meta:
        db_table = 'tb_feedback'


class LoginLog(BaseModle, models.Model):
    """
    登录日志
    """
    ipAddr = models.CharField(max_length=126, verbose_name='IP地址',  null=True)
    logDate = models.DateTimeField( verbose_name='登录日期时间', null=True)
    devCode = models.CharField(max_length=256, verbose_name='设备编号',  null=True)
    userUuid = models.ForeignKey('User', models.CASCADE, null=True, related_name='longinLogUuid', to_field='uuid')

    class Meta:
        db_table = 'tb_login_log'


class Module(BaseModle, models.Model):
    """
    首页显示模块
    """
    name = models.CharField(max_length=32,  null=True)
    ordernNum = models.IntegerField( verbose_name='排序编号', null=True)
    type = models.CharField(max_length=32,  null=True)

    class Meta:
        db_table = 'tb_module'


class Rank(BaseModle, models.Model):
    """活动排名  用户和活动中间的关联表"""
    userRank = models.IntegerField( null=True)
    popularity = models.IntegerField( verbose_name='人气', null=True)
    userUuid = models.ForeignKey('User', models.CASCADE, db_column='userUuid',
                                 null=True, related_name='userRankUuid', to_field='uuid')
    activityUuid = models.ForeignKey(Activity, models.CASCADE, db_column='userUuid',
                                     null=True, related_name='activityRankUuid', to_field='uuid')

    class Meta:
        db_table = 'tb_rank'


class Records(BaseModle, models.Model):
    """播放记录/最近录过记录表"""
    playdatetime = models.DateTimeField( verbose_name='播放/录制 日期时间', null=True)
    userUuid = models.ForeignKey('User', models.CASCADE, db_column='userUuid',
                                 null=True, related_name='userRecordUuid', to_field='uuid')
    workUuid = models.ForeignKey('Works', models.CASCADE, db_column='workUuid',
                                 null=True, related_name='workRecordUuid', to_field='uuid')
    record_type = models.IntegerField( null=True)  # 播放记录  / 最近录过

    class Meta:
        db_table = 'tb_records'


class Relation(BaseModle, models.Model):
    """当前用户和其他用户关系表"""
    userUuid = models.ForeignKey('User', models.CASCADE, null=True,
                                 related_name='userRelationUuid', to_field='uuid')
    relationType = models.CharField( null=True)  # 当前用户和另一用户的关系 粉丝 还是 关注
    relationUserUuid = models.ForeignKey('User', models.CASCADE, null=True,
                                         related_name='relationUserRelationUuid', to_field='uuid')
    status = models.BooleanField(default=False)    # 状态，是否取消0/关注1

    class Meta:
        db_table = 'tb_relation'


class HotSearch(BaseModle, models.Model):
    """
    热搜词
    """
    keyword = models.CharField(max_length=32, null=True) # 搜索关键词
    orderNum = models.IntegerField( null=True) # 排列序号
    isDelete = models.BooleanField(default=False)

    class Meta:
        db_table = 'tb_search'


class SearchHistory(BaseModle, models.Model):
    """
    搜索历史表
    """
    searchName = models.CharField(max_length=20,  null=True)  # 搜索名字
    searchTime = models.DateTimeField( null=True)
    userUuid = models.ForeignKey('User', models.CASCADE, null=True, related_name='userSearchUuid', to_field='uuid')

    class Meta:
        db_table = 'tb_searchhistory'


class Tag(BaseModle, models.Model):
    """
    标签字典表
    """
    code = models.CharField(max_length=20, null=True)       # 编码
    tag_name = models.CharField(max_length=32, null=True)   # 标签名字
    parent_id = models.IntegerField( null=True)  # 爸爸标签id

    class Meta:
        db_table = 'tb_tag'


class Templatestory(BaseModle, models.Model):
    """
    模板故事
    """
    mediaUuid = models.CharField(max_length=64, null=True)          # 封面图片
    intro = models.CharField(max_length=512,  null=True) # 介绍
    content = models.TextField( null=True)               # 故事内容
    recordNum = models.IntegerField( null=True)          # 录制次数
    tags = models.ManyToManyField(Tag)

    class Meta:
        db_table = 'tb_templatestory'


class User(BaseModle, models.Model):
    """
    用户表
    """
    username = models.CharField(max_length=30)
    is_delete = models.IntegerField(default=False)
    forbiddenType = models.CharField( max_length=16, null=True) # 禁止方式,（禁止登录，禁止发言）
    startTime = models.DateTimeField( null=True)
    endTime = models.DateTimeField(  null=True)
    tel = models.CharField(max_length=20)
    mediaUuid = models.CharField(max_length=64, null=True) # 用户头像
    gender = models.IntegerField( null=True) # 性别
    status = models.IntegerField( null=True) # 状态
    roles = models.CharField(max_length=1024,  null=True) # 角色
    lastvisit = models.DateTimeField( null=True) # 最近登录时间
    searchHistoryUuid = models.ForeignKey('Searchhistory', models.CASCADE, related_name='searchUserUuid',
                                          to_field='uuid', null=True)
    versionUuid = models.ForeignKey('Version', models.CASCADE, null=True, related_name='versionUserUuid',
                                    to_field='uuid' )
    works = models.ManyToManyField(to='Works', through=Records)

    class Meta:
        db_table = 'tb_user'


class Version(BaseModle, models.Model):
    """
    版本信息表
    """
    version = models.CharField(max_length=26,  null=True) # 版本号
    name = models.CharField(max_length=26,  null=True)   #app名字
    company = models.CharField(max_length=26,  null=True) # 公司名

    class Meta:
        db_table = 'tb_version'


class Viewpager(BaseModle, models.Model):
    """
    轮播图
    """
    titlte = models.CharField(max_length=64,  null=True)
    orderNum = models.IntegerField(null=True) # 显示序号
    mediaUuid = models.CharField(max_length=64, null=True) # 轮播图片
    startTime = models.DateTimeField(null=True) # 有效起始时间
    endTime = models.DateTimeField(null=True)
    jumpType = models.CharField(max_length=64, null=True) # 跳转类型
    worksUuid = models.ForeignKey('Works', on_delete=models.CASCADE, related_name='worksViewpagerUuid', to_field='uuid')
    isUsing = models.BooleanField(default=True) #

    class Meta:
        db_table = 'tb_viewpager'


class Works(BaseModle, models.Model):
    """
    作品表自由录制和模U板作品
    """
    isUpload = models.IntegerField(default=False)                  # 是否上传
    voiceMediaUuid = models.CharField( max_length=64,  null=True)        # 用户的声音
    uservolume = models.IntegerField( null=True)
    bgmUuid = models.ForeignKey(Bgm, on_delete=models.CASCADE, related_name='bgmWorksUuid', to_field='uuid')
    bgmvolume = models.IntegerField( null=True)                 # 背景音乐音量
    recordType = models.IntegerField( null=True)                # 录制形式
    recordDate = models.DateTimeField( null=True)               # 录制时间
    playTimes = models.IntegerField( null=True)                 # 播放次数
    worksType = models.BooleanField( default=True)               # 作品类型  是用的模板1 还是自由录制0
    templateUuid = models.CharField(max_length=10,  null=True)  # 作品关联的模板（如果不是自由录制的作品）
    title = models.CharField(max_length=128,  null=True)    # 自由录制的标题
    photoMediaUuid = models.CharField(max_length=64, null=True)     # 封面图片
    feeling = models.CharField(max_length=512,  null=True)  # 录制感受
    worksTime = models.IntegerField( null=True)             # 作品时长
    tags = models.ManyToManyField(Tag)                      # 作品标签
    moduleUuid = models.ForeignKey(Module, on_delete=models.CASCADE,
                                   related_name='moduleWorksUuid', to_field='uuid')    # 在首页哪个模块显示

    class Meta:
        db_table = 'tb_works'
