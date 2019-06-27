
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from common.common import get_uuid
from manager.models import Tag, User, Bgm, AudioStory, Story, HotSearch
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
        fields = ('uuid', 'name')




class TemplateStory(object):
    pass


class TemplateStoryDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = TemplateStory
        exclude = ('tags', 'uuid', 'id')


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


class UserSearchSerializer(serializers.ModelSerializer):


    class Meta:
        model = User
        fields = ('uuid', 'nickName')


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

    class Meta:
        model = AudioStory
        exclude = ('name', 'bgIcon', 'tags', 'storyUuid', 'albumUuid', 'userUuid', 'bgm')



class CheckAudioStoryInfoSerializer(serializers.ModelSerializer):
    tagsInfo = serializers.SerializerMethodField()
    bgmInfo = serializers.SerializerMethodField()
    userInfo = serializers.SerializerMethodField()
    storyInfo = serializers.SerializerMethodField()

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




