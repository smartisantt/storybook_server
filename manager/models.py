#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
import logging

from django.db import models, transaction

from common.models import BaseModle


class Activity(BaseModle, models.Model):
    """
    活动表
    """
    name = models.CharField(max_length=255, verbose_name="活动名称", null=True)
    intro = models.CharField(max_length=1024, verbose_name="活动介绍", null=True)
    status = models.CharField(max_length=32, verbose_name="活动状态", null=True)
    mediaUuid = models.CharField(max_length=256, verbose_name="活动图片", null=True)
    startTime = models.DateTimeField(verbose_name='活动开始时间', null=True)
    endTime = models.DateTimeField(verbose_name='活动结束时间', null=True)

    class Meta:
        db_table = 'tb_activity'


class Ad(BaseModle, models.Model):
    """
    首页弹屏广告
    """
    mediaUuid = models.CharField(max_length=64, verbose_name='广告图片', null=True)
    jumpUrl = models.CharField(max_length=255, verbose_name='跳转地址', null=True)
    startTime = models.DateTimeField(verbose_name='时效开始时间', null=True)
    endTime = models.DateTimeField(verbose_name='时效结束时间', null=True)
    isDelete = models.BooleanField(verbose_name='软删除', null=True)

    class Meta:
        db_table = 'tb_ad'


class Baby(BaseModle, models.Model):
    """
    宝宝表
    """
    name = models.CharField(max_length=24, verbose_name='宝宝姓名', null=True)
    babyBirthday = models.DateTimeField(verbose_name='宝宝生日', null=True)
    gender = models.IntegerField(default=False)

    class Meta:
        db_table = 'tb_baby'


class Bgm(BaseModle, models.Model):
    """
    背景音乐
    """
    name = models.CharField(max_length=32, null=True)
    mediaUrl = models.CharField(max_length=255, null=True)
    bgmTime = models.IntegerField(verbose_name='背景音乐时长', null=True)
    isUsing = models.IntegerField(verbose_name='是否在用', null=True)  # 0 停用 1 在用
    sortNum = models.IntegerField(verbose_name='排序编号', null=True)

    class Meta:
        db_table = 'tb_bgm'


class Feedback(BaseModle, models.Model):
    """
    用户反馈表
    """
    questiontype = models.CharField(max_length=26,
                                    null=True)
    content = models.CharField(max_length=1024, null=True)
    mediauuid1 = models.CharField(max_length=64, null=True)
    mediauuid2 = models.CharField(max_length=64, null=True)
    mediauuid3 = models.CharField(max_length=64, null=True)
    mediauuid4 = models.CharField(max_length=64, null=True)
    tel = models.CharField(max_length=20, null=True)
    userUuid = models.ForeignKey('User', models.CASCADE, null=True, related_name='userFeedbackUuid', to_field='uuid')

    class Meta:
        db_table = 'tb_feedback'


class LoginLog(BaseModle, models.Model):
    """
    登录日志
    """
    ipAddr = models.CharField(max_length=126, verbose_name='IP地址', null=True)
    devCode = models.CharField(max_length=256, verbose_name='设备编号', null=True)
    userUuid = models.ForeignKey('User', models.CASCADE, null=True, related_name='longinLogUuid', to_field='uuid')

    class Meta:
        db_table = 'tb_login_log'


class Module(BaseModle, models.Model):
    """
    首页显示模块
    """
    name = models.CharField(max_length=32, null=True)       # 显示模块名 抢先听
    ordernNum = models.IntegerField(verbose_name='排序编号', null=True)
    type = models.CharField(max_length=32, null=True)       #显示模块类型 MOD1  MOD2  MOD3  MOD4
    showNum = models.IntegerField(null=True)

    class Meta:
        db_table = 'tb_module'


class Rank(BaseModle, models.Model):
    """活动排名  用户和活动中间的关联表"""
    userRank = models.IntegerField(null=True)
    popularity = models.IntegerField(verbose_name='人气', null=True)
    userUuid = models.ForeignKey('User', models.CASCADE, null=True, related_name='userRankUuid', to_field='uuid')
    activityUuid = models.ForeignKey(Activity, models.CASCADE, null=True, related_name='activityRankUuid',
                                     to_field='uuid')
    workUuid = models.OneToOneField('Works', models.CASCADE, null=True, related_name='workRankUuid', to_field='uuid')

    class Meta:
        db_table = 'tb_rank'


