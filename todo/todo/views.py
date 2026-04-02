import json
import urllib.request
import urllib.error
from datetime import timedelta, date
from collections import defaultdict

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from .models import TODOO, SubTask, UserProfile


# ─────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────

def get_or_create_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


# ─────────────────────────────────────────
#  AUTH
# ─────────────────────────────────────────

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
        get_or_create_profile(user)
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


# ─────────────────────────────────────────
#  MAIN TODO VIEW
# ─────────────────────────────────────────

@login_required
def todo_view(request):
    profile = get_or_create_profile(request.user)
    profile.break_streak_if_needed()

    filter_type  = request.GET.get("filter", "all")
    search_query = request.GET.get("q", "").strip()
    sort_by      = request.GET.get("sort", "default")
    label_filter = request.GET.get("label", "")

    tasks = TODOO.objects.filter(user=request.user).prefetch_related("subtasks")

    if search_query:
        tasks = tasks.filter(title__icontains=search_query)
    if label_filter:
        tasks = tasks.filter(label=label_filter)

    if filter_type == "active":
        tasks = tasks.filter(completed=False)
    elif filter_type == "completed":
        tasks = tasks.filter(completed=True)
    elif filter_type == "high":
        tasks = tasks.filter(priority="high", completed=False)
    elif filter_type == "overdue":
        tasks = tasks.filter(completed=False, due_date__lt=timezone.now().date())
    elif filter_type == "today":
        tasks = tasks.filter(completed=False, due_date=timezone.now().date())
    elif filter_type == "pinned":
        tasks = tasks.filter(pinned=True)
    elif filter_type == "recurring":
        tasks = tasks.exclude(recur_type="")

    if sort_by == "due":
        tasks = tasks.order_by("-pinned", "completed", "due_date")
    elif sort_by == "priority":
        order = {"high": 0, "med": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (not t.pinned, t.completed, order.get(t.priority, 1)))
    elif sort_by == "created":
        tasks = tasks.order_by("-pinned", "completed", "-data")
    elif sort_by == "az":
        tasks = tasks.order_by("-pinned", "completed", "title")
    else:
        tasks = tasks.order_by("-pinned", "completed", "-priority", "-data")

    all_tasks       = TODOO.objects.filter(user=request.user)
    total_count     = all_tasks.count()
    completed_count = all_tasks.filter(completed=True).count()
    active_count    = total_count - completed_count
    high_count      = all_tasks.filter(priority="high", completed=False).count()
    overdue_count   = all_tasks.filter(completed=False, due_date__lt=timezone.now().date()).count()
    today_count     = all_tasks.filter(completed=False, due_date=timezone.now().date()).count()
    pinned_count    = all_tasks.filter(pinned=True).count()
    recurring_count = all_tasks.exclude(recur_type="").filter(completed=False).count()

    context = {
        "tasks":           tasks,
        "filter":          filter_type,
        "search_query":    search_query,
        "sort_by":         sort_by,
        "label_filter":    label_filter,
        "total_count":     total_count,
        "completed_count": completed_count,
        "active_count":    active_count,
        "high_count":      high_count,
        "overdue_count":   overdue_count,
        "today_count":     today_count,
        "pinned_count":    pinned_count,
        "recurring_count": recurring_count,
        "label_choices":   TODOO.LABEL_CHOICES,
        "recur_choices":   TODOO.RECUR_CHOICES,
        "today":           timezone.now().date(),
        # streak
        "streak":          profile.current_streak,
        "longest_streak":  profile.longest_streak,
        "total_completed": profile.total_completed,
    }
    return render(request, "todo.html", context)


# ─────────────────────────────────────────
#  TASK CRUD
# ─────────────────────────────────────────

@login_required
def add_task(request):
    if request.method == "POST":
        title      = request.POST.get("title", "").strip()
        desc       = request.POST.get("description", "").strip()
        priority   = request.POST.get("priority", "med")
        label      = request.POST.get("label", "")
        due_date   = request.POST.get("due_date", "") or None
        recur_type = request.POST.get("recur_type", "")
        pinned     = bool(request.POST.get("pinned"))

        if priority not in ("low", "med", "high"):
            priority = "med"
        if title:
            TODOO.objects.create(
                title=title, description=desc,
                priority=priority, label=label,
                due_date=due_date, recur_type=recur_type,
                pinned=pinned, user=request.user,
            )
    return redirect("todo")


@login_required
def toggle_task(request, srno):
    if request.method == "POST":
        task = get_object_or_404(TODOO, srno=srno, user=request.user)
        task.completed = not task.completed
        task.save()

        if task.completed:
            # Update streak
            profile = get_or_create_profile(request.user)
            profile.update_streak()
            # Spawn recurrence if needed
            if task.recur_type:
                task.spawn_recurrence()

    return redirect(request.META.get("HTTP_REFERER", "todo"))


@login_required
def edit_task(request, srno):
    if request.method == "POST":
        task = get_object_or_404(TODOO, srno=srno, user=request.user)
        title = request.POST.get("title", "").strip()
        if title:
            task.title = title
        task.description = request.POST.get("description", "").strip()
        priority = request.POST.get("priority", task.priority)
        if priority in ("low", "med", "high"):
            task.priority = priority
        task.label      = request.POST.get("label", "")
        task.due_date   = request.POST.get("due_date", "") or None
        task.recur_type = request.POST.get("recur_type", "")
        task.pinned     = bool(request.POST.get("pinned"))
        task.save()
    return redirect(request.META.get("HTTP_REFERER", "todo"))


