from django.shortcuts import render, get_object_or_404, redirect
from .models import Post
from .forms import PostForm

from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView, LogoutView

from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt

from datetime import datetime, timezone  # ✅ 用于 UTC 时间

import requests
import os
import json
import random


# ========= タイムライン / 投稿 =========
def timeline(request):
    q = request.GET.get("q")
    posts = Post.objects.all().order_by("-created_at")
    if q:
        posts = posts.filter(content__icontains=q)

    context = {"posts": posts, "q": q}
    return render(request, "timeline.html", context)


def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    return render(request, "post_detail.html", {"post": post})


@login_required
def post_create(request):
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect("timeline")
    else:
        form = PostForm()
    return render(request, "post_create.html", {"form": form})


def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)

    if request.user != post.author:
        return redirect("post_detail", pk=pk)

    if request.method == "POST":
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            return redirect("post_detail", pk=pk)
    else:
        form = PostForm(instance=post)

    return render(request, "post_edit.html", {"form": form, "post": post})


def post_delete(request, pk):
    post = get_object_or_404(Post, pk=pk)

    if request.user != post.author:
        return redirect("post_detail", pk=pk)

    if request.method == "POST":
        post.delete()
        return redirect("timeline")

    return render(request, "post_delete.html", {"post": post})


def like_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    user = request.user

    if post.likes.filter(id=user.id).exists():
        post.likes.remove(user)
        liked = False
    else:
        post.likes.add(user)
        liked = True

    return JsonResponse({"liked": liked, "count": post.total_likes()})


# ========= ポモドーロ =========
def pomodoro(request):
    work_minutes = int(request.GET.get("work", 25))
    break_minutes = int(request.GET.get("rest", 5))

    context = {
        "work_minutes": work_minutes,
        "break_minutes": break_minutes,
    }
    return render(request, "pomodoro.html", context)