class Sign(BaseModle, models.Model):
    """活动报名表"""
    activitUuid = models.ForeignKey(Activity, models.CASCADE, null=True, related_name='activitSignUuid',
                                    to_field='uuid')
    userUuid = models.ForeignKey('User', models.CASCADE, null=True, related_name='userSignUuid', to_field='uuid')

    class Meta:
        db_table = 'tb_sign'


class Records(BaseModle, models.Model):
    """播放记录/最近录过记录表"""
    userUuid = models.ForeignKey('User', models.CASCADE, null=True, related_name='userRecordUuid', to_field='uuid')
    workUuid = models.ForeignKey('Works', models.CASCADE, null=True, related_name='workRecordUuid', to_field='uuid')
    recordType = models.CharField(max_length=20, null=True)  # 播放记录  / 最近录过

    class Meta:
        db_table = 'tb_records'


class FriendShip(BaseModle, models.Model):
    """当前用户和其他用户关系表"""
    followed = models.ForeignKey('User', on_delete=models.CASCADE, related_name='followed')
    follower = models.ForeignKey('User', on_delete=models.CASCADE, related_name='follower')
    status = models.BooleanField(default=False)  # 状态，是否取消0/关注1

    class Meta:
        db_table = 'tb_friend'


class HotSearch(BaseModle, models.Model):
    """
    热搜词
    """
    keyword = models.CharField(max_length=32, null=True)  # 搜索关键词
    orderNum = models.IntegerField(null=True)  # 排列序号
    isDelete = models.BooleanField(default=False)

    class Meta:
        db_table = 'tb_search'


class SearchHistory(BaseModle, models.Model):
    """
    搜索历史表
    """
    searchName = models.CharField(max_length=20, null=True)  # 搜索名字
    searchTime = models.DateTimeField(null=True)
    userUuid = models.ForeignKey('User', models.CASCADE, null=True, related_name='userSearchUuid', to_field='uuid')

    class Meta:
        db_table = 'tb_searchhistory'


class Tag(BaseModle, models.Model):
    """
    标签字典表
    """
    code = models.CharField(max_length=20, null=True)  # 编码
    tagName = models.CharField(max_length=32, null=True)  # 标签名字
    iconUrl = models.CharField(max_length=256, null=True) # 分类图标
    sortNum = models.IntegerField(verbose_name='排序编号', null=True) # 排列顺序
    parent = models.ForeignKey(to='self', on_delete=models.CASCADE,related_name='child_tag',
                               db_column='parent_id', to_field='uuid', null=True)  # 爸爸标签id
    isUsing = models.BooleanField(default=True)                     # 标签状态停用还是使用
    isDelete = models.BooleanField(default=False)                    # 标签是否删除

    def __str__(self):
        return self.tagName

    class Meta:
        db_table = 'tb_tag'




class TemplateStory(BaseModle, models.Model):
    """
    模板故事
    """
    faceUrl = models.CharField(max_length=255, null=True)  # 封面图片
    listUrl = models.CharField(max_length=255, null=True)  # 列表图片
    title = models.CharField(max_length=512, null=True)  # 标题
    intro = models.CharField(max_length=512, null=True)  # 介绍(标题)
    content = models.TextField(null=True)  # 故事内容
    recordNum = models.IntegerField(null=True)  # 录制次数
    status = models.CharField(max_length=32, null=True, default="normal")  # normal启用 forbid禁用 destroy删除
    isRecommd = models.BooleanField(default=True)  # 显示位置 默认推荐 否则是 最新
    isTop = models.IntegerField(default=0)  # 置顶 默认为0 置顶为1
    tags = models.ManyToManyField(Tag)

    class Meta:
        db_table = 'tb_templatestory'


class User(BaseModle, models.Model):
    """
    用户表
    """
    userID = models.CharField(max_length=64, default=None)
    username = models.CharField(max_length=30)
    startTime = models.DateTimeField(null=True)  # 禁止起始时间
    endTime = models.DateTimeField(null=True)  # 禁止结束时间
    tel = models.CharField(max_length=20)
    userLogo = models.CharField(max_length=255, null=True)  # 用户头像
    gender = models.IntegerField(null=True)  # 性别 0未知  1男  2女
    status = models.CharField(max_length=64, null=True)  # 状态 normal  destroy  forbbiden_login  forbbiden_say
    roles = models.CharField(max_length=1024, null=True)  # 角色 normalUser adminUser

    versionUuid = models.ForeignKey('Version', models.CASCADE, null=True, related_name='versionUserUuid',
                                    to_field='uuid')
    works = models.ManyToManyField(to='Works', through=Records)

    class Meta:
        db_table = 'tb_user'

    def get_follower(self):
        '''
        folloer  关注的人
        :return:
        '''
        user_list = []
        for followed_user in self.followed.all():
            user_list.append(followed_user.follower)
        return user_list

    def get_followed(self):
        '''
        followed 关注我的人
        :return:
        '''
        user_list = []
        for follower_user in self.follower.all():
            user_list.append(follower_user.followed)
        return user_list

    def set_follower(self, uuid):
        '''
        follow some user use uuid
        :param id:
        :return:
        '''
        try:
            user = User.objects.get(uuid=uuid)
        except Exception as e:
            logging.error(str(e))
            return False
        # 这是关注的逻辑
        friendship = FriendShip()
        friendship.followed = self
        friendship.follower = user
        try:
            with transaction.atomic():
                friendship.save()
        except Exception as e:
            logging.error(str(e))
            return False
        return True


