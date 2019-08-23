import json
import logging
from datetime import datetime

from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, mixins
from rest_framework.decorators import api_view, authentication_classes, throttle_classes
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from common.common import page_index, get_uuid
from common.expressage import Express100
from manager.auths import CustomAuthentication
from manager.filters import ActivityFilter
from manager.managerCommon import request_body, http_return, timestamp2datetime
from manager.models import Activity, GameInfo, ActivityConfig, Shop, Prize, UserPrize
from manager.paginations import MyPagination
from manager.serializers import ActivitySerializer
from manager_activity.filters import ShopFilter, PrizeFilter, UserPrizeFilter
from manager_activity.serializers import ShopSerializer, PrizeSerializer, UserPrizeSerializer
from utils.errors import ParamsException


class ActivityView(ListAPIView):
    queryset = Activity.objects.all().prefetch_related('activityRankUuid').order_by('-createTime')
    serializer_class = ActivitySerializer
    filter_class = ActivityFilter
    pagination_class = MyPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('-createTime',)
    ordering_fields = ('id', 'createTime')

    def get_queryset(self):
        startTimestamp = self.request.query_params.get('starttime', '')
        endTimestamp = self.request.query_params.get('endtime', '')

        if (startTimestamp and not endTimestamp) or (not startTimestamp and endTimestamp):
            raise ParamsException('时间错误')
        if startTimestamp and endTimestamp:
            try:
                starttime, endtime = timestamp2datetime(startTimestamp, endTimestamp, convert=False)
                return self.queryset.exclude(Q(startTime__gt=endtime) & Q(endTime__gt=endtime) |
                                             Q(endTime__lt=starttime) & Q(startTime__lt=starttime))
            except Exception as e:
                logging.error(str(e))
                raise ParamsException(e.detail)

        return self.queryset


@api_view(['POST'])
@authentication_classes((CustomAuthentication, ))
def create_activity(request):
    # 创建活动
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    name = data.get('name', '')
    intro = data.get('intro', '')
    startTime = data.get('starttime', '')
    endTime = data.get('endtime', '')
    url = data.get('url', '')
    icon = data.get('icon', '')         # 非必填
    if not all([url, name, intro, startTime, endTime]):
        return http_return(400, '参数错误')
    if Activity.objects.filter(name=name).exists():
        return http_return(400, '重复活动名')

    if startTime > endTime:
        return http_return(400, '时间错误')

    if not all([isinstance(startTime, int), isinstance(endTime, int)]):
        return http_return(400, '时间错误')

    if not isinstance(url, str):
        return http_return(400, 'url错误')

    if not url.startswith('http'):
        return http_return('url格式错误')

    startTime = startTime/1000
    endTime = endTime/1000

    try:
        startTime = datetime.fromtimestamp(startTime)
        endTime = datetime.fromtimestamp(endTime)
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '时间参数错误')

    try:
        with transaction.atomic():
            uuid = get_uuid()
            Activity.objects.create(
                uuid=uuid,
                name=name,
                url=url,
                startTime=startTime,
                endTime=endTime,
                intro=intro,
                icon=icon,
                status="normal"
            )
            return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '创建失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication, ))
def modify_activity(request):
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    uuid = data.get('uuid', '')
    name = data.get('name', '')
    intro = data.get('intro', '')
    icon = data.get('icon', '') # 没有icon
    startTime = data.get('starttime', '')
    endTime = data.get('endtime', '')
    url = data.get('url', '')
    if not all([uuid, name, intro, startTime, endTime, url]):
        return http_return(400, '参数错误')
    activity = Activity.objects.filter(uuid=uuid).first()
    if not activity:
        return http_return(400, '没有对象')
    myName = activity.name
    if myName != name:
        if Activity.objects.filter(name=name).exists():
            return http_return(400, '重复活动名')

    if not all([isinstance(startTime, int), isinstance(endTime, int)]):
        return http_return(400, '时间错误')

    if startTime > endTime:
        return http_return(400, '时间错误')

    if not url.startswith('http'):
        return http_return('url格式错误')

    startTime = startTime/1000
    endTime = endTime/1000
    try:
        startTime = datetime.fromtimestamp(startTime)
        endTime = datetime.fromtimestamp(endTime)
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '时间错误')

    activity = Activity.objects.filter(uuid=uuid).first()
    try:
        with transaction.atomic():
            activity.name = name
            activity.startTime = startTime
            activity.endTime = endTime
            activity.icon = icon
            activity.intro = intro
            activity.url = url
            activity.save()
            return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '修改失败')