# ========= 認証 =========
class SignUpView(CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy("login")
    template_name = "signup.html"


class LoginViewCustom(LoginView):
    template_name = "login.html"


class LogoutViewCustom(LogoutView):
    next_page = "timeline"


# ========= Freesound: 環境音 =========
@require_GET
def api_sound(request):
    """
    Freesound からタグ(tag)に応じた環境音を1つランダム取得して返す API。

    ここを詳しくデバッグできるように、print とエラー情報をかなり出すようにしている。
    """
    tag = (request.GET.get("tag") or "rain").strip()  # 例: "rain", "birds"

    token = os.environ.get("FREESOUND_TOKEN")
    if not token:
        return JsonResponse({"error": "FREESOUND_TOKEN is not set"}, status=500)

    url = "https://freesound.org/apiv2/search/text/"

    # ✅ Freesound は query パラメータ token= でも、Authorization: Token xxxx でもOK
    # 念のため両方つけておく
    params = {
        "query": tag,
        "page_size": 20,
        "fields": "id,name,previews",
        "token": token,
    }
    headers = {"Authorization": f"Token {token}"}

    try:
        print("[api_sound] ===============================")
        print("[api_sound] tag =", tag)
        print("[api_sound] url =", url)

        r = requests.get(url, params=params, headers=headers, timeout=10)

        print("[api_sound] status =", r.status_code)
        print("[api_sound] content-type =", r.headers.get("Content-Type"))
        # レスポンスの先頭だけログに出す（全部は長すぎるので）
        print("[api_sound] body_preview =", r.text[:400])

        # ステータスコードが 200 以外なら例外にして except でまとめて処理
        r.raise_for_status()

        # JSON パース
        try:
            data = r.json()
        except Exception as e:
            print("[api_sound] JSON decode error:", e)
            return JsonResponse(
                {
                    "error": "Freesound JSON parse error",
                    "detail": str(e),
                    "raw": r.text[:200],
                },
                status=502,
            )

        results = data.get("results") or []
        if not results:
            print("[api_sound] no results for tag =", tag)
            return JsonResponse({"error": f"No sound found for tag={tag}"}, status=404)

        chosen = random.choice(results)
        previews = chosen.get("previews") or {}
        mp3 = previews.get("preview-hq-mp3") or previews.get("preview-lq-mp3")

        if not mp3:
            print("[api_sound] no mp3 preview in chosen result:", chosen)
            return JsonResponse({"error": "No mp3 preview found"}, status=502)

        print("[api_sound] chosen id =", chosen.get("id"))
        print("[api_sound] chosen name =", chosen.get("name"))
        print("[api_sound] chosen mp3 =", mp3)

        return JsonResponse(
            {
                "id": chosen.get("id"),
                "name": chosen.get("name"),
                "mp3Url": mp3,
                "tag": tag,
            }
        )

    except requests.exceptions.RequestException as e:
        # ネットワーク系エラー（タイムアウトなど）
        print("[api_sound] RequestException:", repr(e))
        return JsonResponse(
            {"error": "Freesound request exception", "detail": str(e)},
            status=502,
        )
    except Exception as e:
        # それ以外のエラー
        print("[api_sound] Other exception:", repr(e))
        return JsonResponse(
            {"error": "Freesound exception", "detail": str(e)},
            status=502,
        )


# ========= Todoist helper =========
def _todoist_headers():
    token = os.environ.get("TODOIST_TOKEN")
    if not token:
        return None
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ========= Todoist: タスクリスト取得 =========
@require_GET
def api_todoist_tasks(request):
    headers = _todoist_headers()
    if not headers:
        return JsonResponse({"error": "TODOIST_TOKEN is not set"}, status=500)

    url = "https://api.todoist.com/rest/v2/tasks"
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200:
            return JsonResponse(
                {"error": "Todoist list failed", "status": r.status_code, "body": r.text},
                status=502,
            )

        tasks = r.json()
        simple = [{"id": t.get("id"), "content": t.get("content")} for t in tasks]
        return JsonResponse({"tasks": simple})
    except Exception as e:
        return JsonResponse({"error": "Todoist exception", "detail": str(e)}, status=502)


# ========= Todoist: タスク作成 =========
@csrf_exempt
@require_POST
def api_todoist_create_task(request):
    headers = _todoist_headers()
    if not headers:
        return JsonResponse({"error": "TODOIST_TOKEN is not set"}, status=500)

    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
        content = (body.get("content") or "").strip()
    except Exception:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    if not content:
        return JsonResponse({"error": "content is required"}, status=400)

    url = "https://api.todoist.com/rest/v2/tasks"
    try:
        r = requests.post(url, headers=headers, json={"content": content}, timeout=15)
        if r.status_code not in (200, 201):
            return JsonResponse(
                {"error": "Todoist create failed", "status": r.status_code, "body": r.text},
                status=502,
            )

        task = r.json()
        return JsonResponse({"id": task.get("id"), "content": task.get("content")})
    except Exception as e:
        return JsonResponse({"error": "Todoist exception", "detail": str(e)}, status=502)


# ========= Todoist: タスク完了 =========
@csrf_exempt
@require_POST
def api_todoist_close_task(request):
    headers = _todoist_headers()
    if not headers:
        return JsonResponse({"error": "TODOIST_TOKEN is not set"}, status=500)

    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
        task_id = body.get("taskId")
    except Exception:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    if not task_id:
        return JsonResponse({"error": "taskId is required"}, status=400)

    url = f"https://api.todoist.com/rest/v2/tasks/{task_id}/close"
    try:
        r = requests.post(url, headers=headers, timeout=15)
        if r.status_code not in (204, 200):
            return JsonResponse(
                {"error": "Todoist close failed", "status": r.status_code, "body": r.text},
                status=502,
            )
        return JsonResponse({"ok": True})
    except Exception as e:
        return JsonResponse({"error": "Todoist exception", "detail": str(e)}, status=502)


# ========= UTC Time (no external API) =========
@require_GET
def api_time_utc(request):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    return JsonResponse({"datetime": now})


   