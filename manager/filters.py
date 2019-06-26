
import django_filters

from manager.models import TemplateStory, Works, Tag


class TemplateStoryFilter(django_filters.rest_framework.FilterSet):
    """模板id，模板名，日期，"""
    title = django_filters.CharFilter('title', lookup_expr='contains')

    class Meta:
        model = TemplateStory
        fields = ('id', 'title')


class TemplateWorksInfoFilter(django_filters.rest_framework.FilterSet):
    recordtype = django_filters.NumberFilter(field_name='recordType')

    class Meta:
        model = Works
        fields = ('id', 'recordType', )


class FreedomWorksInfoFilter(django_filters.rest_framework.FilterSet):
    recordtype = django_filters.NumberFilter(field_name='recordType')
    title = django_filters.CharFilter(field_name='title', lookup_expr='icontains')

    class Meta:
        model = Works
        fields = ('id', 'recordType', 'title')


class CheckWorksInfoFilter(django_filters.rest_framework.FilterSet):

    checkstatus = django_filters.CharFilter(field_name='checkStatus')


    class Meta:
        model = Works
        fields = ('id', 'checkStatus')
