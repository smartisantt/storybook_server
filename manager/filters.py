
import django_filters

from manager.models import TemplateStory, Works, Tag


class TemplateStoryFilter(django_filters.rest_framework.FilterSet):
    """模板id，模板名，日期，"""
    title = django_filters.CharFilter('title', lookup_expr='contains')

    class Meta:
        model = TemplateStory
        fields = ('id', 'title')


class WorksInfoFilter(django_filters.rest_framework.FilterSet):
    """"""
    typetag = django_filters.CharFilter(method='filter_by_tag')

    @staticmethod
    def filter_by_tag(queryset, name, value):
        return queryset.filter(

        )

    class Meta:
        model = Works
        fields = ('id', 'recordType', )
