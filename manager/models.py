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
    status = models.CharField(max_length=32, verbose_name="活动状态", null=True)  # normal正常 forbid 禁用 destroy 删除
    icon = models.CharField(max_length=256, verbose_name="活动图片", null=True)
    startTime = models.DateTimeField(verbose_name='活动开始时间', null=True)
    endTime = models.DateTimeField(verbose_name='活动结束时间', null=True)

    class Meta:
        db_table = 'tb_activity'


class Ad(BaseModle, models.Model):
    """
    首页弹屏广告
    """
    name = models.CharField(max_length=64, null=True)
    icon = models.CharField(max_length=255, verbose_name='广告图片', null=True)
    type = models.IntegerField(null=True)  # 跳转类型 0活动 1专辑 2audiostory 3story 4外部链接
    target = models.CharField(max_length=255, null=True)  # 跳转uuid 或者外部url
    orderNum = models.IntegerField(null=True)  # 显示序号  数字越小越优先显示
    startTime = models.DateTimeField(verbose_name='时效开始时间', null=True)
    endTime = models.DateTimeField(verbose_name='时效结束时间', null=True)
    isDelete = models.BooleanField(verbose_name='软删除', default=False)

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
    url = models.CharField(max_length=255, null=True)
    duration = models.IntegerField(verbose_name='背景音乐时长', null=True)
    status = models.CharField(max_length=64, verbose_name='状态', default="normal")  # forbid 停用 normal正常 在用  destroy 删除
    sortNum = models.IntegerField(verbose_name='排序编号', null=True)

    class Meta:
        db_table = 'tb_bgm'


class Feedback(BaseModle, models.Model):
    """
    用户反馈表
    """
    type = models.IntegerField(max_length=26, null=True)  # 反馈问题类型 1产品建议 2功能异常 3其他问题
    content = models.CharField(max_length=1024, null=True)
    icon = models.CharField(max_length=1024, null=True)
    tel = models.CharField(max_length=20, null=True)
    userUuid = models.ForeignKey('User', models.CASCADE, null=True, related_name='userFeedbackUuid', to_field='uuid')
    status = models.IntegerField(default=0)  # 处理状态 0未处理 1已处理
    replyInfo = models.CharField(max_length=1024, null=True)  # 回复信息
    isRead = models.BooleanField(default=False)  # 用户是否已读

    class Meta:
        db_table = 'tb_feedback'


class LoginLog(BaseModle, models.Model):
    """登录日志"""
    ipAddr = models.CharField(max_length=126, verbose_name='IP地址', null=True)
    devCode = models.CharField(max_length=256, verbose_name='设备编号', null=True)
    userUuid = models.ForeignKey('User', models.CASCADE, null=True, related_name='longinLogUuid', to_field='uuid')
    platform = models.CharField(max_length=126, verbose_name='登录平台', null=True),    # ANDROID  / IOS / H5 / PC / WEAPP
    isManager = models.BooleanField(default=False)      # 0 客户端  1 是后台管理端

    class Meta:
        db_table = 'tb_login_log'


class Operation(BaseModle, models.Model):
    """后台人员操作记录表"""
    userUuid = models.ForeignKey('User', on_delete=models.CASCADE, related_name='oUserUuid', to_field='uuid')
    operation = models.CharField(max_length=255, null=True)     # create retrieve update delete
    objectUuid = models.CharField(max_length=64, unique=True)
    remark = models.CharField(max_length=255, null=True)

    class Meta:
        db_table = "tb_operation_record"


class Module(BaseModle, models.Model):
    """
    首页显示模块
    """

    orderNum = models.IntegerField(verbose_name='排序编号', null=True)
    type = models.CharField(max_length=32, null=True)  # 显示模块类型 MOD1每日一读  MOD2抢先听  MOD3热门推荐
    audioUuid = models.ForeignKey('AudioStory', on_delete=models.CASCADE, related_name='moduleAudioUuid',
                                  to_field='uuid', null=True)
    isDelete = models.BooleanField(default=False)

    class Meta:
        db_table = 'tb_module'


class GameInfo(BaseModle, models.Model):
    """活动排名  用户和活动中间的关联表"""
    userUuid = models.ForeignKey('User', models.CASCADE, null=True, related_name='userRankUuid', to_field='uuid')
    activityUuid = models.ForeignKey('Activity', models.CASCADE, null=True, related_name='activityRankUuid',
                                     to_field='uuid')
    audioUuid = models.ForeignKey('AudioStory', models.CASCADE, null=True, related_name='audioRankUuid',
                                  to_field='uuid')
    status = models.IntegerField(default=0)  # 状态 0正常 1禁用 2删除

    class Meta:
        db_table = 'tb_gameinfo'


