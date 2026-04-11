# ============================================================
#  VIEW 5 — AI Smart Suggestions
#  Feature: POST /ai-suggest/
#           Sends task title to Claude, returns suggested
#           priority, label, due_days, and reason.
#  URL:     /ai-suggest/
#  Requires: ANTHROPIC_API_KEY in settings.py
#  Depends: No models — pure API call
# ============================================================

import json
import urllib.request

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.conf import settings


def _get_api_key():
    return getattr(settings, "ANTHROPIC_API_KEY", "")


@login_required
@require_POST
def ai_suggest(request):
    """
    POST body : { "title": "Fix the login bug" }
    Response  : { "priority": "high", "label": "work",
                  "due_days": 2, "reason": "..." }
    """
    try:
        body  = json.loads(request.body)
        title = body.get("title", "").strip()

        if not title:
            return JsonResponse({"error": "No title provided"}, status=400)

        prompt = f"""You are a smart productivity assistant. Given a task title, suggest:
1. priority: one of "high", "med", "low"
2. label: one of "work", "personal", "urgent", "health", "finance", or ""
3. due_days: number of days from today (1-30), or null if no clear deadline
4. reason: one short sentence explaining your suggestion

Task title: "{title}"

Respond ONLY with a JSON object, no markdown, no extra text. Example:
{{"priority":"high","label":"work","due_days":3,"reason":"Sounds time-sensitive and work-related."}}"""

        payload = json.dumps({
            "model":      "claude-sonnet-4-6",
            "max_tokens": 200,
            "messages":   [{"role": "user", "content": prompt}],
        }).encode()

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "content-type":      "application/json",
                "anthropic-version": "2023-06-01",
                "x-api-key":         _get_api_key(),
            },
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())

        text = data["content"][0]["text"].strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]

        return JsonResponse(json.loads(text.strip()))

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)