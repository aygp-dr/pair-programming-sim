"""Tests for pair programming simulator."""

import json
import os
import tempfile

import pytest

# Override DB_PATH before importing app
os.environ.setdefault("SECRET_KEY", "test-key")

from main import TASKS, TASKS_BY_ID, app, run_tests, score_quality, score_time


@pytest.fixture
def client(tmp_path):
    """Create a test client with a temporary database."""
    import main

    original_path = main.DB_PATH
    main.DB_PATH = str(tmp_path / "test.db")
    app.config["TESTING"] = True
    with app.test_client() as c:
        with app.app_context():
            main.get_db()
        yield c
    main.DB_PATH = original_path


# ---------------------------------------------------------------------------
# Task data integrity
# ---------------------------------------------------------------------------


class TestTasks:
    def test_all_tasks_have_required_fields(self):
        for task in TASKS:
            assert "id" in task
            assert "title" in task
            assert "difficulty" in task
            assert "description" in task
            assert "starter" in task
            assert "test_code" in task
            assert "hints" in task
            assert len(task["hints"]) >= 1

    def test_ten_tasks_defined(self):
        assert len(TASKS) == 10

    def test_task_ids_unique(self):
        ids = [t["id"] for t in TASKS]
        assert len(ids) == len(set(ids))

    def test_tasks_by_id_lookup(self):
        assert "implement-fizzbuzz" in TASKS_BY_ID
        assert "reverse-linked-list" in TASKS_BY_ID
        assert "parse-csv" in TASKS_BY_ID
        assert "lru-cache" in TASKS_BY_ID

    def test_difficulty_values(self):
        valid = {"easy", "medium", "hard"}
        for task in TASKS:
            assert task["difficulty"] in valid


# ---------------------------------------------------------------------------
# Scoring functions
# ---------------------------------------------------------------------------


class TestScoring:
    def test_score_quality_empty_code(self):
        assert score_quality("") == 0

    def test_score_quality_decent_code(self):
        code = 'def fizzbuzz(n):\n    """Return fizzbuzz list."""\n    return [str(i) for i in range(1, n+1)]\n'
        s = score_quality(code)
        assert 70 <= s <= 100

    def test_score_quality_penalizes_bare_except(self):
        code_good = "def f():\n    try:\n        pass\n    except ValueError:\n        pass\n"
        code_bad = "def f():\n    try:\n        pass\n    except:\n        pass\n"
        assert score_quality(code_good) > score_quality(code_bad)

    def test_score_time_fast(self):
        assert score_time(30, "easy") == 100

    def test_score_time_slow(self):
        assert score_time(1000, "easy") == 20

    def test_score_time_medium(self):
        s = score_time(100, "easy")
        assert 50 <= s <= 100


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------


class TestRunner:
    def test_passing_code(self):
        code = "def fizzbuzz(n):\n    r = []\n    for i in range(1, n+1):\n        if i % 15 == 0: r.append('FizzBuzz')\n        elif i % 3 == 0: r.append('Fizz')\n        elif i % 5 == 0: r.append('Buzz')\n        else: r.append(str(i))\n    return r\n"
        task = TASKS_BY_ID["implement-fizzbuzz"]
        passed, total, error = run_tests(code, task["test_code"])
        assert passed == total
        assert error is None

    def test_failing_code(self):
        code = "def fizzbuzz(n):\n    return [str(i) for i in range(1, n+1)]\n"
        task = TASKS_BY_ID["implement-fizzbuzz"]
        passed, total, error = run_tests(code, task["test_code"])
        assert passed < total

    def test_syntax_error(self):
        code = "def fizzbuzz(n)\n    return\n"
        task = TASKS_BY_ID["implement-fizzbuzz"]
        passed, total, error = run_tests(code, task["test_code"])
        assert passed == 0
        assert error is not None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


