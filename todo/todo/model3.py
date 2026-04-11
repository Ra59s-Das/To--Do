# ============================================================
#  MODEL 3 — UserProfile
#  Feature: Daily Streak Tracker
#           One profile per user. Tracks current streak,
#           longest streak, last active date, total completed.
# ============================================================

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class UserProfile(models.Model):

    user             = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    current_streak   = models.PositiveIntegerField(default=0)
    longest_streak   = models.PositiveIntegerField(default=0)
    last_active_date = models.DateField(null=True, blank=True)
    total_completed  = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} — streak {self.current_streak}"

    def update_streak(self):
        """Call every time a user completes a task."""
        today = timezone.now().date()
        if self.last_active_date == today:
            # Already counted today — just bump total
            self.total_completed += 1
            self.save()
            return
        if self.last_active_date == today - timedelta(days=1):
            self.current_streak += 1   # consecutive day — extend
        else:
            self.current_streak = 1    # gap in days — reset to 1
        self.last_active_date = today
        self.longest_streak   = max(self.longest_streak, self.current_streak)
        self.total_completed += 1
        self.save()

    def break_streak_if_needed(self):
        """Call on every page load to auto-reset streak if a day was missed."""
        today = timezone.now().date()
        if self.last_active_date and self.last_active_date < today - timedelta(days=1):
            self.current_streak = 0
            self.save()