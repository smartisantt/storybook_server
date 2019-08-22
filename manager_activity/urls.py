from django.urls import path

from manager_activity import views
from manager_activity.views import ActivityView, ShopView, PrizeView, UserPrizeView

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

]