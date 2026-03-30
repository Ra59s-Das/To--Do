from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import TODOO


def home(request):
    """Landing page — shown at /"""
    if request.user.is_authenticated:
        return redirect("todo")
    return render(request, "home.html")


def signup(request):
    if request.method == "POST":
        username   = request.POST.get("username")
        first_name = request.POST.get("first_name")
        last_name  = request.POST.get("last_name")
        email      = request.POST.get("email")
        password   = request.POST.get("password")

        if not username or not password:
            return render(request, "signup.html", {"error": "Username and password are required"})

        if User.objects.filter(username=username).exists():
            return render(request, "signup.html", {"error": "Username already taken"})

        if User.objects.filter(email=email).exists():
            return render(request, "signup.html", {"error": "Email already registered. Please log in."})

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        login(request, user)
        return redirect("todo")

    return render(request, "signup.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("todo")
        return render(request, "login.html", {"error": "Invalid credentials"})
    return render(request, "login.html")


@login_required
def todo_view(request):
    """Main todo list page — requires login."""
    tasks = TODOO.objects.filter(user=request.user).order_by("-data")
    return render(request, "todo.html", {"tasks": tasks})


@login_required
def add_task(request):
    """Add a new task (POST only)."""
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        if title:
            TODOO.objects.create(title=title, user=request.user)
    return redirect("todo")


@login_required
def delete_task(request, srno):
    """Delete a task by its primary key (POST only)."""
    if request.method == "POST":
        task = get_object_or_404(TODOO, srno=srno, user=request.user)
        task.delete()
    return redirect("todo")


def logout_view(request):
    logout(request)
    return redirect("home")
