#!/usr/bin/env python3
"""Sanity-check questions.json. Exits non-zero and lists every problem found."""
import json
import re
import sys
from collections import Counter
from pathlib import Path

EXPECTED_BIASES = 20
PER_BIAS = 10

data = json.loads((Path(__file__).parent / "questions.json").read_text(encoding="utf-8"))
bias_names = [b["name"] for b in data["biases"]]
questions = data["questions"]
problems = []

if len(bias_names) != EXPECTED_BIASES or len(set(bias_names)) != EXPECTED_BIASES:
    problems.append(f"expected {EXPECTED_BIASES} unique biases, found {len(bias_names)}")
for b in data["biases"]:
    for key in ("name", "family", "definition"):
        if not b.get(key, "").strip():
            problems.append(f"bias {b.get('name')!r}: missing {key}")

if len(questions) != EXPECTED_BIASES * PER_BIAS:
    problems.append(f"expected {EXPECTED_BIASES * PER_BIAS} questions, found {len(questions)}")

for bias, n in Counter(q["bias"] for q in questions).items():
    if bias not in bias_names:
        problems.append(f"unknown bias {bias!r}")
    elif n != PER_BIAS:
        problems.append(f"{bias}: {n} questions (expected {PER_BIAS})")
for bias in bias_names:
    if not any(q["bias"] == bias for q in questions):
        problems.append(f"{bias}: no questions")

ids = Counter(q["id"] for q in questions)
scenarios = Counter(q["scenario"].strip() for q in questions)
problems += [f"duplicate id {i}" for i, n in ids.items() if n > 1]
problems += [f"duplicate scenario: {s[:60]}..." for s, n in scenarios.items() if n > 1]

# Names that must not appear in a scenario (they would give the answer away).
GIVEAWAY = {
    "Cognitive Dissonance": r"cognitive dissonance",
    "Conservatism": r"conservatism",
    "Confirmation": r"confirmation bias",
    "Representativeness": r"representativeness",
    "Illusion of Control": r"illusion of control",
    "Hindsight": r"hindsight",
    "Mental Accounting": r"mental account",
    "Anchoring and Adjustment": r"anchor",
    "Framing": r"framing|framed",
    "Availability": r"availability",
    "Self-Attribution": r"self-attribution",
    "Outcome": r"outcome bias",
    "Recency": r"recency",
    "Loss Aversion": r"loss aversion",
    "Overconfidence": r"overconfiden",
    "Self-Control": r"self-control",
    "Status Quo": r"status quo",
    "Endowment": r"endowment",
    "Regret Aversion": r"regret aversion",
    "Affinity": r"affinity",
}

for q in questions:
    qid = q["id"]
    d = q.get("distractors", [])
    if len(d) != 4 or len(set(d)) != 4:
        problems.append(f"{qid}: needs exactly 4 distinct distractors")
    if q["bias"] in d:
        problems.append(f"{qid}: distractors include the correct answer")
    for name in d:
        if name not in bias_names:
            problems.append(f"{qid}: unknown distractor {name!r}")
    if not q.get("scenario", "").strip() or not q.get("explanation", "").strip():
        problems.append(f"{qid}: empty scenario or explanation")
    for name, pattern in GIVEAWAY.items():
        if re.search(pattern, q.get("scenario", ""), re.I):
            problems.append(f"{qid}: scenario mentions '{name}' bias terminology")

if problems:
    print("\n".join(f"- {p}" for p in problems))
    sys.exit(1)
print(f"OK: {len(bias_names)} biases, {len(questions)} questions")
