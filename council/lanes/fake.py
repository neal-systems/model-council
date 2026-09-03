"""Deterministic responses that exercise both council rounds without a network."""

from __future__ import annotations

import json
from pathlib import Path


FACTORS = {
    "claude": {
        "architecture": "interfaces should be settled before files change",
        "implementation": "one bounded change can be reviewed on its own",
        "verification": "the checker must be independent of the builder",
        "authority": "scope and risk belong to the request owner",
    },
    "codex": {
        "architecture": "dependencies determine a safe build order",
        "implementation": "a separate work area makes the patch attributable",
        "verification": "repeatable commands make the result observable",
        "authority": "separate changes can combine into an unauthorized whole",
    },
    "gemini": {
        "architecture": "acceptance criteria must exist before execution",
        "implementation": "isolating writes prevents cross-part interference",
        "verification": "fresh evidence is stronger than an executor claim",
        "authority": "the objective and completion threshold cannot be delegated",
    },
}


def _positions(vendor: str, phase: str) -> list[dict]:
    f = FACTORS[vendor]
    suffix = " after considering the other seats" if phase == "revision" else ""
    return [
        {
            "position_id": "architecture",
            "kind": "part",
            "text": "Define the architecture, boundaries, and acceptance criteria.",
            "decisive_factor": f["architecture"] + suffix,
            "acceptance": "A reader can identify inputs, outputs, boundaries, and tests.",
            "depends_on": [],
        },
        {
            "position_id": "implementation",
            "kind": "part",
            "text": "Implement the approved design in an isolated worktree.",
            "decisive_factor": f["implementation"] + suffix,
            "acceptance": "The expected files change and prohibited files do not.",
            "depends_on": ["architecture"],
        },
        {
            "position_id": "verification",
            "kind": "part",
            "text": "Verify the candidate against the written acceptance criteria.",
            "decisive_factor": f["verification"] + suffix,
            "acceptance": "Every prescribed check has captured output and a status.",
            "depends_on": ["implementation"],
        },
        {
            "position_id": "authority",
            "kind": "whole",
            "text": "Keep the objective, authorization boundary, and final approval together.",
            "decisive_factor": f["authority"] + suffix,
            "acceptance": "The request owner retains every scope and release decision.",
            "depends_on": [],
        },
    ]


def run(prompt_file: Path, model: str, vendor: str) -> str:
    prompt = json.loads(Path(prompt_file).read_text(encoding="utf-8"))
    phase = prompt.get("phase", "initial")
    return json.dumps(
        {
            "model": model,
            "phase": phase,
            "positions": _positions(vendor, phase),
            "note": "I kept my reasoning independent." if phase == "initial"
            else "I retained the cut and made the verification boundary explicit.",
        },
        sort_keys=True,
    )