@api_view(['GET'])
@authentication_classes((CustomAuthentication, ))
def activity_rank(request):
    """活动排行"""
    data = request_body(request)
    if not data:
        return http_return(400, '参数错误')
    activityUuid = data.get('activityuuid', '')
    page = data.get('page', '')
    page_size = data.get('page_size', '')
    if not activityUuid:
        return http_return(400, '参数错误')
    act = Activity.objects.filter(uuid=activityUuid).first()
    if not act:
        return http_return(400, '活动信息不存在')
    config = ActivityConfig.objects.filter(status=0).first()
    if not config:
        return http_return(400, '未获取到参数配置')
    praiseNum = config.praiseNum / 100
    playTimesNum = config.playTimesNum / 100
    games = GameInfo.objects.filter(activityUuid__uuid=activityUuid).all()
    games = sorted(games,
                   key=lambda x: praiseNum * x.audioUuid.bauUuid.filter(
                       type=1).count() + playTimesNum * x.audioUuid.playTimes,
                   reverse=True)
    total, games = page_index(games, page, page_size)
    activityRankList = []
    for index,game in enumerate(games):
        name = game.audioUuid.name
        if game.audioUuid.audioStoryType:
            name = game.audioUuid.storyUuid.name
        activityRankList.append({
            "rank": index+1+(int(page)-1)*int(page_size) if page else index+1,
            "publisher": {
                "uuid": game.userUuid.uuid or '',
                "nickname": game.userUuid.nickName or '',
                "avatar": game.userUuid.avatar or '',
                "tel": game.userUuid.tel or '',
            },
            "audio": {
                "id": game.audioUuid.id or '',
                "uuid": game.audioUuid.uuid or '',
                "bgmUrl":  game.audioUuid.bgm.url if game.audioUuid.bgm else '',
                "voiceUrl": game.audioUuid.voiceUrl or '',
                "name": name or '',
            },
            "score": praiseNum * game.audioUuid.bauUuid.filter(type=1).count() + playTimesNum * game.audioUuid.playTimes,
        })
    return http_return(200, '成功', {"total": total, "activityRankList": activityRankList})


# 查询快递
@api_view(['GET'])
@authentication_classes((CustomAuthentication, ))
@cache_page(60*10)
def query_expressage(request):
    data = request_body(request, 'GET')
    if not data:
        return http_return(400, '快递单号不能为空')
    num = data.get('num', '')
    if not num:
        return http_return(400, '快递单号不能为空')
    userPrize = UserPrize.objects.filter(deliveryNum=num).first()
    if not userPrize:
        return http_return(400, "用户发货管理没有此快递单号！")

    # 超过30天无法获取物流的详细信息
    if not userPrize.expressDate:
        if (timezone.now() - userPrize.expressDate).days > 30:
            return Response({"info": "暂无详细信息", "state": userPrize.expressState})

    if userPrize.expressState == 3:
        return Response({"info": json.loads(userPrize.expressDetail), "state": userPrize.expressState})

    res = Express100.get_express_info(str(num).strip())
    if not res:
        return http_return(400, "查询无结果，请检查单号是否正确或隔断时间再查！")
    res = json.loads(res.text)
    info = res.get("data", "")
    state = res.get("state", "")

    if not info:
        return http_return(400, "查询无结果，请检查单号是否正确或隔断时间再查！")

    # 如快递状态有更新，则更新显示
    if state and userPrize.expressState != state:
        userPrize.expressState = state

    userPrize.expressDetail = json.dumps(info)
    userPrize.save()
    return Response({"info": info, "state": state})


