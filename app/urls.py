"""app URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URL_conf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf.urls.static import static
from django.urls import path

from app import views, settings

urlpatterns = [
                  path('', views.normal),
                  path('admin/', admin.site.urls),
                  path('login', views.login),
                  path('register', views.register),
                  path('append/tie', views.append_tie),
                  path('reply/tie', views.append_floor),
                  path('reply/floor', views.append_reply_floor),
                  path('get/tie', views.get_tie_by_id),
                  path('get/tie/list', views.get_tie_list),
                  path('get/floor', views.get_floor),
                  path('get/reply_floor', views.get_reply_floor),
                  path('like', views.like),
                  path('get/user/info', views.get_user_info),
                  path('get/user/tie', views.get_user_tie),
                  path('get/ba', views.get_ba),
                  path('sign', views.sign),
                  path('subscription/ba', views.subscription_ba),
                  path('change/user_info', views.change_user_info),
                  path('change/avatar', views.change_avatar),
                  path(r'save/image', views.save_image),
                  # 就是路由-操作对
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
