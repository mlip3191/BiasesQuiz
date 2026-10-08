#!/usr/bin/env python3
"""Sanity-check quiz files. Exits non-zero and lists every problem found.

Usage:  python3 validate_questions.py                 (checks every quizzes/*.json)
        python3 validate_questions.py quizzes/x.json  (checks just that file)
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path


def check(path):
    """Return (problems, summary) for one quiz file."""
    problems = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as err:
        return [f"cannot read file: {err}"], ""

    for key in ("title", "questions"):
        if not data.get(key):
            problems.append(f"missing {key!r}")
    questions = data.get("questions", [])
    cfg = data.get("validation", {})

    length = data.get("quiz_length", 10)
    if not isinstance(length, int) or length < 1:
        problems.append("quiz_length must be a positive integer")
    elif length > len(questions):
        problems.append(f"quiz_length {length} is more than the {len(questions)} questions")

    # Optional categories (e.g. the 20 biases): answers/distractors must come from them.
    categories = data.get("categories", [])
    cat_names = [c.get("name") for c in categories]
    if len(set(cat_names)) != len(cat_names):
        problems.append("duplicate category names")
    for c in categories:
        for key in ("name", "definition"):
            if not c.get(key, "").strip():
                problems.append(f"category {c.get('name')!r}: missing {key}")

    per_category = cfg.get("per_category")
    if categories:
        counts = Counter(q.get("answer") for q in questions)
        for name in cat_names:
            if counts[name] == 0:
                problems.append(f"{name}: no questions")
            elif per_category and counts[name] != per_category:
                problems.append(f"{name}: {counts[name]} questions (expected {per_category})")
        for name in counts:
            if name not in cat_names:
                problems.append(f"unknown category {name!r} used as an answer")

    ids = Counter(q.get("id") for q in questions)
    scenarios = Counter(q.get("scenario", "").strip() for q in questions)
    problems += [f"duplicate id {i}" for i, n in ids.items() if n > 1]
    problems += [f"duplicate scenario: {s[:60]}..." for s, n in scenarios.items() if n > 1]

    giveaway = cfg.get("giveaway", {})
    for q in questions:
        qid = q.get("id", "<no id>")
        answer = q.get("answer", "")
        d = q.get("distractors", [])
        if not qid or qid == "<no id>":
            problems.append("question without an id")
        if not answer.strip():
            problems.append(f"{qid}: missing answer")
        if len(d) < 2 or len(set(d)) != len(d):
            problems.append(f"{qid}: needs at least 2 distinct distractors")
        if categories and len(d) != 4:
            problems.append(f"{qid}: category quizzes need exactly 4 distractors")
        if answer in d:
            problems.append(f"{qid}: distractors include the correct answer")
        if categories:
            for name in d:
                if name not in cat_names:
                    problems.append(f"{qid}: unknown distractor {name!r}")
        if not q.get("scenario", "").strip() or not q.get("explanation", "").strip():
            problems.append(f"{qid}: empty scenario or explanation")
        # Names that must not appear in a scenario (they would give the answer away).
        for name, pattern in giveaway.items():
            if re.search(pattern, q.get("scenario", ""), re.I):
                problems.append(f"{qid}: scenario mentions '{name}' terminology")

    summary = f"{len(categories)} categories, " if categories else ""
    return problems, f"{summary}{len(questions)} questions"


def main():
    base = Path(__file__).parent
    paths = [Path(a) for a in sys.argv[1:]] or sorted((base / "quizzes").glob("*.json"))
    if not paths:
        sys.exit("No quiz files found in quizzes/")
    failed = False
    for path in paths:
        problems, summary = check(path)
        if problems:
            failed = True
            print(f"{path.name}:")
            print("\n".join(f"- {p}" for p in problems))
        else:
            print(f"OK: {path.stem}: {summary}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
