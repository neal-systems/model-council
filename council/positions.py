"""Compare council positions without voting or hiding minority views."""

from __future__ import annotations

from collections import defaultdict


STATE_ORDER = ["CONVERGENT", "SHARED_RATIONALE", "CONTESTED", "UNIQUE_POSITION"]


def compare(responses: dict[str, dict]) -> list[dict]:
    grouped: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    for member, response in responses.items():
        for position in response.get("positions", []):
            grouped[str(position.get("position_id", "unnamed"))].append((member, position))

    rows = []
    for position_id, entries in grouped.items():
        kinds = {entry.get("kind") for _, entry in entries}
        factors = [str(entry.get("decisive_factor", "")).strip() for _, entry in entries]
        distinct_factors = {factor.casefold() for factor in factors if factor}
        if len(entries) == 1:
            state = "UNIQUE_POSITION"
        elif len(kinds) > 1:
            state = "CONTESTED"
        elif len(distinct_factors) > 1:
            state = "CONVERGENT"
        else:
            state = "SHARED_RATIONALE"
        exemplar = entries[0][1]
        rows.append(
            {
                "position_id": position_id,
                "kind": exemplar.get("kind"),
                "text": exemplar.get("text"),
                "acceptance": exemplar.get("acceptance"),
                "depends_on": exemplar.get("depends_on", []),
                "state": state,
                "members": [member for member, _ in entries],
                "decisive_factors": factors,
                "variants": [entry.get("text") for _, entry in entries],
            }
        )
    rank = {state: index for index, state in enumerate(STATE_ORDER)}
    return sorted(rows, key=lambda row: (rank.get(row["state"], 99), row["position_id"]))


def overall_state(rows: list[dict]) -> str:
    if not rows:
        return "NO_RESPONSE"
    if any(row["state"] == "CONTESTED" for row in rows):
        return "DISAGREEMENT_RECORDED"
    if any(row["state"] == "UNIQUE_POSITION" for row in rows):
        return "MINORITY_VIEW_RECORDED"
    return "CUT_RECORDED"
