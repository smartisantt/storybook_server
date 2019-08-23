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
    url = models.CharField(max_length=255, verbose_name="活动url", null=True)
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
    type = models.IntegerField(null=True)  # 0 活动 1 专辑 2 音频 3 商品 4外部链接
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
    type = models.IntegerField(null=True)  # 反馈问题类型 1产品建议 2功能异常 3其他问题
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
    userAgent = models.CharField(max_length=256, verbose_name='登录平台', null=True)
    isManager = models.BooleanField(default=False)  # 0 客户端登录  1 是后台管理端

    class Meta:
        db_table = 'tb_login_log'


class Operation(BaseModle, models.Model):
    """后台人员操作记录表"""
    adminUserUuid = models.CharField(max_length=64, null=True)
    operation = models.CharField(max_length=255, null=True)  # create retrieve update delete
    objectUuid = models.CharField(max_length=64, null=True)
    remark = models.CharField(max_length=1024, null=True)

    class Meta:
        db_table = "tb_operation_record"


class Module(BaseModle, models.Model):
    """
    首页显示模块
    """

    orderNum = models.IntegerField(verbose_name='排序编号', null=True)
    type = models.CharField(max_length=32, null=True)  # 显示模块类型 MOD1每日一读  MOD2抢先听  MOD3热门推荐
    contentType = models.IntegerField(null=True)  # 1 自由音频 2 模板音频 3 专辑
    audioUuid = models.ForeignKey('AudioStory', on_delete=models.CASCADE, related_name='moduleAudioUuid',
                                  to_field='uuid', null=True)
    albumUuid = models.ForeignKey('Album', on_delete=models.CASCADE, related_name='moduleAlbumUuid',
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
    votes = models.IntegerField(null=True, default=0)
    status = models.IntegerField(default=0)  # 状态 0正常 1禁用 2删除
    inviter = models.CharField(max_length=32, null=True)  # 邀请人 or 门店uuid

    class Meta:
        db_table = 'tb_gameinfo'


class VoteBehavior(BaseModle, models.Model):
    """
    投票行为表
    """
    userUuid = models.ForeignKey('User', models.CASCADE, null=True, related_name='userVoteBehavior', to_field='uuid')
    gameUuid = models.ForeignKey('GameInfo', models.CASCADE, null=True, related_name='gameVoteBehavior',
                                 to_field='uuid')
    voteDate = models.DateField(null=True)

    class Meta:
        db_table = 'tb_vote_behavior'


class Shop(BaseModle, models.Model):
    """
    门店信息表
    """
    owner = models.CharField(max_length=32, null=True)  # 店主姓名
    tel = models.CharField(max_length=20, null=True)  # 店主号码
    shopNo = models.CharField(max_length=32, null=True)  # 门店编号
    shopName = models.CharField(max_length=64, null=True)  # 门店名称
    isDelete = models.BooleanField(default=False)

    class Meta:
        db_table = 'tb_shop'


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
    isTop = models.IntegerField(default=0)  # 置顶 1置顶 2不设置 3置底
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
    readDate = models.DateField(null=True)  # 连续阅读最后时间
    readDays = models.IntegerField(default=0)  # 连续阅读天数
    loginType = models.CharField(max_length=32, null=True)  # 登录方式
    inviter = models.CharField(max_length=32, null=True)  # 邀请人uuid or 门店uuid

    class Meta:
        db_table = 'tb_user'

    def __str__(self):
        return self.nickName


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
    type = models.IntegerField(null=True)  # 跳转类型
    # {value: 0, label: "活动"},
    # {value: 1, label: "专辑"},
    # {value: 2, label: "音频"},
    # {value: 3, label: "商品"},
    # {value: 4, label: "链接"},
    # {value: 5, label: "模板"}
    target = models.CharField(max_length=255, null=True)  # 跳转uuid
    isUsing = models.BooleanField(default=True)  #
    location = models.IntegerField(null=True)  # 1：录制首页轮播图 0：首页轮播图
    isDelete = models.BooleanField(default=False)  # 1 删除   0 没有删除

    class Meta:
        db_table = 'tb_viewpager'


class Album(BaseModle, models.Model):
    """专辑"""
    title = models.CharField(max_length=64, verbose_name='专辑名称', null=False, default='专辑名称')
    intro = models.CharField(max_length=256, verbose_name='专辑介绍', null=False, default='专辑介绍')
    faceIcon = models.CharField(max_length=255, verbose_name='列表图', null=True)  # 专辑封面
    bgIcon = models.CharField(max_length=255, verbose_name='背景图', null=True)  # 专辑封面
    creator = models.ForeignKey('User', on_delete=models.CASCADE, related_name='creatorUuid', to_field='uuid',
                                verbose_name='音频创建者', null=True)
    author = models.ForeignKey('User', on_delete=models.CASCADE, related_name='authorUuid', to_field='uuid',
                               verbose_name='作者', null=True)
    isDelete = models.BooleanField(default=False)  # 1 删除   0 没有删除
    checkStatus = models.CharField(max_length=64, null=True)
    # 审核状态 unCheck待审核 check审核通过 checkFail审核不通过 exemption 后台创建免审核
    remark = models.CharField(max_length=1024, null=True)  # 不通过的理由
    isManagerCreate = models.IntegerField(default=False, verbose_name='是否是官方上传')
    tags = models.ManyToManyField(Tag)  # 标签
    audioStory = models.ManyToManyField(to='AudioStory', through='AlbumAudioStory')

    class Meta:
        db_table = 'tb_album'


class AlbumAudioStory(BaseModle, models.Model):
    """专辑和音频的中间实体"""
    album = models.ForeignKey(to=Album, on_delete=models.CASCADE)
    audioStory = models.ForeignKey(to='AudioStory', on_delete=models.CASCADE)
    isUsing = models.BooleanField(default=True, verbose_name="是否停用")

    class Meta:
        db_table = 'tb_album_audiostory'


class AudioStory(BaseModle, models.Model):
    """
    作品表自由录制和模板作品
    """
    isUpload = models.IntegerField(default=1)  # 是否上传 0 没有传  1 上传到服务器
    mixAudioUrl = models.CharField(max_length=255, null=True)  # 合成音频url
    voiceUrl = models.CharField(max_length=255, null=True)  # 用户的声音
    userVolume = models.FloatField(default=1.0)  # 用户音量
    bgm = models.ForeignKey('Bgm', on_delete=models.CASCADE, related_name='bgmaudiosUuid', to_field='uuid', null=True)
    bgmVolume = models.FloatField(default=1.0)  # 背景音乐音量
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
    # albumUuid = models.ForeignKey('Album', on_delete=models.CASCADE, related_name='albumAudioUuid', to_field='uuid',
    #                               null=True)  # 专辑
    userUuid = models.ForeignKey('User', on_delete=models.CASCADE, related_name='useAudioUuid', to_field='uuid',
                                 null=True)  # 用户
    checkStatus = models.CharField(max_length=64,
                                   null=True)  # 审核状态 unCheck待审核 check审核通过 checkFail审核不通过 exemption 后台上传免审核
    checkInfo = models.CharField(max_length=256, null=True)  # 审核信息，审核被拒绝原因
    isDelete = models.BooleanField(default=False)  # 软删除
    fileSize = models.IntegerField(null=True)  # 音频文件大小
    taskID = models.CharField(max_length=255, null=True)  # 任务轮训id
    interfaceStatus = models.CharField(max_length=64, default="unCheck")  # unCheck待审核 check审核通过 checkFail审核不通过

    class Meta:
        db_table = 'tb_audio_story'


class Behavior(BaseModle, models.Model):
    """
    用户对作品的行为记录表
    """
    userUuid = models.ForeignKey(User, on_delete=models.CASCADE, related_name='busUuid', to_field='uuid', null=True)
    audioUuid = models.ForeignKey(AudioStory, on_delete=models.CASCADE, related_name='bauUuid', to_field='uuid',
                                  null=True)
    type = models.IntegerField(null=True)  # 行为类型 1:点赞 2:评论 3:收藏 4:播放记录 5:最近录过
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


class Listen(BaseModle, models.Model):
    """
    用户听单
    """
    userUuid = models.ForeignKey('User', on_delete=models.CASCADE, related_name='userListenUuid', to_field='uuid',
                                 null=True)
    name = models.CharField(max_length=128, null=True)
    icon = models.CharField(max_length=255, null=True)
    intro = models.CharField(max_length=500, null=True)
    status = models.IntegerField(null=True, default=0)  # 状态 0：正常 1：删除

    class Meta:
        db_table = 'tb_listen'


class ListenAudio(BaseModle, models.Model):
    """
    听单列表
    """
    listenUuid = models.ForeignKey('Listen', on_delete=models.CASCADE, related_name='listListenUuid', to_field='uuid',
                                   null=True)
    audioUuid = models.ForeignKey('AudioStory', on_delete=models.CASCADE, related_name='listAudioUuid', to_field='uuid',
                                  null=True)
    status = models.IntegerField(null=True, default=0)  # 状态 0：正常 1：删除

    class Meta:
        db_table = 'tb_listen_audio'


class UserPrize(BaseModle):
    """
    用户奖品
    """
    orderNum = models.CharField(max_length=255, verbose_name='订单号', null=True)
    userUuid = models.ForeignKey('User', on_delete=models.CASCADE, related_name='userDeliveryUuid', to_field='uuid',
                                 null=True, verbose_name="中奖用户")
    deliveryNum = models.CharField(max_length=255, verbose_name='运单号', null=True)
    prizeUuid = models.ForeignKey('Prize', on_delete=models.CASCADE, related_name='prizeUuid', to_field='uuid',
                                  null=True, verbose_name="奖品")
    receiveUuid = models.ForeignKey('ReceivingInfo', on_delete=models.CASCADE, related_name='receivePrizeUuid',
                                    to_field='uuid',
                                    null=True, verbose_name="收货信息")
    # 填写订单日期
    expressDate = models.DateTimeField(verbose_name='填写快递日期', null=True)
    # 物流的详细信息
    expressDetail = models.TextField(null=True)
    #  为空这是无效快递或者没有填写快递
    #  快递单当前状态，包括0在途，1揽收，2疑难，3签收，4退签，5派件，6退回等7个状态
    expressState = models.IntegerField(null=True)
    classNo = models.CharField(max_length=64, null=True)  # 课程号兑换码
    orderStatus = models.IntegerField(default=1)#1:未发货 2：已发货 3：已签收

    class Meta:
        db_table = 'tb_user_prize'


class Prize(BaseModle):
    """
    奖品设置表
    """
    activityUuid = models.ForeignKey("Activity", on_delete=models.CASCADE, related_name='activityPrizeUuid',
                                     to_field='uuid',
                                     null=True, )
    name = models.CharField(max_length=128, null=True)  # 奖品名称
    icon = models.CharField(max_length=255, verbose_name='奖品图', null=True)
    inventory = models.PositiveIntegerField(default=0)  # 库存
    status = models.IntegerField(default=1)  # 1 启用  0 禁用
    isDelete = models.BooleanField(verbose_name='软删除', default=False)
    type = models.IntegerField(default=2)  # 0 月卡 1 季卡  3 年卡 9 实物商品
    probability = models.FloatField(default=0.0, verbose_name="中奖概率")

    class Meta:
        db_table = "tb_prize"


class ReceivingInfo(BaseModle):
    """
    收货信息
    """
    userUuid = models.ForeignKey('User', on_delete=models.CASCADE, related_name='userShippingAddressUuid',
                                 to_field='uuid',
                                 null=True, verbose_name="用户")
    address = models.CharField(max_length=255, verbose_name='收货地址', null=True)
    defaultAddress = models.BooleanField(default=0)  # 0 不是默认地址  1 是默认地址
    contact = models.CharField(max_length=32, null=False)  # 收件人
    tel = models.CharField(max_length=20, null=True)

    class Meta:
        db_table = "tb_receiving_info"
