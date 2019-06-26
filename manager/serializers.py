
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from common.common import get_uuid
from manager.models import Tag, User, Bgm, AudioStory, Story
from utils.errors import ParamsException


class TemplateStory(object):
    pass


class StorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Story
        exclude = ('tags', )


class TemplateStory(object):
    pass


class TemplateStoryDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = TemplateStory
        exclude = ('tags', 'uuid', 'id')


class TagsSimpleSerialzer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'tagName', 'code')


class WorksInfoSerializer(serializers.ModelSerializer):
    tags = serializers.SerializerMethodField()

    def get_tags(self, work):
        return TagsSimpleSerialzer(work.tags, many=True).data

    class Meta:
        model = AudioStory
        exclude = ('id', )


class FreedomAudioStoryInfoSerializer(serializers.ModelSerializer):
    pass


class AudioStoryInfoSerializer(serializers.ModelSerializer):
    pass



class CheckAudioStoryInfoSerializer(serializers.ModelSerializer):
    pass

