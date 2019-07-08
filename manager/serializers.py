
from datetime import datetime

from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from common.common import get_uuid
from manager.models import Tag, User, Bgm, AudioStory, Story, HotSearch, Ad, Module, Activity, GameInfo, CycleBanner, \
    Feedback
from utils.errors import ParamsException


class TemplateStory(object):
    pass


class StorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Story
        exclude = ('tags', )



class StorySimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Story
        fields = ('uuid', 'name', 'faceIcon', 'listIcon')





class TagsSerialzer(serializers.ModelSerializer):

    childTagsNum = serializers.SerializerMethodField()
    childTagList = serializers.SerializerMethodField()

    @staticmethod
    def get_childTagsNum(tag):
        return Tag.objects.filter(parent=tag, isDelete=False).count()

    @staticmethod
    def get_childTagList(tag):
        queryset = Tag.objects.filter(parent=tag)
        return TagsChildSerialzer(queryset, many=True).data

    class Meta:
        model = Tag
        fields = ('uuid', 'sortNum', 'name', 'icon', 'childTagList', 'childTagsNum')



class TagsChildSerialzer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('uuid', 'sortNum', 'name')


class TagsSimpleSerialzer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        exclude = ("parent", "isDelete", "isUsing")

class BgmSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Bgm
        fields = ('name', 'url', 'duration')


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('nickName', 'avatar', 'roles', 'uuid')


class UserDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        exclude = ('versionUuid', 'userID')


class UserSearchSerializer(serializers.ModelSerializer):


    class Meta:
        model = User
        fields = ('uuid', 'nickName', 'id')


class FreedomAudioStoryInfoSerializer(serializers.ModelSerializer):
    tagsInfo = serializers.SerializerMethodField()
    bgmInfo = serializers.SerializerMethodField()
    userInfo = serializers.SerializerMethodField()
    # storyInfo = serializers.SerializerMethodField()

    @staticmethod
    def get_tagsInfo(audioinfo):
        return TagsSimpleSerialzer(audioinfo.tags, many=True).data

    @staticmethod
    def get_bgmInfo(audioinfo):
        return BgmSimpleSerializer(audioinfo.bgm).data

    @staticmethod
    def get_userInfo(audioinfo):
        return UserSerializer(audioinfo.userUuid).data

    # @staticmethod
    # def get_storyInfo(audioinfo):
    #     return StorySerializer(audioinfo.storyUuid).data

    class Meta:
        model = AudioStory
        exclude = ('tags', 'storyUuid', 'albumUuid', 'userUuid', 'bgm')



class AudioStoryInfoSerializer(serializers.ModelSerializer):
    tagsInfo = serializers.SerializerMethodField()
    bgmInfo = serializers.SerializerMethodField()
    userInfo = serializers.SerializerMethodField()
    storyInfo = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    bgIcon = serializers.SerializerMethodField()

    @staticmethod
    def get_tagsInfo(audioinfo):
        return TagsSimpleSerialzer(audioinfo.tags, many=True).data

    @staticmethod
    def get_bgmInfo(audioinfo):
        return BgmSimpleSerializer(audioinfo.bgm).data

    @staticmethod
    def get_userInfo(audioinfo):
        return UserSerializer(audioinfo.userUuid).data

    @staticmethod
    def get_storyInfo(audioinfo):
        return StorySerializer(audioinfo.storyUuid).data

    @staticmethod
    def get_name(audioinfo):
        if audioinfo.audioStoryType == False:
            return audioinfo.name
        else:
            return audioinfo.storyUuid.name if audioinfo.storyUuid else None

    @staticmethod
    def get_bgIcon(audioinfo):
        if audioinfo.audioStoryType == False:
            return audioinfo.bgIcon
        else:
            return audioinfo.storyUuid.faceIcon if audioinfo.storyUuid else None

    class Meta:
        model = AudioStory
        exclude = ('tags', 'storyUuid', 'albumUuid', 'userUuid', 'bgm')



class AudioStoryDownloadSerializer(serializers.ModelSerializer):
    # tagsInfo = serializers.SerializerMethodField()
    bgmInfo = serializers.SerializerMethodField()
    userInfo = serializers.SerializerMethodField()
    # storyInfo = serializers.SerializerMethodField()

    # @staticmethod
    # def get_tagsInfo(audioinfo):
    #     return TagsSimpleSerialzer(audioinfo.tags, many=True).data

    @staticmethod
    def get_bgmInfo(audioinfo):
        return BgmSimpleSerializer(audioinfo.bgm).data

    @staticmethod
    def get_userInfo(audioinfo):
        return UserSerializer(audioinfo.userUuid).data

    # @staticmethod
    # def get_storyInfo(audioinfo):
    #     return StorySerializer(audioinfo.storyUuid).data

    class Meta:
        model = AudioStory
        exclude = ('name', 'bgIcon', 'tags', 'storyUuid', 'albumUuid', 'userUuid', 'bgm', 'isDelete')



class AudioStorySimpleSerializer(serializers.ModelSerializer):
    storyInfo = serializers.SerializerMethodField()
    nickName = serializers.SerializerMethodField()

    @staticmethod
    def get_storyInfo(audioinfo):
        return StorySimpleSerializer(audioinfo.storyUuid).data

    @staticmethod
    def get_nickName(audioinfo):
        return audioinfo.userUuid.nickName

    class Meta:
        model = AudioStory
        fields = ('name', 'storyInfo', 'audioStoryType', 'bgIcon', 'nickName', 'createTime')





