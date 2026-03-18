"""Pair Programming Simulator — Flask web app for Replit deployment.

A virtual environment that simulates pair programming scenarios,
teaching collaboration and communication skills in coding.
"""

import json
import os
import re
import sqlite3
import textwrap
import time
from datetime import datetime, timezone

from flask import Flask, g, jsonify, redirect, render_template_string, request, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-key-change-in-production")

DB_PATH = os.path.join("data", "app.db")

# ---------------------------------------------------------------------------
# Coding tasks
# ---------------------------------------------------------------------------

TASKS = [
    {
        "id": "implement-fizzbuzz",
        "title": "Implement FizzBuzz",
        "difficulty": "easy",
        "description": "Write a function `fizzbuzz(n)` that returns a list of strings from 1 to n. "
        "For multiples of 3 use 'Fizz', multiples of 5 use 'Buzz', multiples of both use 'FizzBuzz'.",
        "starter": "def fizzbuzz(n):\n    pass\n",
        "test_code": textwrap.dedent("""\
            result = fizzbuzz(15)
            assert len(result) == 15
            assert result[0] == '1'
            assert result[2] == 'Fizz'
            assert result[4] == 'Buzz'
            assert result[14] == 'FizzBuzz'
            assert result[7] == '8'
        """),
        "hints": [
            "Navigator: Think about the order of checks — test divisibility by 15 (or both 3 and 5) before testing 3 or 5 alone.",
            "Navigator: Use the modulo operator (%). Remember to convert numbers to strings.",
            "Navigator: A list comprehension can make this concise. Build the string conditionally.",
        ],
    },
    {
        "id": "reverse-linked-list",
        "title": "Reverse a Linked List",
        "difficulty": "medium",
        "description": "Given a `ListNode` class with `.val` and `.next`, write `reverse_list(head)` "
        "that reverses the list in-place and returns the new head.",
        "starter": (
            "class ListNode:\n"
            "    def __init__(self, val=0, nxt=None):\n"
            "        self.val = val\n"
            "        self.next = nxt\n\n"
            "def reverse_list(head):\n"
            "    pass\n"
        ),
        "test_code": textwrap.dedent("""\
            head = ListNode(1, ListNode(2, ListNode(3)))
            rev = reverse_list(head)
            vals = []
            while rev:
                vals.append(rev.val)
                rev = rev.next
            assert vals == [3, 2, 1]
        """),
        "hints": [
            "Navigator: You need three pointers — prev, current, and next_node.",
            "Navigator: Walk through the list once, reversing each pointer as you go.",
            "Navigator: Initialize prev as None and iterate while current is not None.",
        ],
    },
    {
        "id": "parse-csv",
        "title": "Parse CSV String",
        "difficulty": "easy",
        "description": "Write `parse_csv(text)` that takes a CSV string (with header row) and returns "
        "a list of dicts. Each dict maps column names to values.",
        "starter": "def parse_csv(text):\n    pass\n",
        "test_code": textwrap.dedent("""\
            csv = "name,age\\nAlice,30\\nBob,25"
            result = parse_csv(csv)
            assert len(result) == 2
            assert result[0]['name'] == 'Alice'
            assert result[1]['age'] == '25'
        """),
        "hints": [
            "Navigator: Split the text into lines first, then split each line by commas.",
            "Navigator: The first line gives you the column headers. Use zip() to pair headers with values.",
            "Navigator: Return a list of dictionaries — one per data row.",
        ],
    },
    {
        "id": "two-sum",
        "title": "Two Sum",
        "difficulty": "easy",
        "description": "Write `two_sum(nums, target)` that returns indices of two numbers that add up "
        "to target. Assume exactly one solution exists.",
        "starter": "def two_sum(nums, target):\n    pass\n",
        "test_code": textwrap.dedent("""\
            assert sorted(two_sum([2, 7, 11, 15], 9)) == [0, 1]
            assert sorted(two_sum([3, 2, 4], 6)) == [1, 2]
        """),
        "hints": [
            "Navigator: A brute-force O(n²) approach checks every pair — but there's a faster way.",
            "Navigator: Use a hash map to store numbers you've already seen.",
            "Navigator: For each number, check if (target - number) is in the map.",
        ],
    },
    {
        "id": "balanced-brackets",
        "title": "Balanced Brackets",
        "difficulty": "medium",
        "description": "Write `is_balanced(s)` that returns True if the string has balanced brackets: "
        "(), [], {}. Ignore non-bracket characters.",
        "starter": "def is_balanced(s):\n    pass\n",
        "test_code": textwrap.dedent("""\
            assert is_balanced('()[]{}') is True
            assert is_balanced('([{}])') is True
            assert is_balanced('(]') is False
            assert is_balanced('([)]') is False
            assert is_balanced('hello(world)') is True
        """),
        "hints": [
            "Navigator: A stack is the classic data structure for this problem.",
            "Navigator: Push opening brackets onto the stack; when you see a closing bracket, check the top.",
            "Navigator: Use a dictionary to map closing brackets to their opening counterparts.",
        ],
    },
    {
        "id": "flatten-nested-list",
        "title": "Flatten Nested List",
        "difficulty": "medium",
        "description": "Write `flatten(lst)` that takes an arbitrarily nested list and returns a flat list "
        "of all values. Example: flatten([1, [2, [3, 4], 5]]) → [1, 2, 3, 4, 5].",
        "starter": "def flatten(lst):\n    pass\n",
        "test_code": textwrap.dedent("""\
            assert flatten([1, [2, [3, 4], 5]]) == [1, 2, 3, 4, 5]
            assert flatten([]) == []
            assert flatten([[1], [[2]], [[[3]]]]) == [1, 2, 3]
        """),
        "hints": [
            "Navigator: Recursion is a natural fit here — base case vs. list case.",
            "Navigator: Check isinstance(item, list) to decide whether to recurse.",
            "Navigator: You can also solve this iteratively with a stack.",
        ],
    },
    {
        "id": "word-frequency",
        "title": "Word Frequency Counter",
        "difficulty": "easy",
        "description": "Write `word_freq(text)` that returns a dict mapping each lowercase word to its count. "
        "Strip punctuation, split on whitespace.",
        "starter": "def word_freq(text):\n    pass\n",
        "test_code": textwrap.dedent("""\
            result = word_freq("the cat sat on the mat")
            assert result['the'] == 2
            assert result['cat'] == 1
            result2 = word_freq("Hello, hello! HELLO.")
            assert result2['hello'] == 3
        """),
        "hints": [
            "Navigator: Convert to lowercase first, then strip punctuation.",
            "Navigator: Use str.split() for whitespace splitting, and re.sub or str.strip for punctuation.",
            "Navigator: A collections.Counter or a plain dict both work.",
        ],
    },
    {
        "id": "binary-search",
        "title": "Binary Search",
        "difficulty": "easy",
        "description": "Write `binary_search(arr, target)` that returns the index of target in a sorted array, "
        "or -1 if not found.",
        "starter": "def binary_search(arr, target):\n    pass\n",
        "test_code": textwrap.dedent("""\
            assert binary_search([1, 3, 5, 7, 9], 5) == 2
            assert binary_search([1, 3, 5, 7, 9], 6) == -1
            assert binary_search([], 1) == -1
        """),
        "hints": [
            "Navigator: Maintain low and high pointers. Compute mid = (low + high) // 2.",
            "Navigator: Compare arr[mid] with target — adjust low or high accordingly.",
            "Navigator: Loop while low <= high. If you exit without finding, return -1.",
        ],
    },
    {
        "id": "matrix-transpose",
        "title": "Matrix Transpose",
        "difficulty": "easy",
        "description": "Write `transpose(matrix)` that returns the transpose of a 2D list. "
        "Rows become columns and vice versa.",
        "starter": "def transpose(matrix):\n    pass\n",
        "test_code": textwrap.dedent("""\
            assert transpose([[1, 2, 3], [4, 5, 6]]) == [[1, 4], [2, 5], [3, 6]]
            assert transpose([[1]]) == [[1]]
        """),
        "hints": [
            "Navigator: zip(*matrix) gives you tuples of columns.",
            "Navigator: Convert each tuple back to a list.",
            "Navigator: One-liner: [list(row) for row in zip(*matrix)].",
        ],
    },
    {
        "id": "lru-cache",
        "title": "LRU Cache",
        "difficulty": "hard",
        "description": "Implement an `LRUCache` class with `__init__(self, capacity)`, `get(self, key)` (returns -1 if missing), "
        "and `put(self, key, value)`. Evict the least recently used item when capacity is exceeded.",
        "starter": (
            "class LRUCache:\n"
            "    def __init__(self, capacity):\n"
            "        pass\n\n"
            "    def get(self, key):\n"
            "        pass\n\n"
            "    def put(self, key, value):\n"
            "        pass\n"
        ),
        "test_code": textwrap.dedent("""\
            cache = LRUCache(2)
            cache.put(1, 1)
            cache.put(2, 2)
            assert cache.get(1) == 1
            cache.put(3, 3)
            assert cache.get(2) == -1
            cache.put(4, 4)
            assert cache.get(1) == -1
            assert cache.get(3) == 3
            assert cache.get(4) == 4
        """),
        "hints": [
            "Navigator: Use an OrderedDict from collections — it supports move_to_end().",
            "Navigator: On get(), move the key to the end (most recent). On put(), pop the first item if over capacity.",
            "Navigator: Alternatively, implement with a dict + doubly linked list for O(1) operations.",
        ],
    },
]

