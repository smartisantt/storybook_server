from django.urls import path
from django.views.decorators.cache import cache_page

from manager_activity import views
from manager_activity.views import ActivityView, ShopView, PrizeView, UserPrizeView, UserInvitationView, \
    ShopInvitationView, UserInvitationDetailView, ShopInvitationDetailView, ActivitySelectView

urlpatterns = [
    path('activitylist/', ActivityView.as_view()),
    path('rankactivity/', views.activity_rank, name='activity_rank'),
    path('createactivity/', views.create_activity, name='create_activity'),
    path('modifyactivity/', views.modify_activity, name='modify_activity'),

    # 查询快递接口
    path('expressage/', views.query_expressage, name='queryexpressage'),

    # 门店信息
    path('shoplist/', ShopView.as_view()),
    path('addshopinfo/', views.add_shop_info, name='addshopinfo'),

    # 奖品列表
    path('prizelist/', PrizeView.as_view()),
    path('addprize/', views.add_prize, name='addprize'),
    path('modifyprize/', views.modify_prize, name='modifyprize'),
    path('forbidprize/', views.forbid_prize, name='forbidprize'),
    path('delprize/', views.del_prize, name='delprize'),

    # 发货管理
    path('userprizelist/', UserPrizeView.as_view()),
    path('adduserprize/', views.add_user_prize, name='adduserprize'),

    # 用户邀请关系
    path('userinvitationlist/', UserInvitationView.as_view()),
    path('userinvitationdetail/', UserInvitationDetailView.as_view()),
    # path('invitationdetail/', views.invitation_detail, name='invitationdetail'),

    # 店主邀请关系
    path('shopinvitationlist/', ShopInvitationView.as_view()),
    path('shopinvitationdetail/', ShopInvitationDetailView.as_view()),

    # 选择活动 （现在正在进行的 未来的活动）
    path('activityselect/', ActivitySelectView.as_view()),
]