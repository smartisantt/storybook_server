from django.urls import path

from manager_activity import views
from manager_activity.views import ActivityView

urlpatterns = [
    path('activitylist/', ActivityView.as_view()),
    path('rankactivity/', views.activity_rank, name='activity_rank'),
    path('createactivity/', views.create_activity, name='create_activity'),
    path('modifyactivity/', views.modify_activity, name='modify_activity'),

    # 查询快递接口
    path('expressage/', views.query_expressage, name='queryexpressage'),
]