from datetime import datetime

import django_filters

from manager.models import Tag, Story, AudioStory, User, Bgm, HotSearch, GameInfo, Activity, CycleBanner, Ad, Feedback
from utils.errors import ParamsException


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
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = AudioStory
        fields = ('id', 'checkStatus', 'name')


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


class UserFilter(django_filters.FilterSet):

    nickName = django_filters.CharFilter(field_name='nickName', lookup_expr='icontains')
    tel = django_filters.CharFilter(lookup_expr='contains')
    city = django_filters.CharFilter(lookup_expr='contains')
    # status = django_filters.CharFilter(method='filter_by_status')
    #
    # @staticmethod
    # def filter_by_status(queryset, name, value):
    #     return queryset.filter(status=value)


    class Meta:
        model = User
        fields = ('id', 'nickName', 'tel', 'status', 'city')



class GameInfoFilter(django_filters.FilterSet):

    activityuuid = django_filters.CharFilter(method='filter_by_uuid')

    @staticmethod
    def filter_by_uuid(queryset, name, value):
        activity = Activity.objects.filter(uuid=value).first()
        if not activity:
            raise ParamsException({'code': 400, 'msg': '参数错误'})
        return queryset.filter(activityUuid=activity)

    class Meta:
        model = GameInfo
        fields = "__all__"


class ActivityFilter(django_filters.FilterSet):

    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    stage = django_filters.CharFilter(method='filter_by_stage')

    @staticmethod
    def filter_by_stage(queryset, name, value):
        currentTime = datetime.now()

        if value == "past":
            return queryset.filter(endTime__lt=currentTime)
        elif value == "now":
            return queryset.filter(startTime__lt=currentTime, endTime__gt=currentTime)
        elif value == "future":
            return queryset.filter(startTime__gt=currentTime)
        else:
            return queryset



    class Meta:
        model = Activity
        fields = "__all__"


class CycleBannerFilter(django_filters.FilterSet):

    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")


    class Meta:
        model = CycleBanner
        fields = ("name", )


class AdFilter(django_filters.FilterSet):

    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")


    class Meta:
        model = Ad
        fields = ("name", )



class FeedbackFilter(django_filters.FilterSet):
    id = django_filters.NumberFilter(method='filter_by_id')

    @staticmethod
    def filter_by_id(queryset, name, value):
        user = User.objects.filter(id=value).first()
        return queryset.filter(userUuid=user)

    class Meta:
        model = Feedback
        fields = ("type", "status")# 反馈问题类型 1产品建议 2功能异常 3其他问题







