from __future__ import annotations

import io
import json
import urllib.error
import urllib.request
import webbrowser
from contextlib import redirect_stdout
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable
from urllib.parse import urlparse

from tof_cli.commands import check, doctor, down, setup, status, up


@dataclass(frozen=True)
class ActionSpec:
    label: str
    handler: Callable[..., int]
    kwargs: dict[str, object]
    safe_level: str


ACTIONS = {
    "setup": ActionSpec("Prepare local setup", setup.handle, {}, "SAFE"),
    "up": ActionSpec("Start stack", up.handle, {"build": True}, "SAFE"),
    "check": ActionSpec("Check services", check.handle, {}, "SAFE"),
    "status": ActionSpec("Show runtime status", status.handle, {}, "SAFE"),
    "doctor": ActionSpec("Run doctor", doctor.handle, {}, "SAFE"),
    "down": ActionSpec("Stop stack", down.handle, {"remove_orphans": False}, "SAFE"),
}

LINKS = {
    "openwebui": {"label": "Open WebUI", "url": "http://127.0.0.1:3000"},
    "search_docs": {"label": "Open search API docs", "url": "http://127.0.0.1:8105/docs"},
    "qa_docs": {"label": "Open QA API docs", "url": "http://127.0.0.1:8106/docs"},
    "catalog_docs": {"label": "Open catalog API docs", "url": "http://127.0.0.1:8102/docs"},
}

API_TARGETS = {
    "search": "http://127.0.0.1:8105/search",
    "answer": "http://127.0.0.1:8106/answer",
}


