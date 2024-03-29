from datetime import datetime

from rest_framework import serializers

from manager.models import Tag, User, Bgm, AudioStory, Story, HotSearch, Ad, Module, Activity, GameInfo, CycleBanner, \
    Feedback, Album, AlbumAudioStory, SystemNotification, Behavior
from utils.errors import ParamsException


class TemplateStory(object):
    pass


class StorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Story
        exclude = ('tags', )



class StorySimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Story
        fields = ('uuid', 'name', 'faceIcon', 'listIcon')





class TagsSerialzer(serializers.ModelSerializer):

    childTagsNum = serializers.SerializerMethodField()
    childTagList = serializers.SerializerMethodField()

    @staticmethod
    def get_childTagsNum(tag):
        return Tag.objects.filter(parent=tag, isDelete=False).count()

    @staticmethod
    def get_childTagList(tag):
        queryset = Tag.objects.filter(parent=tag, isDelete=False)
        return TagsChildSerialzer(queryset, many=True).data

    class Meta:
        model = Tag
        fields = ('uuid', 'name', 'sortNum', 'icon','isUsing', 'childTagList',  'childTagsNum')



class TagsChildSerialzer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('uuid', 'name', 'sortNum')


class TagsSimpleSerialzer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        exclude = ("parent", "isDelete", "isUsing", "createTime", "updateTime", "id")

class BgmSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Bgm
        fields = ('name', 'url', 'duration')


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('nickName', 'avatar', 'roles', 'uuid')


class UserDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        exclude = ('versionUuid', 'userID')


class UserSearchSerializer(serializers.ModelSerializer):


    class Meta:
        model = User
        fields = ('uuid', 'nickName', 'id')


class FreedomAudioStoryInfoSerializer(serializers.ModelSerializer):
    tagsInfo = serializers.SerializerMethodField()
    bgmInfo = serializers.SerializerMethodField()
    userInfo = serializers.SerializerMethodField()

    @staticmethod
    def get_tagsInfo(audioinfo):
        tag = audioinfo.tags.filter(isDelete=False).all()
        return TagsSimpleSerialzer(tag, many=True).data

    @staticmethod
    def get_bgmInfo(audioinfo):
        return BgmSimpleSerializer(audioinfo.bgm).data

    @staticmethod
    def get_userInfo(audioinfo):
        return UserSerializer(audioinfo.userUuid).data


    class Meta:
        model = AudioStory
        exclude = ('tags', 'storyUuid', 'userUuid', 'bgm', 'taskID')



class AudioStoryInfoSerializer(serializers.ModelSerializer):
    tagsInfo = serializers.SerializerMethodField()
    bgmInfo = serializers.SerializerMethodField()
    userInfo = serializers.SerializerMethodField()
    storyInfo = serializers.SerializerMethodField()
    # name = serializers.SerializerMethodField()
    # bgIcon = serializers.SerializerMethodField()

    @staticmethod
    def get_tagsInfo(audioinfo):
        tag = audioinfo.tags.filter(isDelete=False).all()
        return TagsSimpleSerialzer(tag, many=True).data

    @staticmethod
    def get_bgmInfo(audioinfo):
        return BgmSimpleSerializer(audioinfo.bgm).data

    @staticmethod
    def get_userInfo(audioinfo):
        return UserSerializer(audioinfo.userUuid).data

    @staticmethod
    def get_storyInfo(audioinfo):
        return StorySerializer(audioinfo.storyUuid).data
    #
    # @staticmethod
    # def get_name(audioinfo):
    #     if audioinfo.audioStoryType == False:
    #         return audioinfo.name
    #     else:
    #         return audioinfo.storyUuid.name if audioinfo.storyUuid else None

    # @staticmethod
    # def get_bgIcon(audioinfo):
    #     if audioinfo.audioStoryType == False:
    #         return audioinfo.bgIcon
    #     else:
    #         return audioinfo.storyUuid.faceIcon if audioinfo.storyUuid else None

    class Meta:
        model = AudioStory
        exclude = ('tags', 'storyUuid', 'userUuid', 'bgm', 'taskID')



class AudioStoryDownloadSerializer(serializers.ModelSerializer):
    # tagsInfo = serializers.SerializerMethodField()
    bgmInfo = serializers.SerializerMethodField()
    userInfo = serializers.SerializerMethodField()
    # storyInfo = serializers.SerializerMethodField()

    # @staticmethod
    # def get_tagsInfo(audioinfo):
    #     return TagsSimpleSerialzer(audioinfo.tags, many=True).data

    @staticmethod
    def get_bgmInfo(audioinfo):
        return BgmSimpleSerializer(audioinfo.bgm).data

    @staticmethod
    def get_userInfo(audioinfo):
        return UserSerializer(audioinfo.userUuid).data

    # @staticmethod
    # def get_storyInfo(audioinfo):
    #     return StorySerializer(audioinfo.storyUuid).data

    class Meta:
        model = AudioStory
        exclude = ('name', 'bgIcon', 'tags', 'storyUuid', 'userUuid', 'bgm', 'isDelete')