class CheckAudioStoryInfoSerializer(serializers.ModelSerializer):
    tagsInfo = serializers.SerializerMethodField()
    bgmInfo = serializers.SerializerMethodField()
    userInfo = serializers.SerializerMethodField()
    storyInfo = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    bgIcon = serializers.SerializerMethodField()


    @staticmethod
    def get_tagsInfo(audioinfo):
        return TagsSimpleSerialzer(audioinfo.tags, many=True).data

    @staticmethod
    def get_bgmInfo(audioinfo):
        return BgmSimpleSerializer(audioinfo.bgm).data

    @staticmethod
    def get_userInfo(audioinfo):
        return UserSerializer(audioinfo.userUuid).data

    @staticmethod
    def get_storyInfo(audioinfo):
        return StorySerializer(audioinfo.storyUuid).data

    @staticmethod
    def get_name(audioinfo):
        if audioinfo.audioStoryType == False:
            return audioinfo.name
        else:
            return audioinfo.storyUuid.name if audioinfo.storyUuid else None

    @staticmethod
    def get_bgIcon(audioinfo):
        if audioinfo.audioStoryType == False:
            return audioinfo.bgIcon
        else:
            return audioinfo.storyUuid.faceIcon if audioinfo.storyUuid else None


    class Meta:
        model = AudioStory
        exclude = ('tags', 'storyUuid', 'albumUuid', 'userUuid', 'bgm')


class BgmSerializer(serializers.ModelSerializer):

    class Meta:
        model = Bgm
        fields = "__all__"


class HotSearchSerializer(serializers.ModelSerializer):

    class Meta:
        model = HotSearch
        fields = "__all__"


class AdSerializer(serializers.ModelSerializer):
    linkObjectInfo = serializers.SerializerMethodField()

    @staticmethod
    def get_linkObjectInfo(ad):
        linkObjectInfo = ""
        if ad.type == 0:  # 活动
            try:
                linkObjectInfo = Activity.objects.filter(uuid=ad.target).first().name
            except:
                raise ParamsException({'code': 400, 'msg': '参数错误'})
        elif ad.type == 1:  # 专辑
            pass
        elif ad.type == 2:  # 音频
            try:
                audioStory = AudioStory.objects.filter(uuid=ad.target).first()
                linkObjectInfo = audioStory.storyUuid.name if audioStory.audioStoryType else audioStory.name
            except:
                raise ParamsException({'code': 400, 'msg': '参数错误'})
        elif ad.type == 3:  # 商品
            pass
        elif ad.type == 4:
            linkObjectInfo = ad.target

        return linkObjectInfo

    class Meta:
        model = Ad
        exclude = ("isDelete", )



class ModuleSerializer(serializers.ModelSerializer):
    audioStory = serializers.SerializerMethodField()


    @staticmethod
    def get_audioStory(module):
        return AudioStorySimpleSerializer(module.audioUuid).data

    class Meta:
        model = Module
        exclude = ('audioUuid', 'id', 'createTime', 'updateTime', 'isDelete')


class GameInfoSerializer(serializers.ModelSerializer):
    # userInfo = serializers.SerializerMethodField()
    audioInfo = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()

    @staticmethod
    def get_score(gameInfo):
        return 0.75 * gameInfo.audioUuid.bauUuid.filter(type=1).count() + 0.25 * gameInfo.audioUuid.playTimes

    # @staticmethod
    # def get_userInfo(gameInfo):
    #     return UserSearchSerializer(gameInfo.userUuid).data

    @staticmethod
    def get_audioInfo(gameInfo):
        # return AudioStoryInfoSerializer(gameInfo.audioUuid).data
        return AudioStoryDownloadSerializer(gameInfo.audioUuid).data


    class Meta:
        model = GameInfo
        fields = ("createTime", "uuid", "audioUuid", "audioInfo", "score")


class ActivitySerializer(serializers.ModelSerializer):

    count = serializers.SerializerMethodField()
    # 返回当前活动处于哪个阶段 未开始，进行中，已结束
    stage = serializers.SerializerMethodField()

    @staticmethod
    def get_count(activity):
        return activity.activityRankUuid.count()

    @staticmethod
    def get_stage(activity):
        # currentTime = datetime.now()
        currentTime =timezone.now()

        if activity.endTime<currentTime:
            return "past"
        elif activity.startTime<=currentTime<=activity.endTime:
            return "now"
        elif currentTime<activity.startTime:
            return "future"


    class Meta:
        model = Activity
        fields = ("name", "startTime", "endTime", "count", "uuid", "id", "intro", "icon", "stage")




class CycleBannerSerializer(serializers.ModelSerializer):

    linkObjectInfo = serializers.SerializerMethodField()

    @staticmethod
    def get_linkObjectInfo(cycleBanner):
        linkObjectInfo = ""
        if cycleBanner.type == 0:   # 活动
            try:
                linkObjectInfo = Activity.objects.filter(uuid=cycleBanner.target).first().name
            except:
                raise ParamsException({'code': 400, 'msg': '参数错误'})
        elif cycleBanner.type == 1: # 专辑
            pass
        elif cycleBanner.type == 2: # 音频
            try:
                audioStory = AudioStory.objects.filter(uuid=cycleBanner.target).first()
                linkObjectInfo = audioStory.storyUuid.name if audioStory.audioStoryType else audioStory.name
            except:
                raise ParamsException({'code': 400, 'msg': '参数错误'})
        elif cycleBanner.type == 3: # 商品
            pass
        elif cycleBanner.type == 4:
            linkObjectInfo = cycleBanner.target

        return linkObjectInfo


    class Meta:
        model = CycleBanner
        exclude = ("location", "isDelete")



class FeedbackSerializer(serializers.ModelSerializer):

    userInfo = serializers.SerializerMethodField()

    @staticmethod
    def get_userInfo(feedback):
        return UserSearchSerializer(feedback.userUuid).data

    class Meta:
        model = Feedback
        exclude = ("userUuid", )







