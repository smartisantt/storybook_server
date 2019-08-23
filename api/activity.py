from api.apiCommon import *
from common.common import request_body


@check_identify
def activity_index(request):
    """活动首页"""
    data = request_body(request)
    if not data:
        return http_return(400, '请求错误')
    uuid = data.get('uuid', '')
    if not uuid:
        return http_return(400, '请选择要查看的活动')
    keyword = data.get('keyword', '')
    game = GameInfo.objects.filter(audioUuid__isnull=False)
    if keyword:
        game = game.filter(Q(audioUuid__name__contains=keyword) | Q(userUuid__nickName__contains=keyword))
    games = game.order_by("?").all()
    page = data.get('page', '')
    pageCount = data.get('pageCount', '')
    total, games = page_index(games, page, pageCount)
    activityRankList = activityRankList_format(games)
    return http_return(200, '成功', {"total": total, "list": activityRankList})


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
        return http_return(400, '请选择要查看的活动')
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
    activityRankList = activityRankList_format(games)
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
    audio = AudioStory.objects.filter(isDelete=False, userUuid__uuid=data['_cache']['uuid'])
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
def activity_sign(request):
    """
    活动报名
    :param request:
    :return:
    """
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '请求错误')
    activityUuid = data.get('activityUuid', '')
    if not activityUuid:
        return http_return(400, '请选择要报名的活动')
    act = Activity.objects.filter(uuid=activityUuid).first()
    if not act:
        return http_return(400, '活动信息不存在')
    inviter = data.get("inviter")
    try:
        GameInfo.objects.create(
            uuid=get_uuid(),
            userUuid=User.objects.filter(uuid=data['_cache']['uuid']).first(),
            activityUuid=act,
            inviter=inviter
        )
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '报名失败')
    return http_return(200, '报名成功')


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
    game = GameInfo.objects.filter(activityUuid__uuid=activityUuid, userUuid__uuid=data['_cache']['uuid']).first()
    if not game:
        return http_return(400, '请报名后再上传作品')
    try:
        game.audioUuid = audioStory
        game.save()
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '参赛失败')
    return http_return(200, '参赛成功')


@check_identify
def activity_vote(request):
    """
    为作品投票
    :param request:
    :return:
    """
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '请求错误')
    uuid = data.get("uuid", "")
    if not uuid:
        return http_return(400, "请选择要投票的作品")
    game = GameInfo.objects.filter(uuid=uuid, audioUuid__isnull=False).first()
    if not game:
        return http_return(400, "未获取到参赛作品信息")
    selfUuid = data['_cache']['uuid']
    user = User.objects.filter(uuid=selfUuid).filter()
    todayDate = datetime.datetime.today()
    voteBehavior = VoteBehavior.objects.filter(userUuid__uuid=selfUuid, voteDate=todayDate).first()
    if voteBehavior:
        return http_return(400, '今日票数已用完')
    game.votes += 1
    voteBehavior = VoteBehavior(
        uuid=get_uuid(),
        userUuid=user,
        gameUuid=game,
        voteDate=todayDate,
    )
    try:
        with transaction.atomic():
            game.save()
            voteBehavior.save()
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '投票失败')
    return http_return(200, '投票成功')


@check_identify
def invite_user(request):
    """
    注册邀请关系确定
    :param request:
    :return:
    """
    data = request_body(request, 'POST')
    if not data:
        return http_return(400, '请求错误')
    inviter = data.get("inviter", "")
    if not inviter:
        return http_return(400, '邀请参数错误')
    user = User.objects.filter(uuid=data['_cache']['uuid']).first()
    if not user:
        return http_return(400, "未获取到用户信息")
    try:
        user.inviter = inviter
        user.save()
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '关系建立失败')
    return http_return(200, '关系建立成功')


@check_identify
def prize_list(request):
    """
    奖品列表
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '请求错误')
    # uuid = data.get('uuid', '') 如果多个活动，则要关联，第一个版本不做
    prizes = Prize.objects.filter(isDelete=False, status=1).all()[:8]
    prizeList = []
    for prize in prizes:
        prizeList.append({
            "uuid": prize.uuid,
            "name": prize.name if prize.name else "",
            "icon": prize.icon if prize.icon else "",
        })
    return http_return(200, prizeList)


@check_identify
def prize_draw(request):
    """
    抽奖
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '请求错误')
