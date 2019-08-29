import json
import logging
from datetime import datetime
from functools import reduce

from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, mixins
from rest_framework.decorators import api_view, authentication_classes, throttle_classes, action
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from common.common import page_index, get_uuid
from common.expressage import Express100
from manager.auths import CustomAuthentication
from manager.filters import ActivityFilter
from manager.managerCommon import request_body, http_return, timestamp2datetime
from manager.models import Activity, GameInfo, ActivityConfig, Shop, Prize, UserPrize, User
from manager.paginations import MyPagination
from manager.serializers import ActivitySerializer
from manager_activity.filters import ShopFilter, PrizeFilter, UserPrizeFilter, UserInvitationFilter, \
    ShopInvitationFilter
from manager_activity.serializers import ShopSerializer, PrizeSerializer, UserPrizeSerializer, UserInvitationSerializer, \
    ShopInvitationSerializer, UserInvitationDetailSerializer, ShopInvitationDetailSerializer, ActivitySelectSerializer
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
    # isParticipationPrize = data.get('isParticipationPrize', '')
    # offeringPrizeType = data.get('offeringPrizeType', '')   # 没有奖品，此项为空
    # isBrokerage = data.get('isBrokerage', '')
    icon = data.get('icon', '')         # 非必填
    if not all([url, name, intro, startTime, endTime]):
        return http_return(400, '参数错误')

    # if not all([isParticipationPrize in [1, 2], isBrokerage in [1, 2]]):
    #     return http_return(400, '活动参数错误')
    #
    # # 有奖品则有发奖形式
    # if isParticipationPrize == 2:
    #     if not offeringPrizeType in [1, 2]:
    #         return http_return(400, '发放奖品参数错误')

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
                # isParticipationPrize=isParticipationPrize,
                # offeringPrizeType=offeringPrizeType,
                # isBrokerage=isBrokerage,
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

    games = GameInfo.objects.filter(activityUuid__uuid=activityUuid).all()
    games = sorted(games, key=lambda x: x.votes, reverse=True)
    total, games = page_index(games, page, page_size)
    activityRankList = []
    for index,game in enumerate(games):
        if not game.audioUuid:
            continue
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
            "score": game.votes,
        })
    return http_return(200, '成功', {"total": total, "activityRankList": activityRankList})