TASKS_BY_ID = {t["id"]: t for t in TASKS}

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------


def get_db():
    if "db" not in g:
        os.makedirs("data", exist_ok=True)
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
        g.db.execute(
            """\
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'driver',
                code TEXT DEFAULT '',
                started_at TEXT NOT NULL,
                completed_at TEXT,
                elapsed_seconds REAL,
                score_correctness INTEGER DEFAULT 0,
                score_time INTEGER DEFAULT 0,
                score_quality INTEGER DEFAULT 0,
                total_score INTEGER DEFAULT 0,
                tests_passed INTEGER DEFAULT 0,
                tests_total INTEGER DEFAULT 0,
                hints_used INTEGER DEFAULT 0
            )"""
        )
        g.db.commit()
    return g.db


@app.teardown_appcontext
def close_db(e=None):
    db = g.pop("db", None)
    if db:
        db.close()


# ---------------------------------------------------------------------------
# Code quality scoring
# ---------------------------------------------------------------------------


def score_quality(code):
    """Heuristic code quality score 0-100."""
    score = 70  # baseline
    lines = code.strip().splitlines()
    if not lines:
        return 0

    # Reward conciseness (but not too short)
    if 3 <= len(lines) <= 30:
        score += 10
    elif len(lines) > 60:
        score -= 10

    # Penalize very long lines
    long_lines = sum(1 for l in lines if len(l) > 100)
    score -= long_lines * 2

    # Reward docstrings / comments
    if any("def " in l for l in lines):
        if any('"""' in l or "'''" in l or "# " in l for l in lines):
            score += 10

    # Penalize bare except
    if "except:" in code:
        score -= 10

    # Penalize unused pass (likely leftover)
    non_class_pass = sum(
        1
        for i, l in enumerate(lines)
        if l.strip() == "pass"
        and i > 0
        and "class " not in lines[i - 1]
        and "__init__" not in lines[i - 1]
    )
    score -= non_class_pass * 5

    return max(0, min(100, score))


