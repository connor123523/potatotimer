# devProject2/devProject/testApp/urls.py

from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    # ホーム（タイムライン）
    path("", views.timeline, name="timeline"),

    # 投稿関連
    path("post/<int:pk>/", views.post_detail, name="post_detail"),
    path("post_create", views.post_create, name="post_create"),
    path("post/<int:pk>/edit/", views.post_edit, name="post_edit"),
    path("post/<int:pk>/delete/", views.post_delete, name="post_delete"),
    path("post/<int:pk>/like/", views.like_post, name="like_post"),

    # 認証
    path("signup/", views.SignUpView.as_view(), name="signup"),
    path("login/", views.LoginViewCustom.as_view(), name="login"),
    path("logout/", LogoutView.as_view(next_page="timeline"), name="logout"),

    # ポモドーロ
    path("pomodoro/", views.pomodoro, name="pomodoro"),

    # Freesound
    path("api/sound/", views.api_sound, name="api_sound"),

    # Todoist
    path("api/todoist/tasks/", views.api_todoist_tasks, name="api_todoist_tasks"),
    path("api/todoist/task/create/", views.api_todoist_create_task, name="api_todoist_create_task"),
    path("api/todoist/task/close/", views.api_todoist_close_task, name="api_todoist_close_task"),

    # UTC 時刻
    path("api/time/utc/", views.api_time_utc, name="api_time_utc"),
]