class FriendShip(BaseModle, models.Model):
    """当前用户和其他用户关系表"""
    follows = models.ForeignKey('User', on_delete=models.CASCADE, related_name='follows')
    followers = models.ForeignKey('User', on_delete=models.CASCADE, related_name='followers')
    status = models.BooleanField(default=False)  # 状态，是否取消0/关注1

    class Meta:
        db_table = 'tb_friend'


class HotSearch(BaseModle, models.Model):
    """
    热搜词
    """
    keyword = models.CharField(max_length=32, null=True)  # 搜索关键词
    isTop = models.IntegerField(default=0)  # 0:不置顶  1：置顶 后置顶的在前面加1
    searchNum = models.IntegerField(null=True, default=0)
    isDelete = models.BooleanField(default=False)
    isAdminAdd = models.BooleanField(default=False)  # 关键词 1 后台添加  0 不是后台添加

    class Meta:
        db_table = 'tb_search'


class SearchHistory(BaseModle, models.Model):
    """
    搜索历史表
    """
    searchName = models.CharField(max_length=20, null=True)  # 搜索名字
    userUuid = models.ForeignKey('User', models.CASCADE, null=True, related_name='userSearchUuid', to_field='uuid')

    class Meta:
        db_table = 'tb_searchhistory'


class Tag(BaseModle, models.Model):
    """
    标签字典表
    """
    code = models.CharField(max_length=20, null=True)  # 编码
    name = models.CharField(max_length=32, null=True)  # 标签名字
    icon = models.CharField(max_length=256, null=True)  # 分类图标
    sortNum = models.IntegerField(verbose_name='排序编号', null=True)  # 排列顺序
    parent = models.ForeignKey(to='self', on_delete=models.CASCADE, related_name='child_tag',
                               db_column='parent_id', to_field='uuid', null=True)  # 爸爸标签id
    isUsing = models.BooleanField(default=True)  # 标签状态停用还是使用
    isDelete = models.BooleanField(default=False)  # 标签是否删除

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'tb_tag'


class Story(BaseModle, models.Model):
    """
    模板故事
    """
    faceIcon = models.CharField(max_length=255, null=True)  # 封面图片
    listIcon = models.CharField(max_length=255, null=True)  # 列表图片
    name = models.CharField(max_length=512, null=True)  # 标题
    intro = models.CharField(max_length=512, null=True)  # 介绍(标题)
    content = models.TextField(null=True)  # 故事内容
    recordNum = models.IntegerField(null=True)  # 录制次数
    status = models.CharField(max_length=32, null=True, default="normal")  # normal启用 forbid禁用 destroy删除
    isRecommd = models.BooleanField(default=True)  # 显示位置 默认1推荐 否则是 0最新
    isTop = models.IntegerField(default=0)  # 置顶 默认为0 置顶为1
    tags = models.ManyToManyField(Tag)

    class Meta:
        db_table = 'tb_story'


class User(BaseModle, models.Model):
    """
    用户表
    """
    userID = models.CharField(max_length=64, default=None)
    nickName = models.CharField(max_length=30)
    startTime = models.DateTimeField(null=True)  # 禁止起始时间
    endTime = models.DateTimeField(null=True)  # 禁止结束时间
    tel = models.CharField(max_length=20)
    intro = models.CharField(max_length=255, null=True)  # 用户介绍
    avatar = models.CharField(max_length=255, null=True)  # 用户头像
    gender = models.IntegerField(null=True)  # 性别 0未知  1男  2女
    status = models.CharField(max_length=64, null=True)  # 状态 normal  destroy  forbbiden_login  forbbiden_say
    settingStatus = models.CharField(max_length=64, null=True)  # 设置的禁止方式 forbbiden_login  forbbiden_say
    roles = models.CharField(max_length=1024, null=True)  # 角色 normalUser adminUser
    city = models.CharField(max_length=255, null=True)

    versionUuid = models.ForeignKey('Version', models.CASCADE, null=True, related_name='versionUserUuid',
                                    to_field='uuid')

    class Meta:
        db_table = 'tb_user'

    def get_follows(self):
        '''
        follows  我关注的人
        :return:
        '''
        user_list = []
        for follows_user in self.follows.all():
            user_list.append(follows_user.followers)
        return user_list

    def get_followers(self):
        '''
        followed 关注我的人
        :return:
        '''
        user_list = []
        for followers_user in self.followers.all():
            user_list.append(followers_user.follows)
        return user_list

    def set_follows(self, uuid):
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
        friendship.follows = self
        friendship.followers = user
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


