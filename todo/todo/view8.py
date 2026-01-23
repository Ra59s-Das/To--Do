# ============================================================
#  VIEW 8 — Voice-to-Task (OpenAI Whisper)
#  Feature: User records voice in browser → Whisper transcribes
#           → Claude extracts task titles → tasks are bulk-added.
#
#  Setup:
#      pip install openai
#      Add to settings.py:
#          OPENAI_API_KEY = 'sk-...'
#
#  How it works:
#      1. Browser records audio via MediaRecorder API (webm/mp4).
#      2. JS POSTs the audio blob to /voice-to-task/.
#      3. view8 sends it to Whisper → gets transcript text.
#      4. Claude reads the transcript and extracts a list of tasks.
#      5. All extracted tasks are bulk-created in the database.
#      6. Returns JSON list of created task titles.
#
#  URL (add to urls.py):
#      path("voice-to-task/", views.voice_to_task, name="voice_to_task"),
#
#  Frontend: add the voice button to todo.html (see bottom of this file)
# ============================================================

import json
import urllib.request
import tempfile
import os

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from .model1 import TODOO


def _get_openai_key():
    return getattr(settings, "OPENAI_API_KEY", "")


def _get_anthropic_key():
    return getattr(settings, "ANTHROPIC_API_KEY", "")


def _transcribe_with_whisper(audio_bytes, filename="audio.webm"):
    """
    Send audio bytes to OpenAI Whisper API.
    Returns transcript string.
    """
    import urllib.request
    import urllib.parse

    # Write to temp file (Whisper needs a file)
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        import openai
        client = openai.OpenAI(api_key=_get_openai_key())
        with open(tmp_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="text",
            )
        return transcript.strip()
    finally:
        os.unlink(tmp_path)


def _extract_tasks_with_claude(transcript):
    """
    Send transcript to Claude.
    Returns a list of task dicts:
    [{"title": "...", "priority": "med", "label": "work"}, ...]
    """
    prompt = f"""The following is a voice transcript of someone describing tasks they need to do.
Extract every distinct task mentioned. For each task:
- title: clear, concise task title (max 100 chars)
- priority: "high", "med", or "low" based on words like urgent/asap/important
- label: "work", "personal", "urgent", "health", "finance", or "" based on context

Transcript: "{transcript}"

Respond ONLY with a JSON array. Example:
[
  {{"title": "Fix the login bug", "priority": "high", "label": "work"}},
  {{"title": "Buy groceries", "priority": "low", "label": "personal"}}
]
If no tasks found, return an empty array: []"""

    payload = json.dumps({
        "model":      "claude-sonnet-4-6",
        "max_tokens": 500,
        "messages":   [{"role": "user", "content": prompt}],
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "content-type":      "application/json",
            "anthropic-version": "2023-06-01",
            "x-api-key":         _get_anthropic_key(),
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())

    text = data["content"][0]["text"].strip()

    # Strip markdown fences if present
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]

    tasks = json.loads(text.strip())
    return tasks if isinstance(tasks, list) else []


@login_required
@require_POST
def voice_to_task(request):
    """
    POST: multipart/form-data with field 'audio' (audio file blob)
    Returns: { "transcript": "...", "tasks": [...], "count": N }
    """
    try:
        audio_file = request.FILES.get("audio")
        if not audio_file:
            return JsonResponse({"error": "No audio file received"}, status=400)

        audio_bytes = audio_file.read()
        if len(audio_bytes) < 100:
            return JsonResponse({"error": "Audio too short"}, status=400)

        # Step 1: Transcribe with Whisper
        transcript = _transcribe_with_whisper(audio_bytes)

        if not transcript:
            return JsonResponse({"error": "Could not transcribe audio"}, status=400)

        # Step 2: Extract tasks with Claude
        extracted = _extract_tasks_with_claude(transcript)

        if not extracted:
            return JsonResponse({
                "transcript": transcript,
                "tasks":      [],
                "count":      0,
                "message":    "No tasks detected in transcript.",
            })

        # Step 3: Bulk create tasks in database
        created_tasks = []
        for t in extracted:
            title    = t.get("title", "").strip()
            priority = t.get("priority", "med")
            label    = t.get("label", "")

            if not title:
                continue
            if priority not in ("low", "med", "high"):
                priority = "med"

            task = TODOO.objects.create(
                title=title,
                priority=priority,
                label=label,
                user=request.user,
            )
            created_tasks.append({
                "srno":     task.srno,
                "title":    task.title,
                "priority": task.priority,
                "label":    task.label,
            })

        return JsonResponse({
            "transcript": transcript,
            "tasks":      created_tasks,
            "count":      len(created_tasks),
            "message":    f"{len(created_tasks)} task{'s' if len(created_tasks) != 1 else ''} created from your voice.",
        })

    except ImportError:
        return JsonResponse({
            "error": "openai package not installed. Run: pip install openai"
        }, status=500)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ============================================================