def score_time(elapsed, difficulty):
    """Time score 0-100. Faster = better, scaled by difficulty."""
    targets = {"easy": 120, "medium": 300, "hard": 600}
    target = targets.get(difficulty, 300)
    if elapsed <= target * 0.5:
        return 100
    if elapsed <= target:
        return 80
    if elapsed <= target * 2:
        return 50
    return 20


def run_tests(code, test_code):
    """Execute user code + tests in a restricted namespace. Returns (passed, total, error)."""
    namespace = {}
    try:
        exec(code, namespace)  # noqa: S102
    except Exception as e:
        return 0, 1, f"Code error: {e}"

    test_lines = [t for t in test_code.strip().splitlines() if t.strip()]
    # Group assertions as individual tests
    passed = 0
    total = 0
    first_error = None
    # Execute line-by-line for granular results
    block = []
    for line in test_code.strip().splitlines():
        block.append(line)
        # Execute when we hit an assert or end of meaningful statement
        if line.strip().startswith("assert ") or (
            block and not line.startswith(" ") and len(block) > 1
        ):
            total += 1
            try:
                exec("\n".join(block), namespace)  # noqa: S102
                passed += 1
            except Exception as e:
                if first_error is None:
                    first_error = str(e)
            block = []

    # Handle remaining block
    if block:
        total += 1
        try:
            exec("\n".join(block), namespace)  # noqa: S102
            passed += 1
        except Exception as e:
            if first_error is None:
                first_error = str(e)

    if total == 0:
        total = 1

    return passed, total, first_error


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

