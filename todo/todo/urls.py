"""
URL configuration for todo project.
"""
from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name="home"),
    path('signup/', views.signup, name="signup"),
    path('login/', views.login_view, name="login"),
    path('todo/', views.todo_view, name="todo"),
    path('add-task/', views.add_task, name="add_task"),
    path('delete-task/<int:srno>/', views.delete_task, name="delete_task"),
    path('logout/', views.logout_view, name="logout"),
]