com_dict = {
    "yunda": "韵达快递",
    "youzhengguonei": "邮政快递包裹",
    "zhongtong": "中通快递",
    "shunfeng": "顺丰速运",
    "shentong": "申通快递",
    "yuantong": "圆通速递",
    "huitongkuaidi": "百世快递",
    "yundakuaiyun": "韵达快运",
    "danniao": "丹鸟",
    "zhongtongkuaiyun": "中通快运",
    "ems": "EMS",
}

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

    # 超过30的单号直接读取数据库历史记录
    if userPrize.expressDate:
        if (timezone.now() - userPrize.expressDate).days > 30:
            return Response({"info": json.loads(userPrize.expressDetail), "state": userPrize.expressState, "com": userPrize.com})

    if userPrize.expressState == 3:
        return Response({"info": json.loads(userPrize.expressDetail), "state": userPrize.expressState, "com": userPrize.com})

    res = Express100.get_express_info(str(num).strip())
    if not res:
        return http_return(400, "查询无结果，请隔断时间再查！")
    res = json.loads(res.text)
    info = res.get("data", "")
    state = res.get("state", "")
    com = res.get("com", "")


    if not info:
        return http_return(400, "查询无结果，请检查单号是否正确或隔断时间再查！")

    # 如快递状态有更新，则更新显示
    if state and userPrize.expressState != state:
        userPrize.expressState = state

    com = com_dict.get(com, com)
    userPrize.expressDetail = json.dumps(info)
    userPrize.com = com
    userPrize.save()
    return Response({"info": info, "state": state, "com": com})


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
    activityUuid = data.get('activityUuid', '')

    if not isinstance(shopList, list):
        return http_return(400, "数据格式错误")

    if not all([shopList, activityUuid]) :
        return http_return(400, "参数有空")

    activity = Activity.objects.filter(uuid=activityUuid).exclude(status="destroy").first()
    if not activity:
        return http_return(400, "无效活动")



    total = len(shopList)

    errorList = []
    # 列表中的字典去重
    # run_function = lambda x, y: x if y in x else x + [y]
    # uniqueList = reduce(run_function, [[], ] + shopList)
    # shopList = uniqueList
    uniqueList = []
    for item in shopList:
        if item in uniqueList:
            item['err_msg'] = "重复添加"
            errorList.append(item)
        else:
            uniqueList += [item]
    shopList = uniqueList
    # 校验用户信息， 重复， 缺少信息， 格式错误，

    for shop in shopList[:]:
        shop["owner"] = shop.get("owner", "")
        shop["tel"] = shop.get("tel", "")
        shop["shopNo"] = shop.get("shopNo", "")
        shop["shopName"] = shop.get("shopName", "")


        # 重复
        if Shop.objects.filter(tel=shop["tel"], shopName=shop["shopName"], shopNo=shop["shopNo"]).exists():
            errorList.append({"err_msg": "重复添加","activityUuid": shop["activityUuid"], "owner": shop["owner"],
                              "tel": shop["tel"], "shopNo": shop["shopNo"], "shopName": shop["shopName"]})
            shopList.remove(shop)
            continue
        if not all([shop["tel"], shop["owner"]]):
            errorList.append({"err_msg": "电话或店主名没有","activityUuid": shop["activityUuid"],
                              "owner": shop["owner"],"tel": shop["tel"],
                              "shopNo": shop["shopNo"], "shopName": shop["shopName"]})
            shopList.remove(shop)
            continue


    data= {"total":total, "success":len(shopList), "fail":total-len(shopList), "err_info": errorList}

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
                    activityUuid=activity,
                    isDelete=False
                ))
            Shop.objects.bulk_create(querysetlist)
        return http_return(200, 'OK', data)
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
        # 更新物流信息（除签收以外）：
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
    inventory = data.get('inventory', '')
    icon = data.get('icon', '')
    name = data.get('name', '')
    probability = data.get('probability', '')
    activityUuid = data.get('activityUuid', '')

    if not all([name, icon, type in [0, 1, 3, 9], activityUuid]):
        return http_return(400, "参数有误")

    if not isinstance(inventory, int):
        return http_return(400, "库存数量格式错误")

    if not inventory >= 0:
        return http_return(400, "库存数量应大于等于0")

    if not (isinstance(probability, float) or (isinstance(probability, int))):
        return http_return(400, "概率格式错误")

    if not 0 <= probability <= 1:
        return http_return(400, "概率在0到1之间")

    activity = Activity.objects.filter(uuid=activityUuid).exclude(status="destroy").first()
    if not activity:
        return http_return(400, "没有此活动")

    if Prize.objects.filter(name=name, isDelete=False).exists():
        return http_return(400, "重复名字")

    total = Prize.objects.filter(isDelete=False, status=1).aggregate(nums=Sum('probability'))['nums']
    if total:
        if round(probability + total, 9) > 1:
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
                activityUuid=activity,
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
    inventory = data.get('inventory', '')
    icon = data.get('icon', '')
    name = data.get('name', '')
    probability = data.get('probability', '')
    activityUuid = data.get('activityUuid', '')

    if not all([prizeUuid, name, icon, type in [0, 1, 3, 9], activityUuid]):
        return http_return(400, "参数有误")

    if not isinstance(inventory, int):
        return http_return(400, "库存数量格式错误")

    if not inventory >= 0:
        return http_return(400, "库存数量应大于等于0")

    if not (isinstance(probability, float) or (isinstance(probability, int))):
        return http_return(400, "概率格式错误")

    if not 0 <= probability <= 1:
        return http_return(400, "概率在0到1之间")

    if not Activity.objects.filter(uuid=activityUuid).exclude(status="destroy").exists():
        return http_return(400, "没有此活动")

    prize = Prize.objects.filter(uuid = prizeUuid, isDelete=False).first()
    if not prize:
        return http_return(400, "无奖品对象")

    total = Prize.objects.filter(isDelete=False, status=1).\
        exclude(uuid = prizeUuid).aggregate(nums=Sum('probability'))['nums']
    if total:
        if round(probability + total, 9) > 1:
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
            prize.activityUuid=activityUuid
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

    if not prize.status:
        total = Prize.objects.filter(isDelete=False, status=1).aggregate(nums=Sum('probability'))['nums']
        if total:
            if round(prize.probability + total, 9) > 1:
                temp = 1 - total
                return http_return(400, "当前启用奖品概率之和已经大于1，建议当前取值小于等于{:.10}".format(temp))
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