BASE_CSS = """\
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'SF Mono',SFMono-Regular,Consolas,'Liberation Mono',Menlo,monospace;
     background:#0d1117;color:#c9d1d9;min-height:100vh}
a{color:#58a6ff;text-decoration:none}
a:hover{text-decoration:underline}
.container{max-width:960px;margin:0 auto;padding:20px}
h1{color:#58a6ff;margin-bottom:4px;font-size:1.4em}
h2{color:#58a6ff;margin-bottom:8px;font-size:1.2em}
.subtitle{color:#8b949e;margin-bottom:20px;font-size:0.9em}
.card{border:1px solid #30363d;border-radius:8px;padding:16px;margin:10px 0;background:#161b22}
.card h3{color:#f0f6fc;margin-bottom:8px}
.btn{display:inline-block;padding:8px 16px;border:1px solid #30363d;background:#21262d;
     color:#c9d1d9;border-radius:6px;cursor:pointer;font-family:inherit;font-size:0.9em}
.btn:hover{background:#30363d;text-decoration:none}
.btn-primary{background:#238636;border-color:#2ea043;color:#fff}
.btn-primary:hover{background:#2ea043}
.btn-danger{background:#da3633;border-color:#f85149;color:#fff}
.btn-danger:hover{background:#f85149}
.badge{display:inline-block;padding:2px 8px;border-radius:12px;font-size:0.75em;font-weight:600}
.badge-easy{background:#238636;color:#fff}
.badge-medium{background:#d29922;color:#fff}
.badge-hard{background:#da3633;color:#fff}
.timer{font-size:1.8em;color:#f0f6fc;font-weight:700;font-variant-numeric:tabular-nums}
.hint-box{border:1px solid #d29922;background:#1c1608;border-radius:8px;padding:12px;margin:8px 0;color:#d29922}
textarea.code-editor{width:100%;min-height:300px;background:#0d1117;color:#c9d1d9;
     border:1px solid #30363d;border-radius:6px;padding:12px;font-family:inherit;
     font-size:0.9em;line-height:1.5;resize:vertical;tab-size:4}
textarea.code-editor:focus{outline:none;border-color:#58a6ff}
.score-bar{display:flex;gap:16px;flex-wrap:wrap;margin:12px 0}
.score-item{text-align:center}
.score-item .label{font-size:0.75em;color:#8b949e;text-transform:uppercase}
.score-item .value{font-size:1.6em;font-weight:700;color:#58a6ff}
.role-tag{display:inline-block;padding:4px 10px;border-radius:4px;font-size:0.8em;
          font-weight:600;text-transform:uppercase;margin-bottom:8px}
.role-driver{background:#1f6feb33;color:#58a6ff;border:1px solid #1f6feb}
.role-navigator{background:#23863633;color:#3fb950;border:1px solid #238636}
nav{border-bottom:1px solid #30363d;padding:12px 20px;margin-bottom:0;display:flex;
    align-items:center;gap:16px}
nav .brand{color:#f0f6fc;font-weight:700;font-size:1.1em}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px}
.test-pass{color:#3fb950}.test-fail{color:#f85149}
.flex{display:flex;gap:12px;align-items:center}
"""