class ShopView(ListAPIView):
    queryset = Shop.objects.filter(isDelete=False)
    serializer_class = ShopSerializer
    filter_class = ShopFilter
    pagination_class = MyPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('-createTime',)
    ordering_fields = ('id', 'createTime')


@api_view(['POST'])
@authentication_classes((CustomAuthentication, ))
def add_shop_info(request):
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    shopList = data.get('shopList', '')

    if not isinstance(shopList, list):
        return http_return(400, "数据格式错误")

    if not shopList:
        return http_return(400, "店主信息为空！")

    # 校验用户信息， 重复， 缺少信息， 格式错误，

    try:
        with transaction.atomic():
            querysetlist = []
            for shop in shopList:
                querysetlist.append(Shop(
                    uuid=get_uuid(),
                    owner=shop["owner"],
                    tel=shop["tel"],
                    shopNo=shop["shopNo"],
                    shopName=shop["shopName"],
                    isDelete=False
                ))
            Shop.objects.bulk_create(querysetlist)
        return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '添加失败')


class PrizeView(ListAPIView):
    queryset = Prize.objects.filter(isDelete=False)
    serializer_class = PrizeSerializer
    filter_class = PrizeFilter
    pagination_class = MyPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('-createTime',)
    ordering_fields = ('id', 'createTime')

    def get_queryset(self):
        startTimestamp = self.request.query_params.get('starttime', '')
        endTimestamp = self.request.query_params.get('endtime', '')

        if (startTimestamp and not endTimestamp) or  (not startTimestamp and endTimestamp):
            raise ParamsException('时间错误')
        if startTimestamp and endTimestamp:
            try:
                starttime, endtime = timestamp2datetime(startTimestamp, endTimestamp, convert=False)
                return self.queryset.filter(createTime__range=(starttime, endtime))
            except Exception as e:
                logging.error(str(e))
                raise ParamsException(e.detail)

        return self.queryset


@api_view(['POST'])
@authentication_classes((CustomAuthentication, ))
def add_prize(request):
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    type = data.get('type', '')
    card_type = data.get('card_type', '')
    inventory = data.get('inventory', '')
    icon = data.get('icon', '')
    name = data.get('name', '')
    probability = data.get('probability', '')

    if not all([name, icon, type in [1, 2]]):
        return http_return(400, "参数有误")

    if type == 1:
        if card_type not in range(1,5):
            return http_return(400, "课程卡参数错误")

    if not isinstance(inventory, int):
        return http_return(400, "库存数量格式错误")

    if not inventory >= 0:
        return http_return(400, "库存数量应大于等于0")

    if not (isinstance(probability, float) or (isinstance(probability, int))):
        return http_return(400, "概率格式错误")

    if not 0 <= probability <= 1:
        return http_return(400, "概率在0到1之间")

    if Prize.objects.filter(name=name, isDelete=False).exists():
        return http_return(400, "重复名字")

    total = Prize.objects.filter(isDelete=False, status=1).aggregate(nums=Sum('probability'))['nums']
    if total:
        if probability + total > 1:
            temp = 1 - total
            return http_return(400, "当前启用奖品概率之和已经大于1，建议当前取值小于等于{:.10}".format(temp))

    try:
        with transaction.atomic():
            uuid = get_uuid()
            Prize.objects.create(
                uuid=uuid,
                icon=icon,
                type=type,
                inventory=inventory,
                probability=probability,
                card_type=card_type,
                name=name
            )
        return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '添加失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication, ))
