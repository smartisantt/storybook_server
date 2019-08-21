import json
import logging
from datetime import datetime

from django.db import transaction
from django.db.models import Q
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import api_view, authentication_classes, throttle_classes
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from common.common import page_index, get_uuid
from common.expressage import Express100
from manager.auths import CustomAuthentication
from manager.filters import ActivityFilter
from manager.managerCommon import request_body, http_return, timestamp2datetime
from manager.models import Activity, GameInfo, ActivityConfig
from manager.paginations import MyPagination
from manager.serializers import ActivitySerializer
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
    res = Express100.get_express_info(str(num).strip())
    res = json.loads(res.text)
    result = res.get("data", "")
    if not result:
        result = "查询无结果，请检查单号是否正确或隔断时间再查！"
    return Response(result)