NAV = """\
<nav>
  <span class="brand">Pair Programming Sim</span>
  <a href="/">Tasks</a>
  <a href="/history">History</a>
</nav>
"""

# ---- Home / Task List ----
HOME_TEMPLATE = (
    "<!DOCTYPE html><html><head><meta charset='utf-8'>"
    "<meta name='viewport' content='width=device-width,initial-scale=1'>"
    "<title>Pair Programming Simulator</title>"
    "<style>"
    + BASE_CSS
    + "</style></head><body>"
    + NAV
    + """\
<div class="container">
<h1>Pair Programming Simulator</h1>
<p class="subtitle">Choose a task and role to start a pair programming session.</p>
<div class="grid">
{% for task in tasks %}
<div class="card">
  <h3>{{ task.title }}</h3>
  <span class="badge badge-{{ task.difficulty }}">{{ task.difficulty }}</span>
  <p style="color:#8b949e;margin:8px 0;font-size:0.85em">{{ task.description[:100] }}{% if task.description|length > 100 %}…{% endif %}</p>
  <div style="margin-top:12px;display:flex;gap:8px">
    <form method="POST" action="/session/start">
      <input type="hidden" name="task_id" value="{{ task.id }}">
      <input type="hidden" name="role" value="driver">
      <button class="btn btn-primary" type="submit">Drive</button>
    </form>
    <form method="POST" action="/session/start">
      <input type="hidden" name="task_id" value="{{ task.id }}">
      <input type="hidden" name="role" value="navigator">
      <button class="btn" type="submit">Navigate</button>
    </form>
  </div>
</div>
{% endfor %}
</div>
</div></body></html>
"""
)