def refresh_express():
    # 排除已签收和没有运单号的
    deliveryNumQueryset  = UserPrize.objects.exclude(expressState__in=[3, 7]).values("deliveryNum")
    deliveryNums = [item["deliveryNum"] for item in list(deliveryNumQueryset)]
    for deliveryNum in deliveryNums:
        res = Express100.get_express_info(deliveryNum)
        if not res:
            continue
        res = json.loads(res.text)
        info = res.get("data", "")
        state = res.get("state", "")
        com = res.get("com", "")

        if not info:
            continue

        # 如快递状态有更新，则更新显示
        userPrize = UserPrize.objects.filter(deliveryNum=deliveryNum).first()

        userPrize.expressState = state
        userPrize.expressDetail = json.dumps(info)
        com = com_dict.get(com, com)
        userPrize.com = com
        userPrize.save()


class UserPrizeView(ListAPIView):
    queryset = UserPrize.objects.filter(prizeUuid__type=9) # 只显示实物奖品
    serializer_class = UserPrizeSerializer
    filter_class = UserPrizeFilter
    pagination_class = MyPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('-createTime',)
    ordering_fields = ('id', 'createTime')

    def get_queryset(self):
        refresh_express()
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
            #  0在途，1揽收，2疑难，3签收，4退签，5派件，6退回  7未录入单号 8暂无物流信息
            #  填写快递单号后暂无物流信息状态
            userPrize.expressState = 8
            userPrize.expressDate = timezone.now()
            userPrize.save()
        return http_return(200, 'OK')
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '添加运单号失败')


class UserInvitationView(ListAPIView):
    queryset = User.objects.exclude(status='destroy')
    serializer_class = UserInvitationSerializer
    filter_class = UserInvitationFilter
    pagination_class = MyPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('-createTime', )
    ordering_fields = ('id', 'createTime')

    def get_queryset(self):
        startTimestamp = self.request.query_params.get('starttime', '')
        endTimestamp = self.request.query_params.get('endtime', '')

        if (startTimestamp and not endTimestamp) or (not startTimestamp and endTimestamp):
            raise ParamsException('时间错误')
        if startTimestamp and endTimestamp:
            try:
                starttime, endtime = timestamp2datetime(startTimestamp, endTimestamp)
                self.queryset = self.queryset.filter(createTime__range=(starttime, endtime))
            except Exception as e:
                logging.error(str(e))
                raise ParamsException(e.detail)

        return self.queryset


class UserInvitationDetailView(ListAPIView):
    queryset = User.objects.exclude(status='destroy')
    serializer_class = UserInvitationDetailSerializer
    pagination_class = MyPagination
    ordering = ('createTime', )

    def get_queryset(self):
        userUuid = self.request.query_params.get('userUuid', '')
        if not userUuid:
            raise ParamsException("参数错误")
        user = User.objects.filter(uuid=userUuid).exclude(status='destroy')
        if not user:
            return ParamsException("用户不存在")

        return User.objects.filter(inviter=userUuid).order_by('createTime')



class ShopInvitationView(ListAPIView):
    queryset = Shop.objects.filter(isDelete=False)
    serializer_class = ShopInvitationSerializer
    filter_class = ShopInvitationFilter
    pagination_class = MyPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ('-createTime', )
    ordering_fields = ('id', 'createTime')

    def get_queryset(self):
        startTimestamp = self.request.query_params.get('starttime', '')
        endTimestamp = self.request.query_params.get('endtime', '')

        if (startTimestamp and not endTimestamp) or (not startTimestamp and endTimestamp):
            raise ParamsException('时间错误')
        if startTimestamp and endTimestamp:
            try:
                starttime, endtime = timestamp2datetime(startTimestamp, endTimestamp)
                self.queryset = self.queryset.filter(createTime__range=(starttime, endtime))
            except Exception as e:
                logging.error(str(e))
                raise ParamsException(e.detail)

        return self.queryset


class ShopInvitationDetailView(ListAPIView):
    queryset = Shop.objects.filter(isDelete=False)
    serializer_class = ShopInvitationDetailSerializer
    pagination_class = MyPagination
    ordering = ('createTime', )

    def get_queryset(self):
        shopUuid = self.request.query_params.get('shopUuid', '')
        if not shopUuid:
            raise ParamsException("参数错误")
        shop = Shop.objects.filter(uuid=shopUuid)
        if not shop:
            return ParamsException("门店不存在")

        return User.objects.filter(inviter=shopUuid).order_by('createTime')


class ActivitySelectView(ListAPIView):
    queryset = Activity.objects.filter(status="normal").exclude(endTime__lt=datetime.now())\
        .only("uuid", "name").order_by('-createTime')
    serializer_class = ActivitySelectSerializer
    # filter_class = ActivitySelectFilter
    # pagination_class = MyPagination
    # filter_backends = (DjangoFilterBackend, OrderingFilter)
    # ordering = ('-createTime',)