@login_required
def delete_task(request, srno):
    if request.method == "POST":
        get_object_or_404(TODOO, srno=srno, user=request.user).delete()
    return redirect(request.META.get("HTTP_REFERER", "todo"))


@login_required
def toggle_pin(request, srno):
    if request.method == "POST":
        task = get_object_or_404(TODOO, srno=srno, user=request.user)
        task.pinned = not task.pinned
        task.save()
    return redirect(request.META.get("HTTP_REFERER", "todo"))


@login_required
def clear_completed(request):
    if request.method == "POST":
        TODOO.objects.filter(user=request.user, completed=True).delete()
    return redirect("todo")


@login_required
def bulk_delete(request):
    if request.method == "POST":
        ids = request.POST.getlist("task_ids")
        if ids:
            TODOO.objects.filter(user=request.user, srno__in=ids).delete()
    return redirect(request.META.get("HTTP_REFERER", "todo"))


# ─────────────────────────────────────────
#  SUBTASKS
# ─────────────────────────────────────────

@login_required
def add_subtask(request, srno):
    if request.method == "POST":
        task  = get_object_or_404(TODOO, srno=srno, user=request.user)
        title = request.POST.get("subtask_title", "").strip()
        if title:
            SubTask.objects.create(todo=task, title=title, order=task.subtasks.count())
    return redirect(request.META.get("HTTP_REFERER", "todo"))


@login_required
def toggle_subtask(request, pk):
    if request.method == "POST":
        sub = get_object_or_404(SubTask, pk=pk, todo__user=request.user)
        sub.completed = not sub.completed
        sub.save()
    return redirect(request.META.get("HTTP_REFERER", "todo"))


@login_required
def delete_subtask(request, pk):
    if request.method == "POST":
        get_object_or_404(SubTask, pk=pk, todo__user=request.user).delete()
    return redirect(request.META.get("HTTP_REFERER", "todo"))


# ─────────────────────────────────────────
#  ★ ANALYTICS PAGE
# ─────────────────────────────────────────

@login_required
def analytics_view(request):
    profile = get_or_create_profile(request.user)
    today   = timezone.now().date()

    # Last 14 days completed per day
    last_14 = []
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        count = TODOO.objects.filter(
            user=request.user,
            completed=True,
            updated_at__date=d,
        ).count()
        last_14.append({"date": d.strftime("%b %d"), "count": count})

    # Label breakdown
    all_tasks = TODOO.objects.filter(user=request.user)
    label_data = {}
    for val, name in TODOO.LABEL_CHOICES:
        if val:
            c = all_tasks.filter(label=val).count()
            if c:
                label_data[name] = c

    # Priority breakdown
    priority_data = {
        "High":   all_tasks.filter(priority="high").count(),
        "Medium": all_tasks.filter(priority="med").count(),
        "Low":    all_tasks.filter(priority="low").count(),
    }

    # Completion rate this week
    week_start  = today - timedelta(days=today.weekday())
    this_week   = all_tasks.filter(data__date__gte=week_start)
    week_total  = this_week.count()
    week_done   = this_week.filter(completed=True).count()
    week_rate   = round(week_done / week_total * 100) if week_total else 0

    # Overdue count
    overdue = all_tasks.filter(completed=False, due_date__lt=today).count()

    context = {
        "profile":       profile,
        "last_14":       json.dumps(last_14),
        "label_data":    json.dumps(label_data),
        "priority_data": json.dumps(priority_data),
        "week_rate":     week_rate,
        "week_done":     week_done,
        "week_total":    week_total,
        "overdue":       overdue,
        "total":         all_tasks.count(),
        "completed":     all_tasks.filter(completed=True).count(),
    }
    return render(request, "analytics.html", context)


# ─────────────────────────────────────────
#  ★ AI SMART SUGGEST  (Anthropic API)
# ─────────────────────────────────────────

@login_required
@require_POST
def ai_suggest(request):
    """
    POST { "title": "..." }
    Returns { "priority": "high|med|low", "label": "...", "due_days": N, "reason": "..." }
    """
    try:
        body  = json.loads(request.body)
        title = body.get("title", "").strip()
        if not title:
            return JsonResponse({"error": "No title"}, status=400)

        prompt = f"""You are a smart productivity assistant. Given a task title, suggest:
1. priority: one of "high", "med", "low"
2. label: one of "work", "personal", "urgent", "health", "finance", or ""
3. due_days: number of days from today (1-30), or null if no clear deadline
4. reason: one short sentence explaining your suggestion

Task title: "{title}"

Respond ONLY with a JSON object, no markdown, no extra text. Example:
{{"priority":"high","label":"work","due_days":3,"reason":"Sounds time-sensitive and work-related."}}"""

        payload = json.dumps({
            "model": "claude-opus-4-6",
            "max_tokens": 200,
            "messages": [{"role": "user", "content": prompt}]
        }).encode()

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "content-type":      "application/json",
                "anthropic-version": "2023-06-01",
                # API key read from Django settings
                "x-api-key":         _get_api_key(),
            },
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())

        text = data["content"][0]["text"].strip()
        # Strip markdown fences if model adds them
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        suggestion = json.loads(text)
        return JsonResponse(suggestion)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def _get_api_key():
    """Read ANTHROPIC_API_KEY from Django settings (set in settings.py)."""
    from django.conf import settings
    return getattr(settings, "ANTHROPIC_API_KEY", "")