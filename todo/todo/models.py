from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


# ─────────────────────────────────────────
#  USER PROFILE  (streak tracker)
# ─────────────────────────────────────────

class UserProfile(models.Model):
    user             = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    current_streak   = models.PositiveIntegerField(default=0)
    longest_streak   = models.PositiveIntegerField(default=0)
    last_active_date = models.DateField(null=True, blank=True)
    total_completed  = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} — streak {self.current_streak}"

    def update_streak(self):
        """Call this every time user completes a task."""
        today = timezone.now().date()
        if self.last_active_date == today:
            # already counted today, just bump total
            self.total_completed += 1
            self.save()
            return
        if self.last_active_date == today - timedelta(days=1):
            self.current_streak += 1
        else:
            self.current_streak = 1  # streak broken
        self.last_active_date = today
        self.longest_streak   = max(self.longest_streak, self.current_streak)
        self.total_completed += 1
        self.save()

    def break_streak_if_needed(self):
        """Call on page load to auto-break streak if user missed a day."""
        today = timezone.now().date()
        if self.last_active_date and self.last_active_date < today - timedelta(days=1):
            self.current_streak = 0
            self.save()


# ─────────────────────────────────────────
#  MAIN TASK MODEL
# ─────────────────────────────────────────

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
    description = models.TextField(blank=True, default="")   # Markdown supported
    completed   = models.BooleanField(default=False)
    priority    = models.CharField(max_length=4,  choices=PRIORITY_CHOICES, default="med")
    label       = models.CharField(max_length=20, choices=LABEL_CHOICES,    default="", blank=True)
    due_date    = models.DateField(null=True, blank=True)
    pinned      = models.BooleanField(default=False)
    recur_type  = models.CharField(max_length=10, choices=RECUR_CHOICES, default="", blank=True)
    data        = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
    user        = models.ForeignKey(User, on_delete=models.CASCADE)

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
        """Create next occurrence when this recurring task is completed."""
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


# ─────────────────────────────────────────
#  SUBTASK
# ─────────────────────────────────────────

class SubTask(models.Model):
    todo      = models.ForeignKey(TODOO, on_delete=models.CASCADE, related_name="subtasks")
    title     = models.CharField(max_length=200)
    completed = models.BooleanField(default=False)
    order     = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{'✓' if self.completed else '○'} {self.title}"