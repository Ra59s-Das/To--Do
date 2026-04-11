# ============================================================
#  VIEW 3 — Subtasks / Checklist
#  Feature: add checklist items to a task,
#           toggle them complete, delete them
#  URLs:    /add-subtask/<id>/  /toggle-subtask/<pk>/  etc.
#  Depends: model1.py (TODOO), model2.py (SubTask)
# ============================================================

from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .model1 import TODOO
from .model2 import SubTask


@login_required
def add_subtask(request, srno):
    if request.method == "POST":
        task  = get_object_or_404(TODOO, srno=srno, user=request.user)
        title = request.POST.get("subtask_title", "").strip()
        if title:
            SubTask.objects.create(
                todo=task,
                title=title,
                order=task.subtasks.count(),
            )
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