"""assignment1 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
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
from django.urls import path
from django.conf.urls import url
from django.urls import path, include, re_path
from rest_framework.urlpatterns import format_suffix_patterns
from userservice import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/users', views.usersList.as_view()),
    path('api/v1/db/read', views.table_list.as_view()),
    path('api/v1/db/write', views.table_write.as_view()),
    path('api/v1/_count', views.count_requests.as_view()),
    path('api/v1/db/clear', views.Db_clear.as_view()),
    re_path(r'api/v1/users/(?P<user>\w+)$',views.usersList.as_view())
]


# /api/v1/rides?source={source}&destination={destination}
