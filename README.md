# Behavioral Finance Bias Quiz

A local quiz on the 20 investor biases from `behavioral_finance_biases_summary.pdf`.
Each quiz is 10 random scenario questions drawn from a bank of 200 (10 per bias).
Pick which of 5 biases is at work, submit, and see whether you were right plus an explanation.

## Run

```
python3 app.py
```

Then open http://localhost:8000. Stop with Ctrl+C.

Python 3 only, no packages to install. If port 8000 is busy: `PORT=8001 python3 app.py`.

## Files

- `app.py`: the web server and all pages
- `questions.json`: the 20 biases and the 200 questions (edit or add here)
- `static/style.css`: styling
- `validate_questions.py`: run after editing `questions.json` to check it is well formed

## Adding a question

Add an entry to `questions.json`:

```json
{"id": "anch-06", "bias": "Anchoring and Adjustment",
 "scenario": "...", "distractors": ["Framing", "Recency", "Availability", "Conservatism"],
 "explanation": "..."}
```

Then run `python3 validate_questions.py`. Note it expects exactly 10 questions per bias, so
update `PER_BIAS` in that script if you grow the bank.
