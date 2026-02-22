from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login


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

        if User.objects.filter(email=email).exists():  # Add this check
            return render(request, "signup.html", {"error": "Email already registered. Please log in."})

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        login(request, user)
        return redirect("login/")  # Or wherever you want post-signup

    return render(request, "signup.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("/")
        return render(request, "login.html", {"error": "Invalid credentials"})
    return render(request, "login.html")
