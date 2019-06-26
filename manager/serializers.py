
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from common.common import get_uuid
from manager.models import TemplateStory, Works, Tag, User, Bgm
from utils.errors import ParamsException


class TemplateStorySerializer(serializers.ModelSerializer):

    class Meta:
        model = TemplateStory
        exclude = ('tags', )



class TemplateStoryDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = TemplateStory
        exclude = ('tags', 'uuid', 'id')


class TagsSimpleSerialzer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'tagName', 'code')


class UserSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('uuid', 'username', 'userLogo')



class BgmSimplesSerializer(serializers.ModelSerializer):

    class Meta:
        model = Bgm
        fields = ('name', 'mediaUrl', 'bgmTime', 'isUsing')


class TemplateWorksInfoSerializer(serializers.ModelSerializer):
    tags = serializers.SerializerMethodField()
    userInfo = serializers.SerializerMethodField()
    templateInfo = serializers.SerializerMethodField()
    bgmInfo = serializers.SerializerMethodField()

    def get_tags(self, works):
        return TagsSimpleSerialzer(works.tags, many=True).data

    def get_userInfo(self, works):
        return UserSimpleSerializer(works.userUuid).data

    def get_templateInfo(self, works):
        return TemplateStoryDetailSerializer(works.templateUuid).data

    def get_bgmInfo(self, works):
        return BgmSimplesSerializer(works.bgmUuid).data

    class Meta:
        model = Works
        exclude = ('userUuid', 'templateUuid', 'albumUuid',
                   'bgmUuid', 'bgUrl', 'title', 'worksType')


class FreedomWorksInfoSerializer(serializers.ModelSerializer):
    tags = serializers.SerializerMethodField()
    userInfo = serializers.SerializerMethodField()
    # templateInfo = serializers.SerializerMethodField()
    bgmInfo = serializers.SerializerMethodField()

    def get_tags(self, works):
        return TagsSimpleSerialzer(works.tags, many=True).data

    def get_userInfo(self, works):
        return UserSimpleSerializer(works.userUuid).data

    # def get_templateInfo(self, works):
    #     return TemplateStoryDetailSerializer(works.templateUuid).data

    def get_bgmInfo(self, works):
        return BgmSimplesSerializer(works.bgmUuid).data

    class Meta:
        model = Works
        exclude = ('userUuid', 'templateUuid', 'albumUuid',
                   'bgmUuid', 'worksType')


class CheckWorksInfoSerializer(serializers.ModelSerializer):
    tags = serializers.SerializerMethodField()
    userInfo = serializers.SerializerMethodField()
    templateInfo = serializers.SerializerMethodField()
    bgmInfo = serializers.SerializerMethodField()

    def get_tags(self, works):
        return TagsSimpleSerialzer(works.tags, many=True).data

    def get_userInfo(self, works):
        return UserSimpleSerializer(works.userUuid).data

    def get_templateInfo(self, works):
        return TemplateStoryDetailSerializer(works.templateUuid).data

    def get_bgmInfo(self, works):
        return BgmSimplesSerializer(works.bgmUuid).data

    class Meta:
        model = Works
        exclude = ('userUuid', 'templateUuid', 'albumUuid',
                   'bgmUuid')

class TypeTagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('tagName', 'sortNum')

