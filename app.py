#!/usr/bin/env python3
"""Behavioral finance biases quiz: a small local web app (standard library only).

Run:  python3 app.py     then open  http://localhost:8000
"""
import html
import json
import os
import random
import secrets
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE_DIR = Path(__file__).parent
HOST = "127.0.0.1"  # local only; nothing is exposed on the network
PORT = int(os.environ.get("PORT", 8000))
QUIZ_LENGTH = 10
LABELS = "ABCDE"

DATA = json.loads((BASE_DIR / "questions.json").read_text(encoding="utf-8"))
BIASES = {b["name"]: b for b in DATA["biases"]}
QUESTIONS = {q["id"]: q for q in DATA["questions"]}

# session id -> {"quiz": [{"id", "options", "choice"}], "index": int}
SESSIONS = {}


def esc(text):
    return html.escape(str(text), quote=True)


# --------------------------------------------------------------------------
# Quiz logic
# --------------------------------------------------------------------------
def new_quiz():
    picked = random.sample(list(QUESTIONS.values()), QUIZ_LENGTH)
    quiz = []
    for q in picked:
        options = [q["bias"]] + q["distractors"]
        random.shuffle(options)
        quiz.append({"id": q["id"], "options": options, "choice": None})
    return {"quiz": quiz, "index": 0}


def score(session):
    return sum(1 for item in session["quiz"] if item["choice"] == QUESTIONS[item["id"]]["bias"])


# --------------------------------------------------------------------------
# HTML rendering
# --------------------------------------------------------------------------
def page(title, body):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<link rel="stylesheet" href="/static/style.css">
</head>
<body>
<main class="card">
{body}
</main>
</body>
</html>"""


def post_button(action, label, css="btn"):
    return f'<form method="post" action="{action}"><button class="{css}" type="submit">{esc(label)}</button></form>'


def render_home(session):
    resume = ""
    if session and session["index"] < QUIZ_LENGTH:
        n = session["index"] + 1
        resume = f'<p class="muted">You have a quiz in progress. <a href="/question">Resume at question {n}</a>.</p>'
    body = f"""
<h1>Behavioral Finance Bias Quiz</h1>
<p>Each question describes a short investing scenario. Pick which of the five behavioral biases is at work.</p>
<p>Every quiz is {QUIZ_LENGTH} questions drawn at random from a bank of {len(QUESTIONS)} questions covering {len(BIASES)} biases.</p>
{post_button("/start", "Start quiz")}
{resume}"""
    return page("Bias Quiz", body)


def render_question(session):
    i = session["index"]
    item = session["quiz"][i]
    q = QUESTIONS[item["id"]]
    options = "\n".join(
        f'<label class="option"><input type="radio" name="choice" value="{esc(opt)}" required>'
        f'<span class="letter">{LABELS[n]}</span><span>{esc(opt)}</span></label>'
        for n, opt in enumerate(item["options"])
    )
    body = f"""
<p class="progress">Question {i + 1} of {QUIZ_LENGTH}</p>
<div class="bar"><div style="width:{i / QUIZ_LENGTH * 100:.0f}%"></div></div>
<h2>Which bias is at work here?</h2>
<p class="scenario">{esc(q["scenario"])}</p>
<form method="post" action="/answer">
{options}
<button class="btn" type="submit" id="submit" disabled>Submit</button>
</form>
<script>
const btn = document.getElementById('submit');
document.querySelectorAll('input[name=choice]').forEach(r => r.addEventListener('change', () => btn.disabled = false));
if (document.querySelector('input[name=choice]:checked')) btn.disabled = false;
</script>"""
    return page(f"Question {i + 1}", body)


def render_result(session):
    i = session["index"]
    item = session["quiz"][i]
    q = QUESTIONS[item["id"]]
    correct = q["bias"]
    chosen = item["choice"]
    is_right = chosen == correct
    bias = BIASES[correct]

    rows = []
    for n, opt in enumerate(item["options"]):
        cls, mark = "option", ""
        if opt == correct:
            cls, mark = "option correct", "&#10003; Correct answer"
        elif opt == chosen:
            cls, mark = "option wrong", "&#10007; Your answer"
        rows.append(
            f'<div class="{cls}"><span class="letter">{LABELS[n]}</span><span>{esc(opt)}</span>'
            f'<span class="mark">{mark}</span></div>'
        )

    banner = (
        '<div class="banner right">Correct!</div>'
        if is_right
        else f'<div class="banner wrong">Incorrect. The answer is <strong>{esc(correct)}</strong>.</div>'
    )
    last = i == QUIZ_LENGTH - 1
    body = f"""
