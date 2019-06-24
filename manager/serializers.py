
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from manager.models import TemplateStory
from utils.errors import ParamsException


class TemplateStorySerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(min_value=8, error_messages={'min_value': 'id超过最小值'})

    class Meta:
        model = TemplateStory
        fields = ('id', 'uuid', 'title', 'createTime', 'recordNum', 'status')

    def validate(self, attrs):
        id = attrs.get('id', '')
        if id:
            if  isinstance(id, int):
                raise ParamsException({'code':400, 'msg': 'dd'})
                # raise ValidationError('ssss')
        return attrs

