from rest_framework import serializers

from common.common import get_uuid
from manager.models import Shop, Prize, UserPrize, ReceivingInfo
from utils.errors import ParamsException


class ShopSerializer(serializers.ModelSerializer):

    class Meta:
        model = Shop
        exclude = ("id", )


class PrizeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Prize
        fields = "__all__"


class ReceivingInfoBasicSerializer(serializers.ModelSerializer):

    class Meta:
        model = ReceivingInfo
        fields = ("tel", "address", "contact")


class UserPrizeSerializer(serializers.ModelSerializer):
    receiveInfo = serializers.SerializerMethodField()
    nickName = serializers.SerializerMethodField()
    prizeName = serializers.SerializerMethodField()

    @staticmethod
    def get_receiveInfo(userPrize):
        return ReceivingInfoBasicSerializer(userPrize.receiveUuid).data

    @staticmethod
    def get_nickName(userPrize):
        return userPrize.userUuid.nickName

    @staticmethod
    def get_prizeName(userPrize):
        return userPrize.prizeUuid.name

    class Meta:
        model = UserPrize
        fields = ("orderNum", "prizeName", "nickName", "receiveInfo", "createTime", "deliveryNum")



