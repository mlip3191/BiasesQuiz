# Behavioral Finance Bias Quiz

A local quiz on the 20 investor biases from `behavioral_finance_biases_summary.pdf`.
Each quiz is 10 random scenario questions drawn from a bank of 200 (10 per bias).
Pick which of 5 biases is at work, submit, and see whether you were right plus an explanation.

The quiz runs on your own computer and opens in your web browser. It does not need the internet once it is downloaded, and it is not reachable from other computers.

## Quick start (if you already know Python)

```
python3 app.py
```

Then open http://localhost:8000. Stop with Ctrl+C. Python 3 only, no packages to install.

The rest of this file is a step-by-step guide for people with no coding experience, on Windows or Mac.

## What you need

| Requirement | Notes |
|---|---|
| A computer | Windows 10 or 11, or a Mac (macOS) |
| A web browser | Chrome, Safari, Edge or Firefox |
| Python 3 (version 3.9 or newer) | Free. Step 1 shows how to install it. |
| Internet | Only for the one-time downloads |

That is everything. There is nothing else to install: no extra Python packages, no database, no accounts. The quiz uses only what comes with Python.

Two words used below: the **terminal** is a window where you type commands (it is called Terminal on Mac and Command Prompt on Windows), and a **folder path** is the address of a folder on your computer.

## Step 1: Install Python

### Mac

1. Open Terminal: press `Cmd + Space`, type `Terminal`, press Enter.
2. Type this and press Enter:
   ```
   python3 --version
   ```
3. If it prints something like `Python 3.9.6` or higher, skip to Step 2.
4. If a window offers to install "command line developer tools", click **Install** and wait for it to finish, then try step 2 again. If you just get `command not found`, download the installer from https://www.python.org/downloads/ , open it and click through it.

### Windows

1. Go to https://www.python.org/downloads/ and click the yellow **Download Python** button.
2. Open the file you downloaded.
3. **Important:** on the first screen, tick the box **"Add python.exe to PATH"** at the bottom. If you miss this, Python will not work from the terminal.
4. Click **Install Now** and wait until it says the setup was successful.
5. Open Command Prompt: click the Start menu, type `cmd`, press Enter.
6. Type this and press Enter:
   ```
   python --version
   ```
   You should see `Python 3.` followed by numbers. If `python` is not recognized, try `py --version` instead (and use `py` wherever this guide says `python`). If neither works, see Troubleshooting.

## Step 2: Download the project

1. Go to https://github.com/mlip3191/BiasesQuiz
2. Click the green **Code** button, then **Download ZIP**.
3. Unzip it:
   - **Windows:** right-click the ZIP file in your Downloads folder, choose **Extract All**, then **Extract**.
   - **Mac:** double-click the ZIP file in your Downloads folder.
4. You now have a folder called `BiasesQuiz-main` (the name may differ slightly).

If you already use Git, you can instead run `git clone https://github.com/mlip3191/BiasesQuiz.git`.

## Step 3: Open a terminal inside the project folder

### Mac

Open Terminal and type the following, then press Enter. If you left the folder in Downloads, this is:

```
cd ~/Downloads/BiasesQuiz-main
```

Shortcut: you can also type `cd ` (with a space after it) and drag the folder from Finder into the Terminal window, then press Enter.

### Windows

Open the `BiasesQuiz-main` folder in File Explorer. Make sure you can see files such as `app.py` in it. Click the address bar at the top, type `cmd`, and press Enter. A Command Prompt opens already inside the folder.

Or, from any Command Prompt:

```
cd %USERPROFILE%\Downloads\BiasesQuiz-main
```

If the ZIP was extracted into a second folder with the same name, go one level deeper until `dir` (Windows) or `ls` (Mac) lists `app.py`.

## Step 4: Start the quiz

### Mac

```
python3 app.py
```

### Windows

```
python app.py
```

You should see `Quiz running at http://localhost:8000  (Ctrl+C to stop)`.

Now open your web browser and go to **http://localhost:8000**. Click to start a quiz.

**Leave the terminal window open while you use the quiz.** To stop it, click the terminal window and press `Ctrl + C`. To start it again later, repeat Steps 3 and 4.

### If port 8000 is already in use

Pick another number, such as 8001, and then open http://localhost:8001 instead.

| Where you type it | Command |
|---|---|
| Mac Terminal | `PORT=8001 python3 app.py` |
| Windows Command Prompt | `set PORT=8001` then press Enter, then `python app.py` |
| Windows PowerShell | `$env:PORT=8001` then press Enter, then `python app.py` |

## Check the questions (optional)

After you edit `questions.json`, check that it is still well formed:

```
python3 validate_questions.py
```

On Windows use `python validate_questions.py`. A good result prints `OK: 20 biases, 200 questions`. Otherwise it lists every problem it found.