# ---- Session workspace ----
SESSION_TEMPLATE = (
    "<!DOCTYPE html><html><head><meta charset='utf-8'>"
    "<meta name='viewport' content='width=device-width,initial-scale=1'>"
    "<title>Session — {{ task.title }}</title>"
    "<style>"
    + BASE_CSS
    + """\
.workspace{display:grid;grid-template-columns:1fr 320px;gap:16px;margin-top:12px}
@media(max-width:768px){.workspace{grid-template-columns:1fr}}
</style></head><body>
"""
    + NAV
    + """\
<div class="container">
<div class="flex" style="justify-content:space-between;flex-wrap:wrap">
  <div>
    <span class="role-tag role-{{ session.role }}">{{ session.role }}</span>
    <h2>{{ task.title }}</h2>
  </div>
  <div class="timer" id="timer">00:00</div>
</div>
<p style="color:#8b949e;margin:8px 0;font-size:0.9em">{{ task.description }}</p>

<div class="workspace">
  <div>
    <form method="POST" action="/session/{{ session.id }}/submit" id="submit-form">
      <textarea class="code-editor" name="code" id="code-editor"
        spellcheck="false" autocomplete="off"
        placeholder="Write your code here...">{{ code }}</textarea>
      <div style="margin-top:8px;display:flex;gap:8px">
        <button type="submit" class="btn btn-primary">Submit &amp; Test</button>
        <button type="button" class="btn" id="hint-btn" onclick="getHint()">
          Get Partner Hint ({{ hints_used }}/{{ task.hints|length }})
        </button>
      </div>
    </form>
  </div>
  <div>
    <div class="card" id="hints-panel">
      <h3 style="font-size:0.9em;margin-bottom:8px">Partner Hints</h3>
      <div id="hints-container">
        {% if hints_used == 0 %}
        <p style="color:#8b949e;font-size:0.85em">Hints from your navigator partner will appear here after 2 minutes, or click the hint button.</p>
        {% endif %}
        {% for hint in shown_hints %}
        <div class="hint-box">{{ hint }}</div>
        {% endfor %}
      </div>
    </div>
    <div class="card" style="margin-top:8px">
      <h3 style="font-size:0.9em;margin-bottom:8px">Session Info</h3>
      <p style="font-size:0.85em;color:#8b949e">Task: {{ task.title }}<br>
      Difficulty: <span class="badge badge-{{ task.difficulty }}">{{ task.difficulty }}</span><br>
      Role: {{ session.role }}<br>
      Started: {{ session.started_at }}</p>
    </div>
  </div>
</div>
</div>

<script>
const startTime = new Date("{{ session.started_at }}Z").getTime();
const timerEl = document.getElementById('timer');
const HINT_DELAY = 120; // seconds
let autoHintShown = false;

function updateTimer() {
  const elapsed = Math.floor((Date.now() - startTime) / 1000);
  const m = String(Math.floor(elapsed / 60)).padStart(2, '0');
  const s = String(elapsed % 60).padStart(2, '0');
  timerEl.textContent = m + ':' + s;
  if (elapsed >= HINT_DELAY && !autoHintShown) {
    autoHintShown = true;
    getHint();
  }
}
setInterval(updateTimer, 1000);
updateTimer();

function getHint() {
  fetch('/session/{{ session.id }}/hint', {method: 'POST'})
    .then(r => r.json())
    .then(data => {
      if (data.hint) {
        const container = document.getElementById('hints-container');
        const div = document.createElement('div');
        div.className = 'hint-box';
        div.textContent = data.hint;
        container.appendChild(div);
        document.getElementById('hint-btn').textContent =
          'Get Partner Hint (' + data.hints_used + '/' + data.hints_total + ')';
      }
    });
}

// Tab key inserts spaces in the editor
document.getElementById('code-editor').addEventListener('keydown', function(e) {
  if (e.key === 'Tab') {
    e.preventDefault();
    const start = this.selectionStart;
    const end = this.selectionEnd;
    this.value = this.value.substring(0, start) + '    ' + this.value.substring(end);
    this.selectionStart = this.selectionEnd = start + 4;
  }
});
</script>
</body></html>
"""
)

# ---- Results page ----
RESULTS_TEMPLATE = (
    "<!DOCTYPE html><html><head><meta charset='utf-8'>"
    "<meta name='viewport' content='width=device-width,initial-scale=1'>"
    "<title>Results — {{ task.title }}</title>"
    "<style>"
    + BASE_CSS
    + "</style></head><body>"
    + NAV
    + """\
<div class="container">
<h2>Results: {{ task.title }}</h2>
<span class="role-tag role-{{ session.role }}">{{ session.role }}</span>
<span class="badge badge-{{ task.difficulty }}">{{ task.difficulty }}</span>

<div class="score-bar">
  <div class="score-item"><div class="label">Correctness</div><div class="value">{{ session.score_correctness }}</div></div>
  <div class="score-item"><div class="label">Time</div><div class="value">{{ session.score_time }}</div></div>
  <div class="score-item"><div class="label">Quality</div><div class="value">{{ session.score_quality }}</div></div>
  <div class="score-item"><div class="label">Total</div>
    <div class="value" style="color:{% if session.total_score >= 80 %}#3fb950{% elif session.total_score >= 50 %}#d29922{% else %}#f85149{% endif %}">
      {{ session.total_score }}
    </div>
  </div>
</div>

<div class="card">
  <h3 style="font-size:0.9em;margin-bottom:8px">Test Results ({{ session.tests_passed }}/{{ session.tests_total }})</h3>
  {% if error %}
  <pre class="test-fail" style="white-space:pre-wrap;font-size:0.85em">{{ error }}</pre>
  {% elif session.tests_passed == session.tests_total %}
  <p class="test-pass" style="font-size:0.9em">All tests passed!</p>
  {% else %}
  <p class="test-fail" style="font-size:0.9em">Some tests failed.</p>
  {% endif %}
</div>

<div class="card">
  <h3 style="font-size:0.9em;margin-bottom:8px">Your Code</h3>
  <pre style="white-space:pre-wrap;font-size:0.85em;color:#c9d1d9">{{ session.code }}</pre>
</div>

<div class="card">
  <p style="font-size:0.85em;color:#8b949e">
    Time: {{ "%.1f"|format(session.elapsed_seconds) }}s &middot;
    Hints used: {{ session.hints_used }} &middot;
    Completed: {{ session.completed_at }}
  </p>
</div>

<div style="margin-top:16px;display:flex;gap:8px">
  <a href="/" class="btn btn-primary">New Session</a>
  <a href="/history" class="btn">View History</a>
</div>
</div></body></html>
"""
)

