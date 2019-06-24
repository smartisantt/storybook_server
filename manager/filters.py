
import django_filters

from manager.models import TemplateStory


class TemplateStoryFilter(django_filters.rest_framework.FilterSet):
    """模板id，模板名，日期，"""
    title = django_filters.CharFilter('title', lookup_expr='contains')



    class Meta:
        model = TemplateStory
        fields = ('id', 'title')
