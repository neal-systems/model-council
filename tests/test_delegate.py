import json

import pytest

from council.delegate import dependency_waves, main, make_plan


def part(part_id, dependencies=None):
    return {"part_id": part_id, "depends_on": dependencies or []}


def sample_cut():
    return {
        "positions": [
            {"position_id": "design", "kind": "part", "state": "CONVERGENT", "text": "Design it", "acceptance": "Design is clear", "depends_on": []},
            {"position_id": "build", "kind": "part", "state": "CONVERGENT", "text": "Build it", "acceptance": "Checks pass", "depends_on": ["design"]},
            {"position_id": "approval", "kind": "whole", "state": "CONVERGENT", "text": "Owner approves", "acceptance": "Approval recorded", "depends_on": []},
        ]
    }


def test_dependency_waves_follow_order():
    waves = dependency_waves([part("a"), part("b", ["a"]), part("c", ["a"])])
    assert [[item["part_id"] for item in wave] for wave in waves] == [["a"], ["b", "c"]]


def test_missing_dependency_is_error():
    with pytest.raises(ValueError, match="missing parts"):
        dependency_waves([part("a", ["missing"])])


def test_cycle_is_error():
    with pytest.raises(ValueError, match="dependency cycle"):
        dependency_waves([part("a", ["b"]), part("b", ["a"])])


def test_plan_keeps_owner_decision_whole():
    plan = make_plan(sample_cut())
    assert plan["kept_whole"] == ["Owner approves"]
    assert plan["operator_decisions"] == ["Owner approves"]


def test_plan_has_ordered_parts():
    assert make_plan(sample_cut())["waves"] == [["design"], ["build"]]


def test_delegate_command_writes_plan(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "cut.json").write_text(json.dumps(sample_cut()))
    assert main([str(run_dir)]) == 0
    assert (run_dir / "plan.json").exists()