# ---- History page ----
HISTORY_TEMPLATE = (
    "<!DOCTYPE html><html><head><meta charset='utf-8'>"
    "<meta name='viewport' content='width=device-width,initial-scale=1'>"
    "<title>Session History</title>"
    "<style>"
    + BASE_CSS
    + """\
table{width:100%;border-collapse:collapse;font-size:0.85em}
th{text-align:left;color:#8b949e;padding:8px;border-bottom:1px solid #30363d}
td{padding:8px;border-bottom:1px solid #21262d}
tr:hover{background:#161b22}
</style></head><body>
"""
    + NAV
    + """\
<div class="container">
<h2>Session History</h2>
{% if sessions %}
<table>
<thead><tr><th>Task</th><th>Role</th><th>Score</th><th>Tests</th><th>Time</th><th>Hints</th><th>Date</th><th></th></tr></thead>
<tbody>
{% for s in sessions %}
<tr>
  <td>{{ tasks[s.task_id].title if s.task_id in tasks else s.task_id }}</td>
  <td><span class="role-tag role-{{ s.role }}">{{ s.role }}</span></td>
  <td style="color:{% if s.total_score >= 80 %}#3fb950{% elif s.total_score >= 50 %}#d29922{% else %}#f85149{% endif %}">
    {{ s.total_score }}
  </td>
  <td>{{ s.tests_passed }}/{{ s.tests_total }}</td>
  <td>{{ "%.0f"|format(s.elapsed_seconds) if s.elapsed_seconds else '-' }}s</td>
  <td>{{ s.hints_used }}</td>
  <td style="color:#8b949e">{{ s.completed_at or s.started_at }}</td>
  <td><a href="/session/{{ s.id }}/results" class="btn" style="padding:4px 8px;font-size:0.8em">View</a></td>
</tr>
{% endfor %}
</tbody>
</table>
{% else %}
<div class="card"><p style="color:#8b949e">No sessions yet. <a href="/">Start one!</a></p></div>
{% endif %}
</div></body></html>
"""
)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.route("/")
def index():
    return render_template_string(HOME_TEMPLATE, tasks=TASKS)


@app.route("/session/start", methods=["POST"])
def session_start():
    task_id = request.form.get("task_id")
    role = request.form.get("role", "driver")
    if task_id not in TASKS_BY_ID:
        return "Unknown task", 404
    if role not in ("driver", "navigator"):
        role = "driver"

    db = get_db()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    cur = db.execute(
        "INSERT INTO sessions (task_id, role, code, started_at) VALUES (?, ?, ?, ?)",
        (task_id, role, TASKS_BY_ID[task_id]["starter"], now),
    )
    db.commit()
    return redirect(url_for("session_workspace", session_id=cur.lastrowid))


