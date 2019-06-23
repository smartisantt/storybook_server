
import django_filters

from manager.models import TemplateStory


class TemplateStoryFilter(django_filters.rest_framework.FilterSet):
    """模板id，模板名，日期，"""
    id = django_filters.NumberFilter(field_name='id')
    title = django_filters.CharFilter('title', lookup_expr='contains')
    # starttime = django_filters.DateTimeFilter('createTime', lookup_expr='gte')
    # endtime = django_filters.DateTimeFilter('createTime', lookup_expr='lte')


    @staticmethod
    def filter_by_starttime(queryset, value):
        return queryset.filter(id=value)

    class Meta:
        model = TemplateStory
        fields = ('title', 'createTime')