HTML = """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>tof_local_knowledge</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 0; background: #f5f7fb; color: #18212f; }
    .wrap { max-width: 1080px; margin: 0 auto; padding: 24px; }
    .hero, .panel { background: white; border-radius: 16px; padding: 24px; box-shadow: 0 8px 30px rgba(0,0,0,0.06); }
    .panel { margin-top: 20px; }
    .lead { color: #4b5563; line-height: 1.5; }
    .note { color: #6b7280; font-size: 14px; }
    .actions { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 14px; margin-top: 18px; }
    button { border: 0; border-radius: 12px; padding: 14px 16px; font-size: 15px; cursor: pointer; background: #1f6feb; color: white; }
    button.secondary { background: #0f766e; }
    button.ghost { background: #e5e7eb; color: #111827; }
    .status { margin-top: 18px; background: #ecfeff; border: 1px solid #a5f3fc; color: #164e63; border-radius: 14px; padding: 16px; }
    .log, .result { margin-top: 18px; background: #111827; color: #d1fae5; border-radius: 14px; padding: 16px; min-height: 220px; }
    .result { background: white; color: #18212f; min-height: 140px; }
    pre { margin: 0; white-space: pre-wrap; word-break: break-word; }
    h1 { margin-top: 0; }
    textarea, input[type=text], input[type=number] { width: 100%; box-sizing: border-box; border: 1px solid #cbd5e1; border-radius: 8px; padding: 10px; font: inherit; }
    textarea { min-height: 90px; resize: vertical; }
    .form-grid { display: grid; grid-template-columns: 1fr; gap: 12px; margin-top: 14px; }
    .hint { color: #6b7280; font-size: 14px; margin-top: 10px; }
    .two-col { display: grid; grid-template-columns: 1fr; gap: 20px; }
    @media (min-width: 1100px) { .two-col { grid-template-columns: 1fr 1fr; } }
  </style>
</head>
<body>
  <div class=\"wrap\">
    <div class=\"hero\">
      <h1>tof_local_knowledge</h1>
      <p class=\"lead\">A simple local control surface for the knowledge stack. Start the stack, open the main pages, search the local knowledge base, and ask grounded questions.</p>
      <p class=\"note\">This UI is local-only. Search and answer requests stay on your local stack.</p>
    </div>

    <div class=\"panel\">
      <h2>Main actions</h2>
      <div class=\"actions\">
        <button onclick=\"runAction('setup')\">1. Prepare local setup</button>
        <button class=\"secondary\" onclick=\"runAction('up')\">2. Start stack</button>
        <button onclick=\"runAction('check')\">3. Check services</button>
        <button class=\"ghost\" onclick=\"runAction('status')\">Show runtime status</button>
        <button class=\"ghost\" onclick=\"runAction('doctor')\">Run doctor</button>
        <button onclick=\"runAction('down')\">Stop stack</button>
      </div>
      <h3 style=\"margin-top:22px;\">Useful links</h3>
      <div class=\"actions\">
        <button class=\"ghost\" onclick=\"openLink('openwebui')\">Open WebUI</button>
        <button class=\"ghost\" onclick=\"openLink('search_docs')\">Open search API docs</button>
        <button class=\"ghost\" onclick=\"openLink('qa_docs')\">Open QA API docs</button>
        <button class=\"ghost\" onclick=\"openLink('catalog_docs')\">Open catalog API docs</button>
      </div>
      <div class=\"status\" id=\"next-step\">Loading current guidance ...</div>
    </div>

    <div class=\"two-col\">
      <div class=\"panel\">
        <h2>Search the local knowledge base</h2>
        <div class=\"form-grid\">
          <input id=\"search-query\" type=\"text\" placeholder=\"Type search words here\">
          <input id=\"search-scope\" type=\"text\" placeholder=\"Optional source IDs, comma separated\">
          <input id=\"search-limit\" type=\"number\" min=\"1\" max=\"20\" value=\"5\">
          <button class=\"secondary\" onclick=\"runSearch()\">Run search</button>
        </div>
        <div class=\"hint\">Search uses the local `POST /search` endpoint of the running stack.</div>
        <div class=\"result\"><pre id=\"search-result\">No search run yet.</pre></div>
      </div>

      <div class=\"panel\">
        <h2>Ask a grounded question</h2>
        <div class=\"form-grid\">
          <textarea id=\"qa-question\" placeholder=\"Ask a question about your indexed local sources\"></textarea>
          <input id=\"qa-scope\" type=\"text\" placeholder=\"Optional source IDs, comma separated\">
          <input id=\"qa-limit\" type=\"number\" min=\"1\" max=\"10\" value=\"5\">
          <button class=\"secondary\" onclick=\"runAnswer()\">Get grounded answer</button>
        </div>
        <div class=\"hint\">Questions use the local `POST /answer` endpoint of the running stack.</div>
        <div class=\"result\"><pre id=\"qa-result\">No grounded answer run yet.</pre></div>
      </div>
    </div>

    <div class=\"panel\">
      <h2>Activity log</h2>
      <div class=\"log\"><pre id=\"log\">Starting tof_local_knowledge UI...</pre></div>
    </div>
  </div>
  <script>
    function appendLog(text) {
      const log = document.getElementById('log');
      log.textContent = `[${new Date().toLocaleTimeString()}] ${text}\n\n` + log.textContent;
    }

    function parseScope(value) {
      if (!value || !value.trim()) return [];
      return value.split(',').map(v => v.trim()).filter(Boolean);
    }

    async function refreshSummary() {
      const response = await fetch('/api/summary');
      const data = await response.json();
      document.getElementById('next-step').textContent = data.next_step;
      appendLog('Summary refreshed.');
    }

    async function runAction(action) {
      appendLog(`Running ${action} ...`);
      const response = await fetch(`/api/${action}`, { method: 'POST' });
      const data = await response.json();
      appendLog(JSON.stringify(data, null, 2));
      await refreshSummary();
    }

    async function openLink(name) {
      appendLog(`Opening ${name} ...`);
      const response = await fetch(`/api/open/${name}`, { method: 'POST' });
      const data = await response.json();
      appendLog(JSON.stringify(data, null, 2));
    }

    async function runSearch() {
      const payload = {
        query: document.getElementById('search-query').value,
        source_scope: parseScope(document.getElementById('search-scope').value),
        limit: Number(document.getElementById('search-limit').value || 5),
      };
      appendLog('Running local search ...');
      const response = await fetch('/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      document.getElementById('search-result').textContent = JSON.stringify(data, null, 2);
      appendLog('Search finished.');
    }

    async function runAnswer() {
      const payload = {
        question: document.getElementById('qa-question').value,
        source_scope: parseScope(document.getElementById('qa-scope').value),
        limit: Number(document.getElementById('qa-limit').value || 5),
      };
      appendLog('Running grounded answer ...');
      const response = await fetch('/api/answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      document.getElementById('qa-result').textContent = JSON.stringify(data, null, 2);
      appendLog('Grounded answer finished.');
    }

    refreshSummary();
  </script>
</body>
</html>
"""