class AudioStorySimpleSerializer(serializers.ModelSerializer):
    storyInfo = serializers.SerializerMethodField()
    nickName = serializers.SerializerMethodField()

    @staticmethod
    def get_storyInfo(audioinfo):
        return StorySimpleSerializer(audioinfo.storyUuid).data

    @staticmethod
    def get_nickName(audioinfo):
        return audioinfo.userUuid.nickName

    class Meta:
        model = AudioStory
        fields = ('name', 'storyInfo', 'audioStoryType', 'bgIcon', 'nickName', 'createTime', 'uuid')


class QualifiedAudioStoryInfoSerializer(serializers.ModelSerializer):
    tagsInfo = serializers.SerializerMethodField()
    bgmInfo = serializers.SerializerMethodField()
    userInfo = serializers.SerializerMethodField()
    storyInfo = serializers.SerializerMethodField()

    @staticmethod
    def get_tagsInfo(audioinfo):
        return TagsSimpleSerialzer(audioinfo.tags, many=True).data

    @staticmethod
    def get_bgmInfo(audioinfo):
        return BgmSimpleSerializer(audioinfo.bgm).data

    @staticmethod
    def get_userInfo(audioinfo):
        return UserSerializer(audioinfo.userUuid).data

    @staticmethod
    def get_storyInfo(audioinfo):
        return StorySerializer(audioinfo.storyUuid).data


    class Meta:
        model = AudioStory
        exclude = ('tags', 'storyUuid', 'userUuid', 'bgm', 'taskID')


class CheckAudioStoryInfoSerializer(serializers.ModelSerializer):
    tagsInfo = serializers.SerializerMethodField()
    bgmInfo = serializers.SerializerMethodField()
    userInfo = serializers.SerializerMethodField()
    storyInfo = serializers.SerializerMethodField()

    @staticmethod
    def get_tagsInfo(audioinfo):
        tag = audioinfo.tags.filter(isDelete=False).all()
        return TagsSimpleSerialzer(tag, many=True).data

    @staticmethod
    def get_bgmInfo(audioinfo):
        return BgmSimpleSerializer(audioinfo.bgm).data

    @staticmethod
    def get_userInfo(audioinfo):
        return UserSerializer(audioinfo.userUuid).data

    @staticmethod
    def get_storyInfo(audioinfo):
        return StorySerializer(audioinfo.storyUuid).data


    class Meta:
        model = AudioStory
        exclude = ('tags', 'storyUuid', 'userUuid', 'bgm', "taskID")


class BgmSerializer(serializers.ModelSerializer):

    class Meta:
        model = Bgm
        fields = "__all__"


class HotSearchSerializer(serializers.ModelSerializer):

    class Meta:
        model = HotSearch
        fields = "__all__"


class AdSerializer(serializers.ModelSerializer):
    linkObjectInfo = serializers.SerializerMethodField()
    isPast = serializers.SerializerMethodField()

    @staticmethod
    def get_isPast(cycleBanner):
        return cycleBanner.endTime < datetime.now()

    @staticmethod
    def get_linkObjectInfo(ad):
        linkObjectInfo = ""
        if ad.type == 0:  # 活动
            try:
                linkObjectInfo = Activity.objects.filter(uuid=ad.target).first().name
            except:
                raise ParamsException({'code': 400, 'msg': '参数错误'})
        elif ad.type == 1:  # 专辑
            try:
                linkObjectInfo = Album.objects.filter(uuid=ad.target).first().title
            except:
                raise ParamsException({'code': 400, 'msg': '参数错误'})
        elif ad.type == 2:  # 音频
            try:
                audioStory = AudioStory.objects.filter(uuid=ad.target).first()
                linkObjectInfo = audioStory.storyUuid.name if audioStory.audioStoryType else audioStory.name
            except:
                raise ParamsException({'code': 400, 'msg': '参数错误'})
        elif ad.type == 3:  # 商品
            pass
        elif ad.type == 4:
            linkObjectInfo = ad.target

        return linkObjectInfo

    class Meta:
        model = Ad
        exclude = ("isDelete", )



