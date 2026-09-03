import json
import sys

import pytest

from council.lanes.adapter import run


def prompt(tmp_path, phase="initial"):
    path = tmp_path / "prompt.json"
    path.write_text(json.dumps({"phase": phase, "request": "example"}))
    return path


def test_default_lane_is_offline_fake(tmp_path, monkeypatch):
    monkeypatch.delenv("COUNCIL_CLAUDE_COMMAND", raising=False)
    body = json.loads(run("claude", prompt(tmp_path), "example-model"))
    assert body["model"] == "example-model"
    assert len(body["positions"]) == 4


def test_external_adapter_receives_file_and_model(tmp_path, monkeypatch):
    helper = tmp_path / "helper.py"
    helper.write_text(
        "import json,sys\n"
        "print(json.dumps({'argv': sys.argv[1:], 'positions': [{'position_id':'x'}]}))\n"
    )
    monkeypatch.setenv("COUNCIL_CODEX_COMMAND", f"{sys.executable} {helper}")
    body = json.loads(run("codex", prompt(tmp_path), "model-x"))
    assert "--prompt-file" in body["argv"]
    assert body["argv"][-2:] == ["--model", "model-x"]


def test_external_adapter_reports_failure(tmp_path, monkeypatch):
    monkeypatch.setenv("COUNCIL_GEMINI_COMMAND", f"{sys.executable} -c raise\\ SystemExit(2)")
    with pytest.raises(RuntimeError, match="gemini lane failed"):
        run("gemini", prompt(tmp_path), "model-y")