@app.route("/session/<int:session_id>")
def session_workspace(session_id):
    db = get_db()
    session = db.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    if not session:
        return "Session not found", 404
    if session["completed_at"]:
        return redirect(url_for("session_results", session_id=session_id))

    task = TASKS_BY_ID.get(session["task_id"])
    if not task:
        return "Task not found", 404

    hints_used = session["hints_used"]
    shown_hints = task["hints"][:hints_used]

    return render_template_string(
        SESSION_TEMPLATE,
        session=session,
        task=task,
        code=session["code"],
        hints_used=hints_used,
        shown_hints=shown_hints,
    )


@app.route("/session/<int:session_id>/hint", methods=["POST"])
def session_hint(session_id):
    db = get_db()
    session = db.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    if not session:
        return jsonify({"error": "not found"}), 404

    task = TASKS_BY_ID.get(session["task_id"])
    hints_used = session["hints_used"]
    if hints_used < len(task["hints"]):
        hint = task["hints"][hints_used]
        db.execute(
            "UPDATE sessions SET hints_used = ? WHERE id = ?",
            (hints_used + 1, session_id),
        )
        db.commit()
        return jsonify(
            {"hint": hint, "hints_used": hints_used + 1, "hints_total": len(task["hints"])}
        )
    return jsonify({"hint": None, "hints_used": hints_used, "hints_total": len(task["hints"])})


@app.route("/session/<int:session_id>/submit", methods=["POST"])
def session_submit(session_id):
    db = get_db()
    session = db.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    if not session:
        return "Session not found", 404

    task = TASKS_BY_ID.get(session["task_id"])
    if not task:
        return "Task not found", 404

    code = request.form.get("code", "")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    started = datetime.strptime(session["started_at"], "%Y-%m-%d %H:%M:%S").replace(
        tzinfo=timezone.utc
    )
    elapsed = (
        datetime.now(timezone.utc) - started
    ).total_seconds()

    # Score
    passed, total, error = run_tests(code, task["test_code"])
    s_correctness = round((passed / total) * 100) if total else 0
    s_time = score_time(elapsed, task["difficulty"])
    s_quality = score_quality(code)
    total_score = round(s_correctness * 0.5 + s_time * 0.25 + s_quality * 0.25)

    db.execute(
        """\
        UPDATE sessions SET code=?, completed_at=?, elapsed_seconds=?,
        score_correctness=?, score_time=?, score_quality=?, total_score=?,
        tests_passed=?, tests_total=?
        WHERE id=?""",
        (
            code, now, elapsed,
            s_correctness, s_time, s_quality, total_score,
            passed, total,
            session_id,
        ),
    )
    db.commit()
    return redirect(url_for("session_results", session_id=session_id))


@app.route("/session/<int:session_id>/results")
def session_results(session_id):
    db = get_db()
    session = db.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    if not session:
        return "Session not found", 404
    task = TASKS_BY_ID.get(session["task_id"])
    if not task:
        return "Task not found", 404

    # Re-run tests for display
    _, _, error = run_tests(session["code"], task["test_code"]) if session["code"] else (0, 0, None)

    return render_template_string(
        RESULTS_TEMPLATE, session=session, task=task, error=error
    )


@app.route("/history")
def history():
    db = get_db()
    sessions = db.execute(
        "SELECT * FROM sessions ORDER BY id DESC LIMIT 100"
    ).fetchall()
    return render_template_string(HISTORY_TEMPLATE, sessions=sessions, tasks=TASKS_BY_ID)


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------


@app.route("/api/tasks")
def api_tasks():
    return jsonify(
        [
            {"id": t["id"], "title": t["title"], "difficulty": t["difficulty"], "description": t["description"]}
            for t in TASKS
        ]
    )


@app.route("/api/sessions")
def api_sessions():
    db = get_db()
    rows = db.execute("SELECT * FROM sessions ORDER BY id DESC LIMIT 100").fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/sessions/<int:session_id>")
def api_session(session_id):
    db = get_db()
    row = db.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    if not row:
        return jsonify({"error": "not found"}), 404
    return jsonify(dict(row))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
