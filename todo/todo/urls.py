from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path("admin/",  admin.site.urls),

    # Auth
    path("",        views.home,        name="home"),
    path("signup/", views.signup,      name="signup"),
    path("login/",  views.login_view,  name="login"),
    path("logout/", views.logout_view, name="logout"),

    # Main todo page
    path("todo/",   views.todo_view,   name="todo"),

    # Task CRUD
    path("add-task/",                    views.add_task,       name="add_task"),
    path("toggle-task/<int:srno>/",      views.toggle_task,    name="toggle_task"),
    path("edit-task/<int:srno>/",        views.edit_task,      name="edit_task"),
    path("delete-task/<int:srno>/",      views.delete_task,    name="delete_task"),
    path("toggle-pin/<int:srno>/",       views.toggle_pin,     name="toggle_pin"),
    path("clear-completed/",             views.clear_completed, name="clear_completed"),
    path("bulk-delete/",                 views.bulk_delete,    name="bulk_delete"),

    # Subtasks
    path("add-subtask/<int:srno>/",      views.add_subtask,    name="add_subtask"),
    path("toggle-subtask/<int:pk>/",     views.toggle_subtask, name="toggle_subtask"),
    path("delete-subtask/<int:pk>/",     views.delete_subtask, name="delete_subtask"),

    # ★ Premium features
    path("analytics/",                   views.analytics_view, name="analytics"),
    path("ai-suggest/",                  views.ai_suggest,     name="ai_suggest"),
]