class CycleBanner(BaseModle, models.Model):
    """
    轮播图
    """
    name = models.CharField(max_length=64, null=True)
    orderNum = models.IntegerField(null=True)  # 显示序号  数字越小越优先显示
    icon = models.CharField(max_length=255, null=True)  # 轮播图片
    startTime = models.DateTimeField(null=True)  # 有效起始时间
    endTime = models.DateTimeField(null=True)
    type = models.IntegerField(null=True)  # 跳转类型 0活动 1专辑 2audiostory 3商品 4外部链接
    target = models.CharField(max_length=255, null=True)  # 跳转uuid
    isUsing = models.BooleanField(default=True)  #
    location = models.IntegerField(null=True)  # 1：录制首页轮播图 0：首页轮播图
    isDelete = models.BooleanField(default=False)  # 1 删除   0 没有删除

    class Meta:
        db_table = 'tb_viewpager'


class Album(BaseModle, models.Model):
    """
    专辑
    """
    title = models.CharField(max_length=64, null=True)
    intro = models.CharField(max_length=256, null=True)
    icon = models.CharField(max_length=255, null=True)  # 专辑封面
    status = models.CharField(max_length=32, null=True)  # 专辑状态
    tags = models.ManyToManyField(Tag)  # 标签
    isDelete = models.BooleanField(default=False)  # 1 删除   0 没有删除

    class Meta:
        db_table = 'tb_album'


class AudioStory(BaseModle, models.Model):
    """
    作品表自由录制和模板作品
    """
    isUpload = models.IntegerField(default=1)  # 是否上传 0 没有传  1 上传到服务器
    voiceUrl = models.CharField(max_length=255, null=True)  # 用户的声音
    userVolume = models.FloatField(null=True)  # 用户音量
    bgm = models.ForeignKey('Bgm', on_delete=models.CASCADE, related_name='bgmaudiosUuid', to_field='uuid', null=True)
    bgmVolume = models.FloatField(null=True)  # 背景音乐音量
    type = models.IntegerField(null=True)  # 录制形式 0宝宝录制 1爸妈录制
    audioStoryType = models.BooleanField(default=True)  # 1模板录制 0 自由音频
    playTimes = models.IntegerField(null=True)  # 播放次数
    name = models.CharField(max_length=128, null=True)  # 自由录制的标题
    bgIcon = models.CharField(max_length=255, null=True)  # 封面图片
    remarks = models.CharField(max_length=512, null=True)  # 录制感受
    duration = models.IntegerField(null=True)  # 作品时长
    tags = models.ManyToManyField('Tag', related_name="tagsAudioStory")  # 作品标签
    storyUuid = models.ForeignKey('Story', on_delete=models.CASCADE, related_name='storyAudioStory',
                                  to_field='uuid', null=True)  # 作品关联的模板（如果不是自由录制的作品）
    albumUuid = models.ForeignKey('Album', on_delete=models.CASCADE, related_name='albumAudioUuid', to_field='uuid',
                                  null=True)  # 专辑
    userUuid = models.ForeignKey('User', on_delete=models.CASCADE, related_name='useAudioUuid', to_field='uuid',
                                 null=True)  # 用户
    checkStatus = models.CharField(max_length=64,
                                   null=True)  # 审核状态 unCheck待审核 check审核通过 checkFail审核不通过 exemption 后台上传免审核
    checkInfo = models.CharField(max_length=256, null=True)  # 审核信息，审核被拒绝原因
    isDelete = models.BooleanField(default=False)  # 软删除

    class Meta:
        db_table = 'tb_audio_story'


class Behavior(BaseModle, models.Model):
    """
    用户对作品的行为记录表
    """
    userUuid = models.ForeignKey(User, on_delete=models.CASCADE, related_name='busUuid', to_field='uuid', null=True)
    audioUuid = models.ForeignKey(AudioStory, on_delete=models.CASCADE, related_name='bauUuid', to_field='uuid',
                                  null=True)
    type = models.IntegerField(null=True)  # 行为类型 1:点赞 2:评论 3:喜欢 4:播放记录
    status = models.IntegerField(null=True, default=0)  # 状态 0：正常 1：取消
    remarks = models.CharField(max_length=256, null=True)

    class Meta:
        db_table = 'tb_behavior'


class ActivityConfig(BaseModle, models.Model):
    """
    活动参数配置表
    """
    praiseNum = models.IntegerField(null=True)  # 点赞所占比例
    playTimesNum = models.IntegerField(null=True)  # 播放所占比例
    status = models.IntegerField(null=True, default=0)  # 状态 0：正常 1：取消 2:删除 3：默认

    class Meta:
        db_table = 'tb_activity_config'
