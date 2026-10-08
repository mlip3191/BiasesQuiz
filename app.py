#!/usr/bin/env python3
"""Multi-quiz local web app (standard library only). Each quizzes/*.json file is one tab.

Run:  python3 app.py     then open  http://localhost:8000
"""
import html
import json
import os
import random
import secrets
import string
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE_DIR = Path(__file__).parent
HOST = "127.0.0.1"  # local only; nothing is exposed on the network
PORT = int(os.environ.get("PORT", 8000))
LABELS = string.ascii_uppercase
DEFAULT_LENGTH = 10


def load_quizzes():
    """Read every quizzes/*.json into {slug: quiz}, ordered by "order" then filename."""
    quizzes = []
    for path in sorted((BASE_DIR / "quizzes").glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            quizzes.append((data.get("order", 100), path.stem, {
                "slug": path.stem,
                "title": data["title"],
                "tab": data.get("tab", data["title"]),
                "intro": data.get("intro", ""),
                "prompt": data.get("prompt", "Choose the best answer."),
                "categories": {c["name"]: c for c in data.get("categories", [])},
                "questions": {q["id"]: q for q in data["questions"]},
                "length": min(data.get("quiz_length", DEFAULT_LENGTH), len(data["questions"])),
            }))
        except (OSError, ValueError, KeyError) as err:
            raise SystemExit(f"Could not load {path.name}: {err!r}\nRun: python3 validate_questions.py")
    if not quizzes:
        raise SystemExit("No quizzes found. Add a JSON file to the quizzes/ folder.")
    return {slug: quiz for _, slug, quiz in sorted(quizzes, key=lambda t: t[:2])}


QUIZZES = load_quizzes()
DEFAULT_SLUG = next(iter(QUIZZES))

# session id -> {"slug", "quiz": [{"id", "options", "choice"}], "index": int}
SESSIONS = {}


def esc(text):
    return html.escape(str(text), quote=True)


# --------------------------------------------------------------------------
# Quiz logic
# --------------------------------------------------------------------------
def new_quiz(slug):
    quiz_def = QUIZZES[slug]
    picked = random.sample(list(quiz_def["questions"].values()), quiz_def["length"])
    quiz = []
    for q in picked:
        options = [q["answer"]] + q["distractors"]
        random.shuffle(options)
        quiz.append({"id": q["id"], "options": options, "choice": None})
    return {"slug": slug, "quiz": quiz, "index": 0}


def questions_of(session):
    return QUIZZES[session["slug"]]["questions"]


def total_of(session):
    return len(session["quiz"])


def score(session):
    questions = questions_of(session)
    return sum(1 for item in session["quiz"] if item["choice"] == questions[item["id"]]["answer"])


# --------------------------------------------------------------------------
# HTML rendering
# --------------------------------------------------------------------------
def tab_bar(active):
    links = []
    for slug, quiz in QUIZZES.items():
        cls = ' class="active"' if slug == active else ""
        links.append(f'<a href="/?quiz={esc(slug)}"{cls}>{esc(quiz["tab"])}</a>')
    return f'<nav class="tabs">{"".join(links)}</nav>'


def page(title, body, active=DEFAULT_SLUG):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<link rel="stylesheet" href="/static/style.css">
</head>
<body>
{tab_bar(active)}
<main class="card">
{body}
</main>
</body>
</html>"""


def post_button(action, label, css="btn"):
    return f'<form method="post" action="{action}"><button class="{css}" type="submit">{esc(label)}</button></form>'


def start_button(slug, label):
    return (
        f'<form method="post" action="/start"><input type="hidden" name="quiz" value="{esc(slug)}">'
        f'<button class="btn" type="submit">{esc(label)}</button></form>'
    )


def render_home(session, slug):
    quiz_def = QUIZZES[slug]
    resume = ""
    if session and session["index"] < total_of(session):
        n = session["index"] + 1
        if session["slug"] == slug:
            resume = f'<p class="muted">You have a quiz in progress. <a href="/question">Resume at question {n}</a>.</p>'
        else:
            other = QUIZZES[session["slug"]]["tab"]
            resume = (
                f'<p class="muted">You have a {esc(other)} quiz in progress. '
                f'<a href="/question">Resume it</a>, or starting here will discard it.</p>'
            )
    counts = f"{quiz_def['length']} questions drawn at random from a bank of {len(quiz_def['questions'])}"
    if quiz_def["categories"]:
        counts += f" covering {len(quiz_def['categories'])} topics"
    body = f"""
<h1>{esc(quiz_def["title"])}</h1>
<p>{esc(quiz_def["intro"])}</p>
<p>Every quiz is {counts}.</p>
{start_button(slug, "Start quiz")}
{resume}"""
    return page(quiz_def["tab"], body, slug)


def render_question(session):
    i = session["index"]
    n_total = total_of(session)
    quiz_def = QUIZZES[session["slug"]]
    item = session["quiz"][i]
    q = quiz_def["questions"][item["id"]]
    options = "\n".join(
        f'<label class="option"><input type="radio" name="choice" value="{esc(opt)}" required>'
        f'<span class="letter">{LABELS[n]}</span><span>{esc(opt)}</span></label>'
        for n, opt in enumerate(item["options"])
    )
    body = f"""
<p class="progress">Question {i + 1} of {n_total}</p>
<div class="bar"><div style="width:{i / n_total * 100:.0f}%"></div></div>
<h2>{esc(quiz_def["prompt"])}</h2>
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
    return page(f"Question {i + 1}", body, session["slug"])


def render_result(session):
    i = session["index"]
    n_total = total_of(session)
    quiz_def = QUIZZES[session["slug"]]
    item = session["quiz"][i]
    q = quiz_def["questions"][item["id"]]
    correct = q["answer"]
    chosen = item["choice"]
    is_right = chosen == correct
    category = quiz_def["categories"].get(correct)

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
    last = i == n_total - 1
    definition = ""
    if category:
        family = f'<span class="family">{esc(category["family"])}</span>' if category.get("family") else ""
        definition = (
            f'<div class="definition"><strong>{esc(correct)}</strong>{family}'
            f'<br>{esc(category["definition"])}</div>'
        )
    body = f"""
<p class="progress">Question {i + 1} of {n_total}</p>
<div class="bar"><div style="width:{(i + 1) / n_total * 100:.0f}%"></div></div>
{banner}
<p class="scenario">{esc(q["scenario"])}</p>
{"".join(rows)}
<h3>Explanation</h3>
<p>{esc(q["explanation"])}</p>
{definition}
{post_button("/next", "See results" if last else "Next question")}"""
    return page(f"Result {i + 1}", body, session["slug"])


def render_summary(session):
    total = score(session)
    n_total = total_of(session)
    questions = questions_of(session)
    rows = []
    for n, item in enumerate(session["quiz"], 1):
        q = questions[item["id"]]
        ok = item["choice"] == q["answer"]
        detail = (
            f'You answered <strong>{esc(item["choice"])}</strong>'
            if ok
            else f'You answered <strong>{esc(item["choice"])}</strong>; correct: <strong>{esc(q["answer"])}</strong>'
        )
        rows.append(
            f'<details class="review {"ok" if ok else "bad"}"><summary>'
            f'<span class="icon">{"&#10003;" if ok else "&#10007;"}</span> Q{n}: {esc(q["answer"])}</summary>'
            f'<p class="scenario">{esc(q["scenario"])}</p><p>{detail}</p></details>'
        )
    body = f"""
<h1>Quiz complete</h1>
<p class="final">{total} / {n_total}</p>
<p class="muted">{total / n_total:.0%} correct. Expand a question to review it.</p>
{"".join(rows)}
{start_button(session["slug"], "Start new quiz")}"""
    return page("Results", body, session["slug"])


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
            slug = (parse_qs(urlparse(self.path).query).get("quiz") or [None])[0]
            if slug not in QUIZZES:
                slug = session["slug"] if session else DEFAULT_SLUG
            return self.send_page(render_home(session, slug))
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
            if session["index"] >= total_of(session):
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
            slug = (self.read_form().get("quiz") or [None])[0]
            if slug not in QUIZZES:
                return self.send_page(page("Not found", "<h1>Unknown quiz</h1><p><a href='/'>Home</a></p>"), status=400)
            sid = secrets.token_urlsafe(16)
            SESSIONS[sid] = new_quiz(slug)
            return self.redirect("/question", [("Set-Cookie", f"sid={sid}; Path=/; HttpOnly; SameSite=Strict")])

        if not session:
            return self.redirect("/")

        if path == "/answer":
            form = self.read_form()
            if session["index"] < total_of(session):
                item = session["quiz"][session["index"]]
                choice = (form.get("choice") or [None])[0]
                if item["choice"] is None and choice in item["options"]:
                    item["choice"] = choice
            return self.redirect("/question")

        if path == "/next":
            item = session["quiz"][session["index"]] if session["index"] < total_of(session) else None
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
