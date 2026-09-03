from council.positions import compare, overall_state


def response(kind="part", factor="reason", text="A bounded part"):
    return {"positions": [{"position_id": "one", "kind": kind, "text": text, "decisive_factor": factor, "acceptance": "observable", "depends_on": []}]}


def test_different_reasons_are_convergent():
    rows = compare({"a": response(factor="alpha"), "b": response(factor="beta")})
    assert rows[0]["state"] == "CONVERGENT"


def test_same_reason_is_shared_rationale():
    rows = compare({"a": response(), "b": response()})
    assert rows[0]["state"] == "SHARED_RATIONALE"


def test_opposite_kinds_are_contested():
    rows = compare({"a": response("part"), "b": response("whole")})
    assert rows[0]["state"] == "CONTESTED"


def test_one_member_is_unique():
    assert compare({"a": response()})[0]["state"] == "UNIQUE_POSITION"


def test_empty_comparison_has_no_response():
    assert overall_state([]) == "NO_RESPONSE"


def test_contested_row_sets_overall_state():
    assert overall_state([{"state": "CONTESTED"}]) == "DISAGREEMENT_RECORDED"