def _run_action(name: str) -> dict[str, object]:
    spec = ACTIONS[name]
    namespace = type("Args", (), spec.kwargs)()
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        code = spec.handler(namespace)
    output = buffer.getvalue().strip()
    return {
        "action": name,
        "label": spec.label,
        "safe_level": spec.safe_level,
        "exit_code": int(code or 0),
        "output": output,
    }



def _open_link(name: str) -> dict[str, object]:
    link = LINKS[name]
    webbrowser.open(link["url"])
    return {"opened": link["url"], "label": link["label"]}



def _read_json_body(handler: BaseHTTPRequestHandler) -> dict[str, object]:
    length = int(handler.headers.get("Content-Length", "0"))
    raw = handler.rfile.read(length) if length > 0 else b"{}"
    return json.loads(raw.decode("utf-8")) if raw else {}



def _post_json(url: str, payload: dict[str, object]) -> dict[str, object]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        return {"error": f"http_error_{exc.code}", "details": body or str(exc)}
    except Exception as exc:
        return {"error": "request_failed", "details": str(exc)}



def _summary_payload() -> dict[str, object]:
    return {
        "next_step": "Recommended order: prepare local setup, start stack, check services, then use search or grounded answer in this browser page.",
        "actions": [
            {"name": key, "label": spec.label, "safe_level": spec.safe_level}
            for key, spec in ACTIONS.items()
        ],
        "links": LINKS,
    }



def _json_bytes(payload: dict[str, object]) -> bytes:
    return json.dumps(payload, indent=2).encode("utf-8")



def run_ui(host: str = "127.0.0.1", port: int = 8785, open_browser: bool = True) -> int:
    class Handler(BaseHTTPRequestHandler):
        def _send(self, code: int, content_type: str, body: bytes) -> None:
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path == "/":
                self._send(200, "text/html; charset=utf-8", HTML.encode("utf-8"))
                return
            if parsed.path == "/api/summary":
                self._send(200, "application/json; charset=utf-8", _json_bytes(_summary_payload()))
                return
            self._send(404, "application/json; charset=utf-8", _json_bytes({"error": "not found"}))

        def do_POST(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            action = parsed.path.removeprefix('/api/')
            if action in ACTIONS:
                self._send(200, "application/json; charset=utf-8", _json_bytes(_run_action(action)))
                return
            if action.startswith('open/'):
                name = action.removeprefix('open/')
                if name in LINKS:
                    self._send(200, "application/json; charset=utf-8", _json_bytes(_open_link(name)))
                    return
            if action == 'search':
                payload = _read_json_body(self)
                self._send(200, "application/json; charset=utf-8", _json_bytes(_post_json(API_TARGETS['search'], payload)))
                return
            if action == 'answer':
                payload = _read_json_body(self)
                self._send(200, "application/json; charset=utf-8", _json_bytes(_post_json(API_TARGETS['answer'], payload)))
                return
            self._send(404, "application/json; charset=utf-8", _json_bytes({"error": "not found"}))

        def log_message(self, fmt: str, *args: object) -> None:  # noqa: A003
            return

    server = ThreadingHTTPServer((host, port), Handler)
    url = f"http://{host}:{port}"
    print(json.dumps({"ui_url": url, "message": "tof_local_knowledge UI is running"}, indent=2))
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0
