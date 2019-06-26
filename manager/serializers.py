
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from common.common import get_uuid
from manager.models import Story, AudioStory, Tag
from utils.errors import ParamsException


class TemplateStorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Story
        exclude = ('tags', )

    def validate(self, attrs):
        id = attrs.get('id', '')
        if id:
            if  isinstance(id, int):
                raise ParamsException({'code':400, 'msg': 'dd'})
                # raise ValidationError('ssss')
        return attrs


class TemplateStoryDetailSerializer(serializers.ModelSerializer):

    uuid = ''
    def validate(self, attrs):
        return attrs

    def create(self, validated_data):
        """创建"""
        validated_data['uuid'] = get_uuid()
        templteStory = Story.objects.create(**validated_data)
        return templteStory

    def update(self, instance, validated_data):
        """更新"""
        if not validated_data['uuid']:
            raise ParamsException({'code': 200, 'msg': '参数错误'})
        # 在数据库中查找是否有此对象
        #
        return instance

    class Meta:
        model = Story
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

