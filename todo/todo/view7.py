# ============================================================
#  VIEW 7 — Deadline Prediction (ML)
#  Feature: Predicts how many days a task will take based on
#           its priority and label, trained on TaskHistory.
#
#  Setup:
#      pip install scikit-learn
#
#  How it works:
#      1. On task completion, view2.toggle_task calls
#         record_task_completion() to save history.
#      2. POST /predict-deadline/ returns predicted days
#         which the frontend shows as a suggested due date.
#      3. Model trains fresh each call (fast for small data).
#         Falls back to rule-based defaults if < 5 data points.
#
#  URLs (add to urls.py):
#      path("predict-deadline/", views.predict_deadline, name="predict_deadline"),
#      path("record-completion/<int:srno>/", views.record_completion, name="record_completion"),
# ============================================================

import json
from datetime import timedelta

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone

from .model1 import TODOO
from .model4 import TaskHistory


# ── Rule-based fallback (used when not enough history) ────────────
FALLBACK_DAYS = {
    ("high", "urgent"):   1,
    ("high", "work"):     2,
    ("high", ""):         2,
    ("med",  "work"):     4,
    ("med",  "personal"): 5,
    ("med",  ""):         4,
    ("low",  "personal"): 7,
    ("low",  "health"):   7,
    ("low",  ""):         7,
}
DEFAULT_DAYS = 3


def _fallback_prediction(priority, label):
    return FALLBACK_DAYS.get((priority, label),
           FALLBACK_DAYS.get((priority, ""), DEFAULT_DAYS))


def _encode(priority, label):
    """One-hot encode priority + label for scikit-learn."""
    priorities = ["low", "med", "high"]
    labels     = ["", "work", "personal", "urgent", "health", "finance"]
    p_vec = [1 if priority == p else 0 for p in priorities]
    l_vec = [1 if label    == l else 0 for l in labels]
    return p_vec + l_vec


def _train_and_predict(user, priority, label):
    """
    Train a Ridge regression model on the user's TaskHistory
    and return predicted days for the given priority + label.
    Falls back to rule-based if fewer than 5 history rows.
    """
    try:
        from sklearn.linear_model import Ridge

        history = TaskHistory.objects.filter(user=user)
        if history.count() < 5:
            return _fallback_prediction(priority, label), False

        X = [_encode(h.priority, h.label) for h in history]
        y = [h.days_taken for h in history]

        model = Ridge(alpha=1.0)
        model.fit(X, y)

        prediction = model.predict([_encode(priority, label)])[0]
        days = max(1, round(prediction))
        return days, True

    except ImportError:
        # scikit-learn not installed — fall back to rule-based
        return _fallback_prediction(priority, label), False
    except Exception:
        return _fallback_prediction(priority, label), False


# ── Record completion (called from view2.toggle_task) ─────────────

def record_task_completion(user, task):
    """
    Call this from view2.toggle_task when task.completed becomes True.
    Records actual days taken so ML model can learn from it.

    Add this to view2.py toggle_task():
        from .view7 import record_task_completion
        if task.completed:
            record_task_completion(request.user, task)
    """
    created = task.data.date() if hasattr(task.data, 'date') else task.data
    today   = timezone.now().date()
    days    = max(1, (today - created).days or 1)

    TaskHistory.objects.create(
        user=user,
        task=task,
        title=task.title,
        priority=task.priority,
        label=task.label,
        days_taken=days,
    )


# ── API endpoint ──────────────────────────────────────────────────

@login_required
@require_POST
def predict_deadline(request):
    """
    POST body : { "priority": "high", "label": "work" }
    Response  : { "days": 2, "due_date": "2026-04-13",
                  "ml_trained": true, "message": "..." }
    """
    try:
        body     = json.loads(request.body)
        priority = body.get("priority", "med")
        label    = body.get("label", "")

        if priority not in ("low", "med", "high"):
            priority = "med"

        days, ml_trained = _train_and_predict(request.user, priority, label)
        due_date = (timezone.now().date() + timedelta(days=days)).isoformat()

        history_count = TaskHistory.objects.filter(user=request.user).count()

        return JsonResponse({
            "days":          days,
            "due_date":      due_date,
            "ml_trained":    ml_trained,
            "history_count": history_count,
            "message": (
                f"Based on your {history_count} completed tasks, "
                f"this usually takes about {days} day{'s' if days != 1 else ''}."
                if ml_trained else
                f"Suggested {days} day{'s' if days != 1 else ''} "
                f"(need 5+ completed tasks to train your personal model — "
                f"you have {history_count} so far)."
            )
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)