class ModuleSerializer(serializers.ModelSerializer):
    audioStory = serializers.SerializerMethodField()
    album = serializers.SerializerMethodField()


    @staticmethod
    def get_audioStory(module):
        if module.contentType in [1, 2]:
            return AudioStorySimpleSerializer(module.audioUuid).data
        return {}

    @staticmethod
    def get_album(module):
        if module.contentType == 3:
            return AlbumSerializer(module.albumUuid).data
        return {}
    class Meta:
        model = Module
        exclude = ('audioUuid', 'albumUuid', 'id', 'createTime', 'updateTime', 'isDelete')


class GameInfoSerializer(serializers.ModelSerializer):
    # userInfo = serializers.SerializerMethodField()
    audioInfo = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()

    @staticmethod
    def get_score(gameInfo):
        return gameInfo.votes

    # @staticmethod
    # def get_userInfo(gameInfo):
    #     return UserSearchSerializer(gameInfo.userUuid).data

    @staticmethod
    def get_audioInfo(gameInfo):
        # return AudioStoryInfoSerializer(gameInfo.audioUuid).data
        return AudioStoryDownloadSerializer(gameInfo.audioUuid).data


    class Meta:
        model = GameInfo
        fields = ("createTime", "uuid", "audioUuid", "audioInfo", "score")


class ActivitySerializer(serializers.ModelSerializer):

    count = serializers.SerializerMethodField()
    # 返回当前活动处于哪个阶段 未开始，进行中，已结束
    stage = serializers.SerializerMethodField()


    @staticmethod
    def get_count(activity):
        return activity.activityRankUuid.count()

    @staticmethod
    def get_stage(activity):
        # currentTime = datetime.now()
        currentTime =datetime.now()

        if activity.endTime<currentTime:
            return "past"
        elif activity.startTime<=currentTime<=activity.endTime:
            return "now"
        elif currentTime<activity.startTime:
            return "future"



    class Meta:
        model = Activity
        fields = ("name", "startTime", "endTime", "count", "uuid", "id", "intro", "icon", "stage","url")




class CycleBannerSerializer(serializers.ModelSerializer):

    linkObjectInfo = serializers.SerializerMethodField()
    isPast = serializers.SerializerMethodField()

    @staticmethod
    def get_isPast(cycleBanner):
        return cycleBanner.endTime < datetime.now()

    @staticmethod
    def get_linkObjectInfo(cycleBanner):
        linkObjectInfo = ""
        if cycleBanner.type == 0:   # 活动
            try:
                linkObjectInfo = Activity.objects.filter(uuid=cycleBanner.target).first().name
            except:
                raise ParamsException({'code': 400, 'msg': '数据库存储数据格式错误'})
        elif cycleBanner.type == 1: # 专辑
            try:
                linkObjectInfo = Album.objects.filter(uuid=cycleBanner.target).first().title
            except:
                raise ParamsException({'code': 400, 'msg': '参数错误'})
        elif cycleBanner.type == 2: # 音频
            try:
                audioStory = AudioStory.objects.filter(uuid=cycleBanner.target).first()
                linkObjectInfo = audioStory.storyUuid.name if audioStory.audioStoryType else audioStory.name
            except:
                raise ParamsException({'code': 400, 'msg': '数据库存储数据格式错误'})
        elif cycleBanner.type == 3: # 商品
            pass
        elif cycleBanner.type == 4: # 外部连接
            linkObjectInfo = cycleBanner.target
        elif cycleBanner.type == 5: # 模板
            pass

        return linkObjectInfo


    class Meta:
        model = CycleBanner
        exclude = ("location", "isDelete")



class FeedbackSerializer(serializers.ModelSerializer):

    userInfo = serializers.SerializerMethodField()

    @staticmethod
    def get_userInfo(feedback):
        return UserSearchSerializer(feedback.userUuid).data

    class Meta:
        model = Feedback
        exclude = ("userUuid", )


# class Feedback2Serializer(serializers.Serializer):
#     # 校验数据
#     uuid = serializers.CharField(required=True)
#     replyInfo = serializers.CharField(required=True,
#                                       error_messages={'required':"replyInfo不能为空"})
#
#     def validate(self, attrs):
#         feedback = Feedback.objects.filter(uuid=attrs.get('uuid')).first()
#         if not Feedback.objects.filter(uuid=attrs.get('uuid')).exists():
#             raise ValidationError('无效的uuid')
#
#         if feedback.status == 1:
#             oldReplyInfo = feedback.replyInfo
#             if oldReplyInfo == attrs.get('replyInfo'):
#                 raise ValidationError('两次回复消息一样')
#         return attrs


    def reply2_data(self, validate_data):
        feedback = Feedback.objects.filter(uuid=validate_data['uuid']).first()
        feedback.replyInfo = validate_data['replyInfo']
        feedback.status = 1
        feedback.isRead = False
        feedback.save()
        return True


