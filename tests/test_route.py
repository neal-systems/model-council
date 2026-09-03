import json
import subprocess
import sys
from pathlib import Path

from council.route import append_log, model_for, run, slugify


def test_route_seats_all_three_members(tmp_path):
    result = run("Design an example", tmp_path / "run")
    assert result["members_contributing"] == ["claude", "codex", "gemini"]


def test_route_completes_cross_review(tmp_path):
    result = run("Design an example", tmp_path / "run")
    assert result["round2_ran"] is True
    assert all((tmp_path / "run" / f"response-revision-{member}.txt").exists() for member in result["members_contributing"])
    prompt = json.loads((tmp_path / "run" / "prompt-revision-claude.json").read_text())
    assert all("model" not in peer for peer in prompt["anonymous_peers"])


def test_route_writes_cut(tmp_path):
    run("Design an example", tmp_path / "run")
    body = json.loads((tmp_path / "run" / "cut.json").read_text())
    assert body["council_state"] == "CUT_RECORDED"
    assert len(body["positions"]) == 4


def test_route_can_skip_second_round(tmp_path):
    result = run("Design an example", tmp_path / "run", round2=False)
    assert result["round2_ran"] is False
    assert not list((tmp_path / "run").glob("response-revision-*.txt"))


def test_log_is_append_only(tmp_path):
    result = run("Design an example", tmp_path / "run")
    log = tmp_path / "index.jsonl"
    append_log(log, result, tmp_path / "run")
    append_log(log, result, tmp_path / "run")
    assert len(log.read_text().splitlines()) == 2


def test_slug_is_short_and_path_safe():
    value = slugify("A request with spaces and punctuation!" * 3)
    assert len(value) <= 40
    assert value.replace("-", "").isalnum()


def test_command_prints_a_cut(tmp_path):
    root = Path(__file__).resolve().parents[1]
    completed = subprocess.run(
        [sys.executable, str(root / "council-route"), "Design an example", "--out", str(tmp_path / "run"), "--log", str(tmp_path / "log.jsonl")],
        cwd=root, capture_output=True, text=True,
    )
    assert completed.returncode == 0
    assert "COUNCIL CUT" in completed.stdout
    assert "claude, codex, gemini" in completed.stdout


def test_model_name_comes_from_environment(monkeypatch):
    monkeypatch.delenv("COUNCIL_CODEX_MODEL", raising=False)
    assert model_for("codex") == "codex-top"
    monkeypatch.setenv("COUNCIL_CODEX_MODEL", "codex-example-2026")
    assert model_for("codex") == "codex-example-2026"


def test_seat_receives_configured_model_name(tmp_path, monkeypatch):
    monkeypatch.setenv("COUNCIL_GEMINI_MODEL", "gemini-example-2026")
    run("Design an example", tmp_path / "run")
    body = json.loads((tmp_path / "run" / "response-initial-gemini.txt").read_text())
    assert body["model"] == "gemini-example-2026"
