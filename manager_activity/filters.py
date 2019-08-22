import django_filters

from manager.models import Shop, Prize


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