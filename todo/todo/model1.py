# ============================================================
#  MODEL 1 — Core Task (TODOO)
#  Feature: Task management with priority, labels, due dates,
#           pinning, recurring, and markdown description
# ============================================================

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class TODOO(models.Model):

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
    RECUR_CHOICES = [
        ("",        "None"),
        ("daily",   "Daily"),
        ("weekly",  "Weekly"),
        ("monthly", "Monthly"),
    ]

    srno        = models.AutoField(primary_key=True)
    title       = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")  # supports Markdown
    completed   = models.BooleanField(default=False)
    priority    = models.CharField(max_length=4,  choices=PRIORITY_CHOICES, default="med")
    label       = models.CharField(max_length=20, choices=LABEL_CHOICES,    default="", blank=True)
    due_date    = models.DateField(null=True, blank=True)
    pinned      = models.BooleanField(default=False)
    recur_type  = models.CharField(max_length=10, choices=RECUR_CHOICES,    default="", blank=True)
    data        = models.DateTimeField(auto_now_add=True)   # created_at
    updated_at  = models.DateTimeField(auto_now=True)
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tasks")

    class Meta:
        ordering = ["-pinned", "completed", "-priority", "-data"]

    def __str__(self):
        return f"{'✓' if self.completed else '○'} {self.title}"

    @property
    def is_overdue(self):
        if self.due_date and not self.completed:
            return self.due_date < timezone.now().date()
        return False

    @property
    def is_due_today(self):
        if self.due_date and not self.completed:
            return self.due_date == timezone.now().date()
        return False

    @property
    def subtasks_done_count(self):
        return self.subtasks.filter(completed=True).count()

    def get_next_recur_date(self):
        base = self.due_date or timezone.now().date()
        if self.recur_type == "daily":
            return base + timedelta(days=1)
        elif self.recur_type == "weekly":
            return base + timedelta(weeks=1)
        elif self.recur_type == "monthly":
            month = base.month + 1
            year  = base.year + (1 if month > 12 else 0)
            month = month if month <= 12 else 1
            return base.replace(year=year, month=month)
        return None

    def spawn_recurrence(self):
        """When a recurring task is completed, auto-create the next one."""
        next_date = self.get_next_recur_date()
        if next_date:
            TODOO.objects.create(
                title=self.title,
                description=self.description,
                priority=self.priority,
                label=self.label,
                due_date=next_date,
                recur_type=self.recur_type,
                pinned=self.pinned,
                user=self.user,
            )