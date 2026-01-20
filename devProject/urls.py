from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    # 🔥 把根路径 / 全部交给 testApp.urls 处理
    path("", include("testApp.urls")),
]