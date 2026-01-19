# ============================================================
#  VIEW 2 — Core Task Management
#  Feature: todo list page, add, edit, delete, toggle,
#           pin/unpin, bulk delete, clear completed
#  URLs:    /todo/  /add-task/  /edit-task/<id>/  etc.
# ============================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .model1 import TODOO
from .model3 import UserProfile



def _get_or_create_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


@login_required
def todo_view(request):
    profile = _get_or_create_profile(request.user)
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

    all_tasks = TODOO.objects.filter(user=request.user)
    context = {
        "tasks":           tasks,
        "filter":          filter_type,
        "search_query":    search_query,
        "sort_by":         sort_by,
        "label_filter":    label_filter,
        "total_count":     all_tasks.count(),
        "completed_count": all_tasks.filter(completed=True).count(),
        "active_count":    all_tasks.filter(completed=False).count(),
        "high_count":      all_tasks.filter(priority="high", completed=False).count(),
        "overdue_count":   all_tasks.filter(completed=False, due_date__lt=timezone.now().date()).count(),
        "today_count":     all_tasks.filter(completed=False, due_date=timezone.now().date()).count(),
        "pinned_count":    all_tasks.filter(pinned=True).count(),
        "recurring_count": all_tasks.exclude(recur_type="").filter(completed=False).count(),
        "label_choices":   TODOO.LABEL_CHOICES,
        "recur_choices":   TODOO.RECUR_CHOICES,
        "today":           timezone.now().date(),
        "streak":          profile.current_streak,
        "longest_streak":  profile.longest_streak,
        "total_completed": profile.total_completed,
    }
    return render(request, "todo.html", context)


@login_required
def add_task(request):
    if request.method == "POST":
        title    = request.POST.get("title", "").strip()
        priority = request.POST.get("priority", "med")
        if priority not in ("low", "med", "high"):
            priority = "med"
        if title:
            TODOO.objects.create(
                title=title,
                description=request.POST.get("description", "").strip(),
                priority=priority,
                label=request.POST.get("label", ""),
                due_date=request.POST.get("due_date", "") or None,
                recur_type=request.POST.get("recur_type", ""),
                pinned=bool(request.POST.get("pinned")),
                user=request.user,
            )
    return redirect("todo")


@login_required
def toggle_task(request, srno):
    if request.method == "POST":
        task = get_object_or_404(TODOO, srno=srno, user=request.user)
        task.completed = not task.completed
        task.save()
        if task.completed:
            _get_or_create_profile(request.user).update_streak()  # view2 → model3
            if task.recur_type:
                task.spawn_recurrence()                            # view2 → model1
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
def bulk_delete(request):
    if request.method == "POST":
        ids = request.POST.getlist("task_ids")
        if ids:
            TODOO.objects.filter(user=request.user, srno__in=ids).delete()
    return redirect(request.META.get("HTTP_REFERER", "todo"))


@login_required
def clear_completed(request):
    if request.method == "POST":
        TODOO.objects.filter(user=request.user, completed=True).delete()
    return redirect("todo")