def modify_prize(request):
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    prizeUuid = data.get('prizeUuid', '')
    type = data.get('type', '')
    card_type = data.get('card_type', '')
    inventory = data.get('inventory', '')
    icon = data.get('icon', '')
    name = data.get('name', '')
    probability = data.get('probability', '')

    if not all([prizeUuid, name, icon, type in [1, 2]]):
        return http_return(400, "参数有误")

    if type == 1:
        if card_type not in range(1,5):
            return http_return(400, "课程卡参数错误")

    if not isinstance(inventory, int):
        return http_return(400, "库存数量格式错误")

    if not inventory >= 0:
        return http_return(400, "库存数量应大于等于0")

    if not (isinstance(probability, float) or (isinstance(probability, int))):
        return http_return(400, "概率格式错误")

    if not 0 <= probability <= 1:
        return http_return(400, "概率在0到1之间")

    prize = Prize.objects.filter(uuid = prizeUuid, isDelete=False).first()
    if not prize:
        return http_return(400, "无奖品对象")

    total = Prize.objects.filter(isDelete=False, status=1).\
        exclude(uuid = prizeUuid).aggregate(nums=Sum('probability'))['nums']
    if total:
        if probability + total > 1:
            temp = 1- total
            return http_return(400, "当前启用奖品概率之和已经大于1，建议当前取值小于等于{:.10}".format(temp))

    if Prize.objects.filter(name=name, isDelete=False).exclude(uuid = prizeUuid).exists():
        return http_return(400, "重复名字")


    try:
        with transaction.atomic():
            prize.type=type
            prize.inventory=inventory
            prize.icon=icon
            prize.name=name
            prize.probability=probability
            prize.card_type=card_type
            prize.save()
        return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '修改失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication, ))
def forbid_prize(request):
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    prizeUuid = data.get('prizeUuid', '')
    if not prizeUuid:
        return http_return(400, "参数有误")

    prize = Prize.objects.filter(uuid=prizeUuid, isDelete=False).first()
    if not prize:
        return http_return(400, "没有对象")
    try:
        with transaction.atomic():
            prize.status = not(prize.status)
            prize.save()
        return http_return(200, {"status": prize.status})
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '停用恢复失败')


@api_view(['POST'])
@authentication_classes((CustomAuthentication, ))
def del_prize(request):
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    prizeUuid = data.get('prizeUuid', '')
    if not prizeUuid:
        return http_return(400, '参数错误')

    prize = Prize.objects.filter(uuid=prizeUuid, isDelete=False).first()
    if not prize:
        return http_return(400, "没有对象")

    try:
        with transaction.atomic():
            prize.isDelete = True
            prize.save()
        return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '删除失败')


class UserPrizeView(ListAPIView):
    queryset = UserPrize.objects.filter(prizeUuid__type=2) # 只显示实物奖品
    serializer_class = UserPrizeSerializer
    filter_class = UserPrizeFilter
    pagination_class = MyPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('-createTime',)
    ordering_fields = ('id', 'createTime')

    def get_queryset(self):
        startTimestamp = self.request.query_params.get('starttime', '')
        endTimestamp = self.request.query_params.get('endtime', '')

        if (startTimestamp and not endTimestamp) or  (not startTimestamp and endTimestamp):
            raise ParamsException('时间错误')
        if startTimestamp and endTimestamp:
            try:
                starttime, endtime = timestamp2datetime(startTimestamp, endTimestamp, convert=False)
                return self.queryset.filter(createTime__range=(starttime, endtime))
            except Exception as e:
                logging.error(str(e))
                raise ParamsException(e.detail)

        return self.queryset


#
@api_view(['POST'])
@authentication_classes((CustomAuthentication, ))
def add_user_prize(request):
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '参数错误')
    userPrizeUuid = data.get('userPrizeUuid', '')
    deliveryNum = data.get('deliveryNum', '')

    if not all([userPrizeUuid, deliveryNum]):
        return http_return(400, '参数错误')

    userPrize = UserPrize.objects.filter(uuid=userPrizeUuid).first()
    if not userPrize:
        return http_return(400, "没有对象")

    try:
        with transaction.atomic():
            userPrize.deliveryNum = deliveryNum
            userPrize.expressDate = timezone.now()
            userPrize.save()
        return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '添加运单号失败')