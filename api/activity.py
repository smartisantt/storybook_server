from api.apiCommon import *
from common.common import request_body


@check_identify
def activity_detail(request):
    """
    活动详情
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '请求错误')
    uuid = data.get('uuid', '')
    if not uuid:
        return http_return(400, '参数错误')
    act = Activity.objects.filter(uuid=uuid).first()
    if not act:
        return http_return(400, '活动信息不存在')
    selfUuid = data['_cache']['uuid']
    user = User.objects.filter(uuid=selfUuid).first()
    activityInfo = {
        "uuid": act.uuid,
        "name": act.name,
        "intro": act.intro,
        "icon": act.icon,
        "startTime": datetime_to_unix(act.startTime),
        "endTime": datetime_to_unix(act.endTime),
    }
    # 返回参赛状态，如果参赛再返回排名
    status = 1
    # 定义参赛状态：1：未报名 2：已报名未上传参赛作品 3：已上传参赛作品
    rank = None
    score = None
    game = GameInfo.objects.filter(userUuid__uuid=selfUuid, activityUuid__uuid=uuid).first()
    if game:
        status = 2
        if game.audioUuid != None:
            status = 3
        games = GameInfo.objects.filter(activityUuid__uuid=uuid, audioUuid__isnull=False).all()
        games = sorted(games, key=lambda x: x.votes, reverse=True)
        rank = games.index(game) + 1
        score = game.votes
    userInfo = {
        "uuid": user.uuid,
        "avatar": user.avatar if user.avatar else '',
        "nickname": user.nickName if user.nickName else '',
        "status": status,
        "rank": rank,
        "score": score,
    }
    return http_return(200, '成功', {"activityInfo": activityInfo, "userInfo": userInfo})


@check_identify
def activity_rank(request):
    """
    活动排行
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '请求错误')
    uuid = data.get('uuid', '')
    page = data.get('page', '')
    pageCount = data.get('pageCount', '')
    if not uuid:
        return http_return(400, '参数错误')
    act = Activity.objects.filter(uuid=uuid).first()
    if not act:
        return http_return(400, '活动信息不存在')
    games = GameInfo.objects.filter(audioUuid__isnull=False).all()
    games = sorted(games, key=lambda x: x.votes, reverse=True)
    total, games = page_index(games, page, pageCount)
    activityRankList = []
    for game in games:
        activityRankList.append({
            "publisher": {
                "uuid": game.userUuid.uuid if game.userUuid else '',
                "nickname": game.userUuid.nickName if game.userUuid else '',
                "avatar": game.userUuid.avatar if game.userUuid else '',
            },
            "audio": {
                "uuid": game.audioUuid.uuid if game.audioUuid else '',
                "name": game.audioUuid.name if game.audioUuid else '',
            },
            "score": game.votes,
        })
    return http_return(200, '成功', {"total": total, "list": activityRankList})


@check_identify
def activity_audiostory_list(request):
    """
    用户可参赛作品列表
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '请求错误')
    uuid = data.get('uuid', '')
    page = data.get('page', '')
    pageCount = data.get('pageCount', '')
    if not uuid:
        return http_return(400, '参数错误')
    activityUuidList = []
    games = GameInfo.objects.filter(activityUuid__uuid=uuid).all()
    for game in games:
        activityUuidList.append(game.audioUuid.uuid)
    audio = AudioStory.objects.filter(Q(checkStatus="check") | Q(checkStatus="exemption")).filter(
        isDelete=False).filter(
        userUuid__uuid=data['_cache']['uuid'])
    # 只能使用活动时间内录制的作品参赛
    activity = Activity.objects.filter(uuid=uuid).first()
    if not activity:
        return http_return(400, '活动信息不存在')
    startTime = activity.startTime
    endTime = activity.endTime
    audio = audio.filter(createTime__gte=startTime, createTime__lte=endTime)
    audios = audio.exclude(uuid__in=activityUuidList).order_by("-updateTime").all()
    total, audios = page_index(audios, page, pageCount)
    audioStoryList = audioList_format(audio, data)
    return http_return(200, '成功', {"list": audioStoryList, "total": total})


@check_identify
def activity_join(request):
    """
    参与活动
    :param request:
    :return:
    """
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '请求错误')
    activityUuid = data.get('activityUuid', '')
    audioStoryUuid = data.get('audioStoryUuid', '')
    if not audioStoryUuid:
        return http_return(400, '请选择参赛作品')
    if not activityUuid:
        return http_return(400, '请选择参赛活动')
    activity = Activity.objects.filter(uuid=activityUuid).first()
    if not activity:
        return http_return(400, '活动信息不存在')
    # 校验作品是否可以参加比赛
    checkGame = GameInfo.objects.filter(audioUuid__uuid=audioStoryUuid).first()
    if checkGame:
        return http_return(400, '作品已参与过活动')
    audioStory = AudioStory.objects.filter(uuid=audioStoryUuid).first()
    if not audioStory:
        return http_return(400, '作品信息不存在')
    if audioStory.createTime <= activity.startTime or audioStory.createTime >= activity.endTime:
        return http_return(400, '参赛作品录制时间不在比赛时间内')
    selfUuid = data['_cache']['uuid']
    user = User.objects.filter(uuid=selfUuid).first()
    if not user:
        return http_return(400, '未获取到用户信息')
    checkUser = GameInfo.objects.filter(activityUuid__uuid=activityUuid, userUuid__uuid=selfUuid).first()
    if checkUser:
        return http_return(400, '你已参与过该活动')
    try:
        GameInfo.objects.create(
            uuid=get_uuid(),
            userUuid=user,
            activityUuid=activity,
            audioUuid=audioStory,
        )
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '参赛失败')
    return http_return(200, '参赛成功')
