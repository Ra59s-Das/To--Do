# ============================================================
#  VIEW 1 — Authentication
#  Feature: home page, signup, login, logout
#  URLs:    /  /signup/  /login/  /logout/
# ============================================================

from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from .model3 import UserProfile


def _get_or_create_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def home(request):
    if request.user.is_authenticated:
        return redirect("todo")
    return render(request, "home.html")


def signup(request):
    if request.method == "POST":
        username   = request.POST.get("username", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name  = request.POST.get("last_name", "").strip()
        email      = request.POST.get("email", "").strip()
        password   = request.POST.get("password", "")

        if not username or not password:
            return render(request, "signup.html", {"error": "Username and password are required"})
        if User.objects.filter(username=username).exists():
            return render(request, "signup.html", {"error": "Username already taken"})
        if email and User.objects.filter(email=email).exists():
            return render(request, "signup.html", {"error": "Email already registered."})

        user = User.objects.create_user(
            username=username, email=email, password=password,
            first_name=first_name, last_name=last_name,
        )
        _get_or_create_profile(user)
        login(request, user)
        return redirect("todo")

    return render(request, "signup.html")


def login_view(request):
    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST.get("username"),
            password=request.POST.get("password"),
        )
        if user:
            login(request, user)
            return redirect("todo")
        return render(request, "login.html", {"error": "Invalid credentials"})
    return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect("home")