class AlbumDetailSerializer(serializers.ModelSerializer):
    # authorInfo = serializers.SerializerMethodField()
    #
    # @staticmethod
    # def get_authorInfo(album):
    #     return UserSearchSerializer(album.author).data
    author = serializers.StringRelatedField()
    totalCount = serializers.SerializerMethodField()
    audioInfo = serializers.SerializerMethodField()
    tagsInfo = serializers.SerializerMethodField()
    authorUuid = serializers.SerializerMethodField()

    @staticmethod
    def get_authorUuid(album):
        return album.author.uuid

    @staticmethod
    def get_totalCount(album):
        return AlbumAudioStory.objects.filter(isUsing=True, album=album).count()

    @staticmethod
    def get_audioInfo(album):
        queryset = AlbumAudioStory.objects.filter(album=album)
        return AlbumAudioStoryDetailSerializer(queryset, many=True).data

    @staticmethod
    def get_tagsInfo(album):
        tag = album.tags.filter(isDelete=False).all()
        return TagsSimpleSerialzer(tag, many=True).data


    class Meta:
        model = Album
        fields = ("uuid", "title", "intro", "createTime", "author", "isManagerCreate",
                  "totalCount", "faceIcon", "authorUuid", "audioInfo", "tagsInfo")


class AlbumSerializer(serializers.ModelSerializer):
    # authorInfo = serializers.SerializerMethodField()
    #
    # @staticmethod
    # def get_authorInfo(album):
    #     return UserSearchSerializer(album.author).data
    author = serializers.StringRelatedField()
    authorUuid = serializers.SerializerMethodField()
    totalCount = serializers.SerializerMethodField()
    tagsInfo = serializers.SerializerMethodField()

    @staticmethod
    def get_authorUuid(album):
        return album.author.uuid

    @staticmethod
    def get_tagsInfo(album):
        tag = album.tags.filter(isDelete=False).all()
        return TagsSimpleSerialzer(tag, many=True).data

    @staticmethod
    def get_totalCount(album):
        return AlbumAudioStory.objects.filter(isUsing=True, album=album).count()

    class Meta:
        model = Album
        fields = ("title", "id", "createTime", "author", "faceIcon", "intro",
                  "isManagerCreate", "totalCount", "uuid", "authorUuid", "tagsInfo")


class CheckAlbumSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField()
    tagsInfo = serializers.SerializerMethodField()

    @staticmethod
    def get_tagsInfo(album):
        tag = album.tags.filter(isDelete=False).all()
        return TagsSimpleSerialzer(tag, many=True).data

    class Meta:
        model = Album
        fields = ("title", "faceIcon",  "id", "intro", "createTime", "author","faceIcon",
                  "checkStatus", "isManagerCreate", "uuid", "tagsInfo")


class AudioStorySimple2Serializer(serializers.ModelSerializer):
    tagsInfo = serializers.SerializerMethodField()

    @staticmethod
    def get_tagsInfo(audioinfo):
        tag = audioinfo.tags.filter(isDelete=False).all()
        return TagsSimpleSerialzer(tag, many=True).data

    class Meta:
        model = AudioStory
        fields = ('name', 'id', 'voiceUrl', 'mixAudioUrl', 'createTime', 'uuid', "type", "tagsInfo")


class AlbumAudioStoryDetailSerializer(serializers.ModelSerializer):
    audioStoryInfo = serializers.SerializerMethodField()

    @staticmethod
    def get_audioStoryInfo(object):
        return AudioStorySimple2Serializer(object.audioStory).data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['sortNum'] = list(self.instance).index(instance)+1
        return data

    class Meta:
        model = AlbumAudioStory
        fields = ("isUsing", "createTime", "audioStoryInfo")


class AuthorAudioStorySerializer(serializers.ModelSerializer):

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['sortNum'] = list(self.instance).index(instance)+1
        return data

    class Meta:
        model = AudioStory
        fields = ('name', 'createTime', 'uuid')


class NotificationSerializer(serializers.ModelSerializer):
    isPublish = serializers.SerializerMethodField()

    @staticmethod
    def get_isPublish(notification):
        return notification.publishDate < datetime.now()
        # return (notification.publishDate < datetime.now()) and notification.publishState in [1,3,7]

    class Meta:
        model = SystemNotification
        fields = ("uuid", "title", "content", "createTime",
                  "publishDate", "isPublish", "linkAddress", "linkText",
                  "type", "activityUuid")


class CommentSerializer(serializers.ModelSerializer):
    nickName = serializers.SerializerMethodField()

    @staticmethod
    def get_nickName(comment):
        return comment.userUuid.nickName

    class Meta:
        model = Behavior
        fields = ("uuid", "nickName", "remarks", "createTime", "checkInfo", "checkStatus", "adminStatus")