## Troubleshooting

| What you see | What it means and what to do |
|---|---|
| Windows: `'python' is not recognized` | Python is not on your PATH. Try `py app.py`. If that fails, re-run the Python installer, choose **Modify** or reinstall, and tick **Add python.exe to PATH**. Then open a new Command Prompt. |
| Windows: typing `python` opens the Microsoft Store | Install Python from python.org (Step 1), then open a new Command Prompt. If it still opens the Store, turn off the `python.exe` entry under Settings > Apps > Advanced app settings > App execution aliases. |
| Mac: `python3: command not found` | Install Python from https://www.python.org/downloads/ (Step 1). |
| `can't open file 'app.py'` | You are in the wrong folder. Repeat Step 3 and make sure `app.py` is listed in the folder. |
| `Could not start on port 8000` | Something else is using that port. Use the port instructions above. |
| The browser says the site can't be reached | The terminal window with the quiz must still be open and showing `Quiz running`. Start it again with Step 4. |
| `OK` does not appear after validating | Read the lines it prints. Each one names the question and the problem. |

## Using an AI assistant (Claude or ChatGPT)

You can ask an AI to walk you through setup, explain an error, or change the quiz. Either one works. The difference is that **Claude Code can run commands and edit files on your computer for you**, while **ChatGPT only talks to you**: it will write the answer, and you copy and run it yourself.

### Option A: Claude Code

1. Install it by following the instructions at https://claude.com/claude-code (it has an installer for Mac and for Windows). It needs a Claude subscription or API account.
2. In the terminal, go to the project folder (Step 3), type `claude` and press Enter, then sign in when asked.
3. Paste one of the prompts below. Claude Code can run the commands and make the edits itself, and will ask your permission first.

### Option B: ChatGPT

1. Go to https://chatgpt.com and sign in (a free account is enough to start).
2. Paste one of the prompts below.
3. When it gives you a command, copy it into your terminal and press Enter. When it asks to see a file, open the file in a text editor (Notepad on Windows, TextEdit on Mac), copy the contents and paste them into the chat. You can also drag the file into the chat window to attach it.
4. If something goes wrong, copy the full error from the terminal and paste it back into the chat.

### Prompts you can copy

Replace anything in `[square brackets]`. These work in both Claude and ChatGPT.

**Get set up from scratch**

```
I am a complete beginner and have never used a terminal. I use [Windows / Mac].
I downloaded a small Python quiz app called BiasesQuiz from
https://github.com/mlip3191/BiasesQuiz . It only needs Python 3 and has no other
dependencies. Walk me through installing Python, opening a terminal in the project
folder, and running "python3 app.py" (or "python app.py" on Windows) so I can open
http://localhost:8000 in my browser. Give me one step at a time and wait for me to
say it worked before giving the next step.
```

**Fix an error**

```
I am a beginner using [Windows / Mac]. I ran "[the command you typed]" for a Python
quiz app and got this error:

[paste the full text from the terminal]

Explain what it means in plain English and tell me the exact steps to fix it.
```

**Add questions**

```
This project has questions in questions.json. Each question has "id", "bias",
"scenario", "distractors" (4 other bias names) and "explanation". Look at the
existing questions for [bias name] and add 5 more in the same style and format, with
ids numbered after the last one. Do not name the bias in the scenario. Then remind
me to update PER_BIAS in validate_questions.py and run it.
```

If you use ChatGPT, also paste in the contents of `questions.json` (or the part for that bias) before sending this.

**Change the quiz length**

```
In app.py, the quiz is 10 questions long (QUIZ_LENGTH = 10). Change it to [20]
questions and tell me exactly what to save and how to restart the quiz.
```

**Understand the project**

```
Explain in simple terms what each file in this project does: app.py, questions.json,
validate_questions.py, static/style.css and the README.
```

### Tips for good results

- Always say which computer you use (Windows or Mac).
- Paste the full error text, not a description of it.
- Ask for one step at a time when you are new to this.
- If an answer mentions something you do not understand, ask "what does that mean?"

## Files

- `app.py`: the web server and all pages
- `questions.json`: the 20 biases and the 200 questions (edit or add here)
- `static/style.css`: styling
- `validate_questions.py`: run after editing `questions.json` to check it is well formed

## Adding a question

Add an entry to `questions.json`:

```json
{"id": "anch-11", "bias": "Anchoring and Adjustment",
 "scenario": "...", "distractors": ["Framing", "Recency", "Availability", "Conservatism"],
 "explanation": "..."}
```

Then run `python3 validate_questions.py`. The checker expects exactly 10 questions per bias, so if you add or remove questions, change `PER_BIAS` near the top of `validate_questions.py` to the new number.
