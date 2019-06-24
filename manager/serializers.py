
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from common.common import get_uuid
from manager.models import TemplateStory
from utils.errors import ParamsException


class TemplateStorySerializer(serializers.ModelSerializer):

    class Meta:
        model = TemplateStory
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
        validated_data['uuid'] = get_uuid()
        templteStory = TemplateStory.objects.create(**validated_data)
        return templteStory

    def update(self, instance, validated_data):
        if not validated_data['uuid']:
            raise ParamsException({'code': 200, 'msg': '参数错误'})
        return instance

    class Meta:
        model = TemplateStory
        exclude = ('tags', 'uuid', 'id')


