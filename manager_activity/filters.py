import django_filters

from manager.models import Shop, Prize, UserPrize
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

    class Meta:
        model = Prize
        fields = ("name", "id", "status")


class UserPrizeFilter(django_filters.FilterSet):
    orderNum = django_filters.CharFilter(field_name="orderNum", lookup_expr="icontains")
    prizeName = django_filters.CharFilter(method='filter_by_prizename')

    @staticmethod
    def filter_by_prizename(queryset, name, value):
        return queryset.filter(prizeUuid__name__icontains=value)

    class Meta:
        model = UserPrize
        fields = ("orderNum", "id", "prizeName")

