"""stroybook_sever URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from api import urls as apiUrl
from manager import urls as managerUrl
from manager_activity import urls as activityUrl

urlpatterns = [
    # path('admin/', admin.site.urls),
    path('api/ht/', include((apiUrl, 'api'), namespace='api')),
    path('api/manage/', include((managerUrl, 'manager'), namespace='manager')),
    path('api/manage/activity/', include((activityUrl, 'manager_activity'), namespace='manager_activity')),
]