<p class="progress">Question {i + 1} of {QUIZ_LENGTH}</p>
<div class="bar"><div style="width:{(i + 1) / QUIZ_LENGTH * 100:.0f}%"></div></div>
{banner}
<p class="scenario">{esc(q["scenario"])}</p>
{"".join(rows)}
<h3>Explanation</h3>
<p>{esc(q["explanation"])}</p>
<div class="definition"><strong>{esc(correct)}</strong>
<span class="family">{esc(bias["family"])}</span><br>{esc(bias["definition"])}</div>
{post_button("/next", "See results" if last else "Next question")}"""
    return page(f"Result {i + 1}", body)


def render_summary(session):
    total = score(session)
    rows = []
    for n, item in enumerate(session["quiz"], 1):
        q = QUESTIONS[item["id"]]
        ok = item["choice"] == q["bias"]
        detail = (
            f'You answered <strong>{esc(item["choice"])}</strong>'
            if ok
            else f'You answered <strong>{esc(item["choice"])}</strong>; correct: <strong>{esc(q["bias"])}</strong>'
        )
        rows.append(
            f'<details class="review {"ok" if ok else "bad"}"><summary>'
            f'<span class="icon">{"&#10003;" if ok else "&#10007;"}</span> Q{n}: {esc(q["bias"])}</summary>'
            f'<p class="scenario">{esc(q["scenario"])}</p><p>{detail}</p></details>'
        )
    body = f"""
<h1>Quiz complete</h1>
<p class="final">{total} / {QUIZ_LENGTH}</p>
<p class="muted">{total / QUIZ_LENGTH:.0%} correct. Expand a question to review it.</p>
{"".join(rows)}
{post_button("/start", "Start new quiz")}"""
    return page("Results", body)


# --------------------------------------------------------------------------
# HTTP handling
# --------------------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # keep the terminal quiet
        pass

    # -- helpers --
    def session_id(self):
        cookie = SimpleCookie(self.headers.get("Cookie", ""))
        return cookie["sid"].value if "sid" in cookie else None

    def current_session(self):
        return SESSIONS.get(self.session_id())

    def send_page(self, content, status=200, extra_headers=()):
        data = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        for k, v in extra_headers:
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def redirect(self, location, extra_headers=()):
        self.send_response(303)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        for k, v in extra_headers:
            self.send_header(k, v)
        self.end_headers()

    def read_form(self):
        length = int(self.headers.get("Content-Length") or 0)
        return parse_qs(self.rfile.read(length).decode("utf-8"))

    # -- GET --
    def do_GET(self):
        path = urlparse(self.path).path
        session = self.current_session()

        if path == "/":
            return self.send_page(render_home(session))
        if path == "/static/style.css":
            data = (BASE_DIR / "static" / "style.css").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/css; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            return self.wfile.write(data)
        if path in ("/question", "/result", "/summary"):
            if not session:
                return self.redirect("/")
            if session["index"] >= QUIZ_LENGTH:
                return self.redirect("/summary") if path != "/summary" else self.send_page(render_summary(session))
            if path == "/summary":
                return self.redirect("/question")
            answered = session["quiz"][session["index"]]["choice"] is not None
            if path == "/question":
                return self.redirect("/result") if answered else self.send_page(render_question(session))
            return self.send_page(render_result(session)) if answered else self.redirect("/question")
        self.send_page(page("Not found", "<h1>Not found</h1><p><a href='/'>Home</a></p>"), status=404)

    # -- POST --
    def do_POST(self):
        path = urlparse(self.path).path
        session = self.current_session()

        if path == "/start":
            sid = secrets.token_urlsafe(16)
            SESSIONS[sid] = new_quiz()
            return self.redirect("/question", [("Set-Cookie", f"sid={sid}; Path=/; HttpOnly; SameSite=Strict")])

        if not session:
            return self.redirect("/")

        if path == "/answer":
            form = self.read_form()
            if session["index"] < QUIZ_LENGTH:
                item = session["quiz"][session["index"]]
                choice = (form.get("choice") or [None])[0]
                if item["choice"] is None and choice in item["options"]:
                    item["choice"] = choice
            return self.redirect("/question")

        if path == "/next":
            item = session["quiz"][session["index"]] if session["index"] < QUIZ_LENGTH else None
            if item and item["choice"] is not None:
                session["index"] += 1
            return self.redirect("/question")

        self.send_page(page("Not found", "<h1>Not found</h1><p><a href='/'>Home</a></p>"), status=404)


def main():
    try:
        server = ThreadingHTTPServer((HOST, PORT), Handler)
    except OSError as err:
        raise SystemExit(f"Could not start on port {PORT}: {err}\nTry: PORT=8001 python3 app.py")
    print(f"Quiz running at http://localhost:{PORT}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
