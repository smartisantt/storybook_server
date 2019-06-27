
import django_filters

from manager.models import Tag, Story, AudioStory, User, Bgm, HotSearch


class StoryFilter(django_filters.FilterSet):
    """模板id，模板名，日期，"""
    name = django_filters.CharFilter('name', lookup_expr='contains')

    class Meta:
        model = Story
        fields = ('id', 'name')


class TemplateWorksInfoFilter(django_filters.FilterSet):
    recordtype = django_filters.NumberFilter(field_name='type')

    class Meta:
        model = AudioStory
        fields = ('id', 'type', )


class FreedomWorksInfoFilter(django_filters.FilterSet):
    recordtype = django_filters.NumberFilter(field_name='type')
    title = django_filters.CharFilter(field_name='title', lookup_expr='icontains')

    class Meta:
        model = AudioStory
        fields = ('id', 'type', 'title')


class FreedomAudioStoryInfoFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = AudioStory
        fields = ('id', 'type', 'name')


class AudioStoryInfoFilter(django_filters.FilterSet):

    class Meta:
        model = AudioStory
        fields = ('id', 'type')


class UserSearchFilter(django_filters.FilterSet):
    nickname = django_filters.CharFilter(field_name='nickName', lookup_expr='icontains')

    class Meta:
        model = User
        fields = ('uuid', 'nickName')




class CheckAudioStoryInfoFilter(django_filters.FilterSet):
    # 审核状态 unCheck待审核 check审核通过 checkFail审核不通过 exemption(后台上传的免审核）
    checkstatus = django_filters.CharFilter(field_name='checkStatus')

    class Meta:
        model = AudioStory
        fields = ('id', 'checkStatus')


class BgmFilter(django_filters.FilterSet):

    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = Bgm
        fields = ('name', 'status')


class HotSearchFilter(django_filters.FilterSet):

    keyword = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = HotSearch
        fields = ('keyword',)