class TestRoutes:
    def test_homepage(self, client):
        rv = client.get("/")
        assert rv.status_code == 200
        assert b"Pair Programming Simulator" in rv.data
        assert b"implement-fizzbuzz" in rv.data

    def test_start_session_driver(self, client):
        rv = client.post(
            "/session/start",
            data={"task_id": "implement-fizzbuzz", "role": "driver"},
            follow_redirects=False,
        )
        assert rv.status_code == 302
        assert "/session/1" in rv.headers["Location"]

    def test_start_session_navigator(self, client):
        rv = client.post(
            "/session/start",
            data={"task_id": "two-sum", "role": "navigator"},
            follow_redirects=False,
        )
        assert rv.status_code == 302

    def test_start_session_invalid_task(self, client):
        rv = client.post(
            "/session/start",
            data={"task_id": "nonexistent", "role": "driver"},
        )
        assert rv.status_code == 404

    def test_session_workspace(self, client):
        client.post("/session/start", data={"task_id": "implement-fizzbuzz", "role": "driver"})
        rv = client.get("/session/1")
        assert rv.status_code == 200
        assert b"FizzBuzz" in rv.data
        assert b"driver" in rv.data

    def test_session_not_found(self, client):
        rv = client.get("/session/999")
        assert rv.status_code == 404

    def test_submit_session(self, client):
        client.post("/session/start", data={"task_id": "implement-fizzbuzz", "role": "driver"})
        code = (
            "def fizzbuzz(n):\n"
            "    r = []\n"
            "    for i in range(1, n+1):\n"
            "        if i % 15 == 0: r.append('FizzBuzz')\n"
            "        elif i % 3 == 0: r.append('Fizz')\n"
            "        elif i % 5 == 0: r.append('Buzz')\n"
            "        else: r.append(str(i))\n"
            "    return r\n"
        )
        rv = client.post("/session/1/submit", data={"code": code}, follow_redirects=False)
        assert rv.status_code == 302
        assert "/session/1/results" in rv.headers["Location"]

    def test_results_page(self, client):
        client.post("/session/start", data={"task_id": "implement-fizzbuzz", "role": "driver"})
        client.post("/session/1/submit", data={"code": "def fizzbuzz(n):\n    return []\n"})
        rv = client.get("/session/1/results")
        assert rv.status_code == 200
        assert b"Results" in rv.data

    def test_hint_endpoint(self, client):
        client.post("/session/start", data={"task_id": "implement-fizzbuzz", "role": "driver"})
        rv = client.post("/session/1/hint")
        data = json.loads(rv.data)
        assert data["hint"] is not None
        assert data["hints_used"] == 1

    def test_hint_exhaustion(self, client):
        client.post("/session/start", data={"task_id": "implement-fizzbuzz", "role": "driver"})
        task = TASKS_BY_ID["implement-fizzbuzz"]
        for _ in range(len(task["hints"])):
            client.post("/session/1/hint")
        rv = client.post("/session/1/hint")
        data = json.loads(rv.data)
        assert data["hint"] is None

    def test_history_empty(self, client):
        rv = client.get("/history")
        assert rv.status_code == 200
        assert b"No sessions yet" in rv.data

    def test_history_with_sessions(self, client):
        client.post("/session/start", data={"task_id": "two-sum", "role": "driver"})
        client.post("/session/1/submit", data={"code": "def two_sum(nums, target):\n    return [0, 1]\n"})
        rv = client.get("/history")
        assert rv.status_code == 200
        assert b"Two Sum" in rv.data

    def test_completed_session_redirects(self, client):
        client.post("/session/start", data={"task_id": "implement-fizzbuzz", "role": "driver"})
        client.post("/session/1/submit", data={"code": "def fizzbuzz(n):\n    return []\n"})
        rv = client.get("/session/1", follow_redirects=False)
        assert rv.status_code == 302


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------


class TestAPI:
    def test_api_tasks(self, client):
        rv = client.get("/api/tasks")
        data = json.loads(rv.data)
        assert len(data) == 10
        assert data[0]["id"] == "implement-fizzbuzz"

    def test_api_sessions_empty(self, client):
        rv = client.get("/api/sessions")
        data = json.loads(rv.data)
        assert data == []

    def test_api_sessions_after_start(self, client):
        client.post("/session/start", data={"task_id": "binary-search", "role": "navigator"})
        rv = client.get("/api/sessions")
        data = json.loads(rv.data)
        assert len(data) == 1
        assert data[0]["task_id"] == "binary-search"
        assert data[0]["role"] == "navigator"

    def test_api_session_detail(self, client):
        client.post("/session/start", data={"task_id": "implement-fizzbuzz", "role": "driver"})
        rv = client.get("/api/sessions/1")
        data = json.loads(rv.data)
        assert data["task_id"] == "implement-fizzbuzz"

    def test_api_session_not_found(self, client):
        rv = client.get("/api/sessions/999")
        assert rv.status_code == 404
