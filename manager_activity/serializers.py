from rest_framework import serializers

from common.common import get_uuid
from manager.models import Shop, Prize
from utils.errors import ParamsException


class ShopSerializer(serializers.ModelSerializer):

    class Meta:
        model = Shop
        exclude = ("id", )


class PrizeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Prize
        fields = "__all__"


# class PrizePostSerializer(serializers.Serializer):
#     name = serializers.CharField(min_length=2, max_length=32, required=True,
#                                  error_messages={
#                                      'min_length': '奖品名字不要小于2个字',
#                                      'max_length': '奖品名字不要大于32个字',
#                                      'required': '奖品名字必填'
#                                  })
#
#     icon = serializers.CharField(required=True,
#                                  error_messages={
#                                      'required': '缺少奖品图片'
#                                  })
#
#     inventory = serializers.IntegerField(required=True,
#                                          error_messages={
#                                              'required': '缺少奖品库存'
#                                          })
#
#     probability = serializers.FloatField(required=True,
#                                          error_messages={
#                                              'required': '缺少奖品概率'
#                                          })
#     type_choices = (
#         (0, "好呗呗课程卡"),
#         (1, "实物商品"),
#     )# 0 好呗呗课程卡 1 实物商品
#
#     type = serializers.ChoiceField(choices=type_choices, required=True,
#                                    error_messages={
#                                      'required': '缺少奖品类型'
#                                    })
#
#     def validate(self, attrs):
#         # 逻辑校验
#         if Prize.objects.filter(name=attrs['name'], isDelete=False).exists():
#             raise ParamsException({'code': 400, 'msg': '奖品名重复'})
#         return attrs
#
#     def create_prize(self, validated_data):
#         validated_data['uuid'] = get_uuid()
#         prize = Prize.objects.create(**validated_data)
#         return True
#
#     class Meta:
#         model = Prize
#         fields = "__all__"