class Version(BaseModle, models.Model):
    """
    版本信息表
    """
    version = models.CharField(max_length=26, null=True)  # 版本号
    name = models.CharField(max_length=26, null=True)  # app名字
    company = models.CharField(max_length=26, null=True)  # 公司名
    status = models.CharField(max_length=32, null=True)  # 状态 dafault 默认使用

    class Meta:
        db_table = 'tb_version'


class Viewpager(BaseModle, models.Model):
    """
    轮播图
    """
    title = models.CharField(max_length=64, null=True)
    orderNum = models.IntegerField(null=True)  # 显示序号  数字越小越优先显示
    mediaUrl = models.CharField(max_length=255, null=True)  # 轮播图片
    startTime = models.DateTimeField(null=True)  # 有效起始时间
    endTime = models.DateTimeField(null=True)
    jumpType = models.CharField(max_length=64, null=True)  # 跳转类型 1专辑 2作品 3故事 4外部链接
    targetUuid = models.CharField(max_length=128, null=True)  # 跳转uuid
    isUsing = models.BooleanField(default=True)  #

    class Meta:
        db_table = 'tb_viewpager'


class Album(BaseModle, models.Model):
    """
    专辑
    """
    title = models.CharField(max_length=64, null=True)
    intro = models.CharField(max_length=256, null=True)
    mediaUuid = models.CharField(max_length=64, null=True)  # 专辑封面
    status = models.CharField(max_length=32, null=True)  # 专辑状态
    tags = models.ManyToManyField(Tag)  # 标签

    class Meta:
        db_table = 'tb_album'


class Works(BaseModle, models.Model):
    """
    作品表自由录制和模板作品
    """
    isUpload = models.IntegerField(default=1)  # 是否上传 0 没有传  1 上传到服务器
    voiceUrl = models.CharField(max_length=255, null=True)  # 用户的声音
    userVolume = models.FloatField(null=True)  # 用户音量
    bgmUuid = models.ForeignKey(Bgm, on_delete=models.CASCADE, related_name='bgmWorksUuid', to_field='uuid')
    bgmVolume = models.FloatField(null=True)  # 背景音乐音量
    recordType = models.IntegerField(null=True)  # 录制形式 0宝宝录制 1爸妈录制

    playTimes = models.IntegerField(null=True)  # 播放次数
    worksType = models.BooleanField(default=True)  # 作品类型  是用的模板1 还是自由录制0
    templateUuid = models.ForeignKey(TemplateStory, on_delete=models.CASCADE, related_name='templateStoryUuid',
                                     to_field='uuid', null=True)  # 作品关联的模板（如果不是自由录制的作品）
    title = models.CharField(max_length=128, null=True)  # 自由录制的标题
    bgUrl = models.CharField(max_length=255, null=True)  # 封面图片
    feeling = models.CharField(max_length=512, null=True)  # 录制感受
    worksTime = models.IntegerField(null=True)  # 作品时长
    tags = models.ManyToManyField(Tag)  # 作品标签
    moduleUuid = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='moduleWorksUuid',
                                   to_field='uuid', null=True)  # 在首页哪个模块显示
    albumUuid = models.ForeignKey(Album, on_delete=models.CASCADE, related_name='albumWorkUuid', to_field='uuid',
                                  null=True)  # 专辑
    userUuid = models.ForeignKey(User, on_delete=models.CASCADE, related_name='userWorkUuid', to_field='uuid',
                                  null=True)  # 用户
    checkStatus = models.CharField(max_length=64, null=True)  # 审核状态 unCheck待审核 check审核通过 checkFail审核不通过
    checkInfo = models.CharField(max_length=256, null=True)  # 审核信息，审核被拒绝原因
    isDelete= models.BooleanField(default=False)    # 软删除

    class Meta:
        db_table = 'tb_works'
