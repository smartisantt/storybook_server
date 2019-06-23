
import django_filters

from manager.models import TemplateStory


class TemplateStoryFilterSet(django_filters.FilterSet):
    """模板id，模板名，日期，"""
    id = django_filters.NumberFilter(field_name='id')
    starttime = django_filters.NumberFilter(field_name='createTime', lookup_expr='gte')
    endtime = django_filters.NumberFilter(field_name='createTime', lookup_expr='lte')



    @staticmethod
    def filer_by_id(queryset, value):
        return queryset.filter(id=value)

    class Meta:
        model = TemplateStory
        fields = ('title', 'createTime')
