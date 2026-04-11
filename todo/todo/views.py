# ============================================================
#  views.py — Import Hub
#
#  DO NOT put view logic here.
#  This file just imports from view1–view5
#  so urls.py can keep doing `from . import views`
#
#  Feature map:
#    view1.py  →  Auth            (home, signup, login, logout)
#    view2.py  →  Task CRUD       (todo page, add/edit/delete/pin/bulk)
#    view3.py  →  Subtasks        (add/toggle/delete checklist items)
#    view4.py  →  Analytics       (/analytics/ dashboard)
#    view5.py  →  AI Suggestions  (/ai-suggest/ API endpoint)
# ============================================================

from .view1 import home, signup, login_view, logout_view
from .view2 import (
    todo_view, add_task, toggle_task, edit_task,
    delete_task, toggle_pin, bulk_delete, clear_completed,
)
from .view3 import add_subtask, toggle_subtask, delete_subtask
from .view4 import analytics_view
from .view5 import ai_suggest