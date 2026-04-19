# ============================================================
#  urls.py — URL Routes
#
#  Feature map:
#    view1  →  Auth
#    view2  →  Task CRUD
#    view3  →  Subtasks
#    view4  →  Analytics
#    view5  →  AI Suggestions
#    view6  →  Google Sign-In (via social_django)
#    view7  →  Deadline Prediction ML
#    view8  →  Voice-to-Task
# ============================================================

from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [

    path("admin/", admin.site.urls),

    # ── view1: Auth ───────────────────────────────────────────────
    path("",        views.home,        name="home"),
    path("signup/", views.signup,      name="signup"),
    path("login/",  views.login_view,  name="login"),
    path("logout/", views.logout_view, name="logout"),

    # ── view2: Task CRUD ──────────────────────────────────────────
    path("todo/",                       views.todo_view,       name="todo"),
    path("add-task/",                   views.add_task,        name="add_task"),
    path("toggle-task/<int:srno>/",     views.toggle_task,     name="toggle_task"),
    path("edit-task/<int:srno>/",       views.edit_task,       name="edit_task"),
    path("delete-task/<int:srno>/",     views.delete_task,     name="delete_task"),
    path("toggle-pin/<int:srno>/",      views.toggle_pin,      name="toggle_pin"),
    path("clear-completed/",            views.clear_completed, name="clear_completed"),
    path("bulk-delete/",                views.bulk_delete,     name="bulk_delete"),

    # ── view3: Subtasks ───────────────────────────────────────────
    path("add-subtask/<int:srno>/",     views.add_subtask,     name="add_subtask"),
    path("toggle-subtask/<int:pk>/",    views.toggle_subtask,  name="toggle_subtask"),
    path("delete-subtask/<int:pk>/",    views.delete_subtask,  name="delete_subtask"),

    # ── view4: Analytics ──────────────────────────────────────────
    path("analytics/",                  views.analytics_view,  name="analytics"),

    # ── view5: AI Suggestions ─────────────────────────────────────
    path("ai-suggest/",                 views.ai_suggest,      name="ai_suggest"),

    # ── view7: Deadline Prediction ML ─────────────────────────────
    path("predict-deadline/",           views.predict_deadline, name="predict_deadline"),

    # ── view8: Voice-to-Task ──────────────────────────────────────
    path("voice-to-task/",              views.voice_to_task,   name="voice_to_task"),

]