# ============================================================
#  MODEL 4 — TaskHistory
#  Feature: Deadline Prediction (ML)
#  Purpose: Every time a task is completed, we record how
#           many days it actually took. scikit-learn learns
#           from this history to predict future deadlines.
#
#  Run after adding this:
#      python manage.py makemigrations
#      python manage.py migrate
# ============================================================

from django.db import models
from django.contrib.auth.models import User
from .model1 import TODOO


class TaskHistory(models.Model):
    """
    One row is inserted every time a task is completed.
    The ML model in view7.py trains on these rows to learn
    how long tasks take per (priority, label) combination.
    """

    PRIORITY_CHOICES = [
        ("low",  "Low"),
        ("med",  "Medium"),
        ("high", "High"),
    ]
    LABEL_CHOICES = [
        ("",         "None"),
        ("work",     "Work"),
        ("personal", "Personal"),
        ("urgent",   "Urgent"),
        ("health",   "Health"),
        ("finance",  "Finance"),
    ]

    user          = models.ForeignKey(User, on_delete=models.CASCADE, related_name="task_history")
    task          = models.ForeignKey(TODOO, on_delete=models.SET_NULL, null=True, blank=True)
    title         = models.CharField(max_length=200)
    priority      = models.CharField(max_length=4,  choices=PRIORITY_CHOICES, default="med")
    label         = models.CharField(max_length=20, choices=LABEL_CHOICES,    default="", blank=True)
    days_taken    = models.PositiveIntegerField()   # actual days from creation to completion
    completed_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-completed_at"]

    def __str__(self):
        return f"{self.title} — {self.days_taken}d ({self.priority}, {self.label or 'no label'})"