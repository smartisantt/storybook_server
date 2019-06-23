
from rest_framework import serializers
from manager.models import TemplateStory


class TemplateStorySerializer(serializers.ModelSerializer):

    class Meta:
        model = TemplateStory
        fields = ('id', 'uuid', 'title', 'createTime', 'recordNum', 'status')
