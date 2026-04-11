# ============================================================
#  VIEW 4 — Productivity Analytics
#  Feature: /analytics/ dashboard page
#           14-day chart, label breakdown, priority breakdown,
#           weekly completion ring, streak stats
#  URL:     /analytics/
#  Depends: model1.py (TODOO), model3.py (UserProfile)
# ============================================================

import json
from datetime import timedelta

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .model1 import TODOO
from .model3 import UserProfile


def _get_or_create_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


@login_required
def analytics_view(request):
    profile   = _get_or_create_profile(request.user)
    today     = timezone.now().date()
    all_tasks = TODOO.objects.filter(user=request.user)

    # Last 14 days — tasks completed per day
    last_14 = []
    for i in range(13, -1, -1):
        d     = today - timedelta(days=i)
        count = all_tasks.filter(completed=True, updated_at__date=d).count()
        last_14.append({"date": d.strftime("%b %d"), "count": count})

    # Label breakdown
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

    # This week completion rate
    week_start = today - timedelta(days=today.weekday())
    this_week  = all_tasks.filter(data__date__gte=week_start)
    week_total = this_week.count()
    week_done  = this_week.filter(completed=True).count()
    week_rate  = round(week_done / week_total * 100) if week_total else 0

    context = {
        "profile":       profile,
        "last_14":       json.dumps(last_14),
        "label_data":    json.dumps(label_data),
        "priority_data": json.dumps(priority_data),
        "week_rate":     week_rate,
        "week_done":     week_done,
        "week_total":    week_total,
        "overdue":       all_tasks.filter(completed=False, due_date__lt=today).count(),
        "total":         all_tasks.count(),
        "completed":     all_tasks.filter(completed=True).count(),
    }
    return render(request, "analytics.html", context)