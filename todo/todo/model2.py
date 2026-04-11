# ============================================================
#  MODEL 2 — SubTask
#  Feature: Checklist items inside a task.
#           Each TODOO can have many SubTask rows.
#           Rendered as a mini checklist in the expand panel.
# ============================================================

from django.db import models
from .model1 import TODOO


class SubTask(models.Model):

    todo      = models.ForeignKey(TODOO, on_delete=models.CASCADE, related_name="subtasks")
    title     = models.CharField(max_length=200)
    completed = models.BooleanField(default=False)
    order     = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{'✓' if self.completed else '○'} {self.title}"