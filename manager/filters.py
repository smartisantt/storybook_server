
import django_filters

from manager.models import Tag, Story, AudioStory


class StoryFilter(django_filters.rest_framework.FilterSet):
    """模板id，模板名，日期，"""
    name = django_filters.CharFilter('name', lookup_expr='contains')

    class Meta:
        model = Story
        fields = ('id', 'name')


class TemplateWorksInfoFilter(django_filters.rest_framework.FilterSet):
    recordtype = django_filters.NumberFilter(field_name='type')

    class Meta:
        model = AudioStory
        fields = ('id', 'type', )


class FreedomWorksInfoFilter(django_filters.rest_framework.FilterSet):
    recordtype = django_filters.NumberFilter(field_name='type')
    title = django_filters.CharFilter(field_name='title', lookup_expr='icontains')

    class Meta:
        model = AudioStory
        fields = ('id', 'type', 'title')


class CheckWorksInfoFilter(django_filters.rest_framework.FilterSet):

    checkstatus = django_filters.CharFilter(field_name='checkStatus')


    class Meta:
        model = AudioStory
        fields = ('id', 'checkStatus')


class FreedomAudioStoryInfoFilter(django_filters.rest_framework.FilterSet):
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = AudioStory
        fields = ('id', 'type', 'name')

class AudioStoryInfoFilter(django_filters.rest_framework.FilterSet):

    class Meta:
        model = AudioStory
        fields = ('id', 'type')



class CheckAudioStoryInfoFilter(django_filters.rest_framework.FilterSet):
    pass