#  FRONTEND SNIPPET
#  Add this button + script to your todo.html
#  Place the button anywhere in the toolbar area:
#
#  <!-- Voice button -->
#  <button class="btn-g" id="voice-btn" onclick="startVoice()" title="Voice to task">
#    <svg viewBox="0 0 13 13" fill="none" width="12" height="12">
#      <rect x="4.5" y="1" width="4" height="7" rx="2" stroke="currentColor" stroke-width="1.3"/>
#      <path d="M2 6.5A4.5 4.5 0 0011 6.5M6.5 11v1.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
#    </svg>
#    Voice
#  </button>
#
#  <!-- Voice status bar (hidden until recording) -->
#  <div id="voice-bar" style="display:none;align-items:center;gap:10px;
#       background:rgba(139,92,246,.08);border:1px solid rgba(139,92,246,.2);
#       border-radius:10px;padding:8px 14px;margin-top:8px">
#    <div id="voice-dot" style="width:8px;height:8px;border-radius:50%;
#         background:rgba(220,50,50,.8);animation:pulse-dot 1s infinite"></div>
#    <span id="voice-status" style="font-size:12px;color:rgba(167,139,250,.8);flex:1">
#      Recording... speak your tasks
#    </span>
#    <button onclick="stopVoice()" style="padding:4px 12px;border-radius:6px;
#            font-size:11px;font-weight:700;color:rgba(167,139,250,.9);
#            background:rgba(139,92,246,.2);border:1px solid rgba(139,92,246,.3);
#            cursor:pointer">Stop</button>
#  </div>
#
#  <!-- Add this <script> block at bottom of todo.html -->
#  <script>
#  let mediaRec = null, audioChunks = [];
#
#  async function startVoice() {
#    try {
#      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
#      audioChunks = [];
#      mediaRec = new MediaRecorder(stream);
#      mediaRec.ondataavailable = e => audioChunks.push(e.data);
#      mediaRec.onstop = sendVoice;
#      mediaRec.start();
#      document.getElementById('voice-bar').style.display = 'flex';
#      document.getElementById('voice-btn').style.opacity = '0.4';
#    } catch(e) {
#      alert('Microphone access denied. Please allow microphone in browser settings.');
#    }
#  }
#
#  function stopVoice() {
#    if (mediaRec && mediaRec.state !== 'inactive') {
#      mediaRec.stop();
#      mediaRec.stream.getTracks().forEach(t => t.stop());
#    }
#    document.getElementById('voice-status').textContent = 'Processing...';
#  }
#
#  async function sendVoice() {
#    const blob = new Blob(audioChunks, { type: 'audio/webm' });
#    const form = new FormData();
#    form.append('audio', blob, 'recording.webm');
#    try {
#      const resp = await fetch('/voice-to-task/', {
#        method: 'POST',
#        headers: { 'X-CSRFToken': getCsrf() },
#        body: form
#      });
#      const data = await resp.json();
#      document.getElementById('voice-bar').style.display = 'none';
#      document.getElementById('voice-btn').style.opacity = '1';
#      if (data.error) { showToast('Error: ' + data.error); return; }
#      showToast('✓ ' + data.message);
#      setTimeout(() => location.reload(), 1200);
#    } catch(e) {
#      showToast('Voice error: ' + e.message);
#    }
#  }
#  </script>
# ============================================================