import django_filters

from manager.models import Shop, Prize, UserPrize, User
from utils.errors import ParamsException


class ShopFilter(django_filters.FilterSet):
    owner = django_filters.CharFilter(field_name="owner", lookup_expr="icontains")
    tel = django_filters.CharFilter(field_name="tel", lookup_expr="icontains")
    shopNo = django_filters.CharFilter(field_name="shopNo", lookup_expr="icontains")
    shopName = django_filters.CharFilter(field_name="shopName", lookup_expr="icontains")

    class Meta:
        model = Shop
        fields = ("owner", "tel", "shopNo", "shopName")


class PrizeFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    activityUuid = django_filters.CharFilter(method='filter_by_activity')

    @staticmethod
    def filter_by_activity(queryset, name, value):
        return queryset.filter(activityUuid__uuid=value)

    class Meta:
        model = Prize
        fields = ("name", "id", "status", "activityUuid")


class UserPrizeFilter(django_filters.FilterSet):
    orderNum = django_filters.CharFilter(field_name="orderNum", lookup_expr="icontains")
    prizeName = django_filters.CharFilter(method='filter_by_prizename')
    tel = django_filters.CharFilter(method='filter_by_tel')
    area = django_filters.CharFilter(method='filter_by_area')
    nickName = django_filters.CharFilter(method='filter_by_nickname')

    @staticmethod
    def filter_by_prizename(queryset, name, value):
        return queryset.filter(prizeUuid__name__icontains=value)

    @staticmethod
    def filter_by_tel(queryset, name, value):
        return queryset.filter(receiveUuid__tel__icontains=value)

    @staticmethod
    def filter_by_area(queryset, name, value):
        value = value.replace('/', ',')
        return queryset.filter(receiveUuid__area__icontains=value)

    @staticmethod
    def filter_by_nickname(queryset, name, value):
        return queryset.filter(userUuid__nickName__icontains=value)

    class Meta:
        model = UserPrize
        fields = ("orderNum", "expressState")


class UserInvitationFilter(django_filters.FilterSet):
    nickName = django_filters.CharFilter(field_name="nickName", lookup_expr="icontains")
    tel = django_filters.CharFilter(field_name="tel", lookup_expr="icontains")

    class Meta:
        model = User
        fields = ("id", )


class ShopInvitationFilter(django_filters.FilterSet):
    owner = django_filters.CharFilter(field_name="owner", lookup_expr="icontains")
    shopNo = django_filters.CharFilter(field_name="shopNo", lookup_expr="icontains")
    tel = django_filters.CharFilter(field_name="tel", lookup_expr="icontains")
    shopName = django_filters.CharFilter(field_name="shopName", lookup_expr="icontains")
    activityUuid = django_filters.CharFilter(method='filter_by_activity')

    @staticmethod
    def filter_by_activity(queryset, name, value):
        return queryset.filter(activityUuid__uuid=value)

    class Meta:
        model = Shop
        fields = ("owner", "shopNo", "activityUuid")


