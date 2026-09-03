"""Run blind proposals, mutual review, comparison, and an append-only log."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from .lanes import LANES
from .positions import compare, overall_state

DEFAULT_MODELS = {"claude": "claude-top", "codex": "codex-top", "gemini": "gemini-top"}


def model_for(member: str) -> str:
    """The model name a seat is asked for: COUNCIL_<VENDOR>_MODEL, else the placeholder."""
    return os.environ.get(f"COUNCIL_{member.upper()}_MODEL") or DEFAULT_MODELS[member]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def slugify(text: str) -> str:
    slug = "".join(char.lower() if char.isalnum() else "-" for char in text[:60])
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")[:40] or "request"


def _write_prompt(path: Path, phase: str, request: str, peers: list[dict] | None) -> None:
    instructions = (
        "Propose independently judgeable parts, their acceptance tests and dependencies. "
        "Also name what must remain a single owner decision. Do not perform the request."
        if phase == "initial"
        else "Read the anonymous proposals, challenge them, and return your revised positions."
    )
    path.write_text(
        json.dumps(
            {"phase": phase, "request": request, "instructions": instructions, "anonymous_peers": peers or []},
            indent=2,
        ),
        encoding="utf-8",
    )


def _parse(text: str, member: str) -> dict:
    try:
        body = json.loads(text)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"{member} returned text that is not JSON") from error
    if not isinstance(body.get("positions"), list) or not body["positions"]:
        raise RuntimeError(f"{member} returned no positions")
    return body


def run(request: str, outdir: Path, round2: bool = True) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    initial: dict[str, dict] = {}
    failed: list[dict] = []
    for member, lane in LANES.items():
        prompt = outdir / f"prompt-initial-{member}.json"
        _write_prompt(prompt, "initial", request, None)
        try:
            text = lane(prompt, model_for(member))
            (outdir / f"response-initial-{member}.txt").write_text(text + "\n", encoding="utf-8")
            initial[member] = _parse(text, member)
        except Exception as error:  # one failed seat must remain visible
            failed.append({"member": member, "phase": "initial", "error": str(error)})

    revised = dict(initial)
    if round2 and initial:
        for member, lane in LANES.items():
            if member not in initial:
                continue
            peers = [
                {"positions": response["positions"], "note": response.get("note")}
                for name, response in initial.items()
                if name != member
            ]
            prompt = outdir / f"prompt-revision-{member}.json"
            _write_prompt(prompt, "revision", request, peers)
            try:
                text = lane(prompt, model_for(member))
                (outdir / f"response-revision-{member}.txt").write_text(text + "\n", encoding="utf-8")
                revised[member] = _parse(text, member)
            except Exception as error:
                failed.append({"member": member, "phase": "revision", "error": str(error)})

    rows = compare(revised)
    result = {
        "timestamp": utc_now(),
        "request": request,
        "round2_ran": bool(round2 and initial),
        "members_seated": list(LANES),
        "members_contributing": list(revised),
        "members_failed": failed,
        "council_state": overall_state(rows),
        "positions": rows,
    }
    (outdir / "cut.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def append_log(path: Path, result: dict, outdir: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {**result, "run_directory": str(outdir)}
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, sort_keys=True) + "\n")


def render(result: dict, outdir: Path) -> str:
    lines = ["", "=" * 68, f"COUNCIL CUT -- {result['council_state']}", "=" * 68]
    lines.append("answered by: " + ", ".join(result["members_contributing"]))
    lines.append(f"cross-review: {'completed' if result['round2_ran'] else 'skipped'}")
    for failure in result["members_failed"]:
        lines.append(f"missing: {failure['member']} during {failure['phase']}: {failure['error']}")
    for row in result["positions"]:
        lines.extend(
            [
                "",
                f"[{row['state']}] {row['text']}",
                "  kind: " + str(row["kind"]),
                "  members: " + ", ".join(row["members"]),
                "  reasons: " + "; ".join(row["decisive_factors"]),
            ]
        )
    lines.extend(["", f"Full record: {outdir / 'cut.json'}", "Nothing has been delegated."])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="council-route")
    parser.add_argument("request")
    parser.add_argument("--out")
    parser.add_argument("--log")
    parser.add_argument("--no-round2", action="store_true")
    args = parser.parse_args(argv)
    request = args.request.strip()
    if not request:
        parser.error("request must not be empty")
    base = Path(os.environ.get("COUNCIL_RUNS", ".council-runs"))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    outdir = Path(args.out) if args.out else base / f"{stamp}-{slugify(request)}"
    log = Path(args.log) if args.log else base / "index.jsonl"
    result = run(request, outdir, not args.no_round2)
    append_log(log, result, outdir)
    print(render(result, outdir))
    return 0 if result["members_contributing"] else 3


if __name__ == "__main__":
    sys.exit(main())
