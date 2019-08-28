from django.db.models import Count
from rest_framework import serializers

from common.common import get_uuid
from manager.models import Shop, Prize, UserPrize, ReceivingInfo, User, GameInfo, Activity
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


class UserInvitationSerializer(serializers.ModelSerializer):
    regitsterNum = serializers.SerializerMethodField()
    activityNum = serializers.SerializerMethodField()

    @staticmethod
    def get_regitsterNum(user):
        res = User.objects.filter(inviter=user.uuid).count()
        return res

    @staticmethod
    def get_activityNum(user):
        res = GameInfo.objects.filter(inviter=user.uuid).count()
        return res

    class Meta:
        model = User
        fields = ("uuid", "id", "tel", "nickName", "createTime", "regitsterNum", "activityNum", "avatar")


class UserInvitationDetailSerializer(serializers.ModelSerializer):
    # 是否参加活动
    isActivity = serializers.SerializerMethodField()

    @staticmethod
    def get_isActivity(inviter):
        if GameInfo.objects.filter(userUuid=inviter).exists():
            return True
        return False

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['sortNum'] = list(self.instance).index(instance) + 1
        return data

    class Meta:
        model = User
        fields = ("uuid", "id", "tel", "nickName", "status", "createTime", "isActivity")



class ShopInvitationDetailSerializer(serializers.ModelSerializer):
    # 是否参加活动
    isActivity = serializers.SerializerMethodField()

    @staticmethod
    def get_isActivity(inviter):
        if GameInfo.objects.filter(userUuid=inviter).exists():
            return True
        return False

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['sortNum'] = list(self.instance).index(instance) + 1
        return data

    class Meta:
        model = User
        fields = ("uuid", "id", "tel", "nickName", "status", "createTime", "isActivity")


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
        fields = ("uuid", "orderNum", "prizeName", "nickName", "receiveInfo",
                  "createTime", "deliveryNum", "expressState", "com")


class ShopInvitationSerializer(serializers.ModelSerializer):
    regitsterNum = serializers.SerializerMethodField()
    activityNum = serializers.SerializerMethodField()

    @staticmethod
    def get_regitsterNum(shop):
        res = User.objects.filter(inviter=shop.uuid).count()
        return res

    @staticmethod
    def get_activityNum(shop):
        res = GameInfo.objects.filter(inviter=shop.uuid).count()
        return res

    class Meta:
        model = Shop
        fields = ("uuid", "owner", "tel", "shopNo", "shopName", "regitsterNum", "activityNum")


class ActivitySelectSerializer(serializers.ModelSerializer):

    class Meta:
        model = Activity
        fields = ("uuid", "name")
